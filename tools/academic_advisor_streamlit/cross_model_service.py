"""Explicit, bounded B/C rescoring of two saved benchmark top-one plans.

Reading saved experiments never builds a model context. Only ``start`` schedules
work, and outcomes/observed registrations are never accepted by the scorer.
"""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
from threading import RLock
from time import perf_counter
from uuid import uuid4

from tools.recommendation_pilot_20251.adapter import PILOT_ROOT, TARGET_PART, sha256
from tools.recommendation_pilot_20251.engine import _digest
from tools.recommendation_pilot_20251.search_benchmark import (
    BUDGETS, STRATEGIES, ResourceLimits, SearchBenchmarkService,
    atomic_json, canonical_plan_id, code_fingerprints, memory_mb, score_chunk,
)
from tools.recommendation_pilot_20251.snapshots import AFTER


ASSET_FIELDS = ('status', 'model_version', 'feature_count', 'artifact_sha256',
                'manifest_sha256', 'history_artifact_sha256', 'reference_sha256',
                'grade_scale_sha256', 'training_as_of_part', 'history_as_of_part')
COURSE_FIELDS = ('course_id', 'course_name', 'course_credits', 'predicted_mark',
                 'expected_points', 'expected_grade', 'fail_probability',
                 'course_history_fallback_level', 'course_history_effective_support',
                 'peer_expected_points', 'similar_peer_support', 'course_difficulty_gap')
FORBIDDEN_INPUTS = {'actual_mark', 'actual_points', 'final_mark', 'points',
                    'course_outcome_status', 'finish_status', 'grade_id'}


class CrossModelBlocked(ValueError):
    """A requested saved source cannot be safely rescored in current context."""


def _assets(assets):
    return {model: {key: value for key, value in (assets.get(model) or {}).items()
                    if key in ASSET_FIELDS} for model in 'BC'}


def _number(value):
    if isinstance(value, bool):
        return None
    try:
        value = float(value)
        return value if math.isfinite(value) else None
    except (TypeError, ValueError, OverflowError):
        return None


class CrossModelService:
    """One explicit job at a time; each scores at most two unique plans on B/C."""

    def __init__(self, validation=None, search=None, root=PILOT_ROOT):
        self.root = Path(root).resolve()
        self.output = self.root / 'experiments' / AFTER / 'university_validation' / 'cross_model'
        self.validation = validation
        self.search = search
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='university-cross-model')
        self.jobs, self.futures, self.lock = {}, {}, RLock()

    def _directory(self, run_id):
        if not isinstance(run_id, str) or not re.fullmatch(r'cross_[A-Za-z0-9_]+', run_id):
            raise ValueError('Invalid cross-model run identifier.')
        directory = self.output / run_id
        if (not self.output.resolve().is_relative_to(self.root) or directory.is_symlink() or
                directory.resolve().parent != self.output.resolve()):
            raise ValueError('Cross-model path escapes storage.')
        return directory

    def start(self, sample_id, *, snapshot_id, source_ref, strategy='SMART_SEARCH',
              budget=1000, scope='FULL_SPACE', target_credits=None):
        """Capture one saved selection, then schedule its bounded complete-plan scores."""
        if snapshot_id != AFTER:
            raise ValueError('Cross-model evaluation requires after_backend_fix.')
        if (not isinstance(sample_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]+', sample_id) or
                not isinstance(source_ref, dict) or source_ref.get('kind') != 'benchmark' or
                not re.fullmatch(r'benchmark_[A-Za-z0-9_]+', str(source_ref.get('run_id', '')))):
            raise ValueError('An explicit saved benchmark sample/source is required.')
        if (strategy not in STRATEGIES or isinstance(budget, bool) or budget not in BUDGETS or
                scope not in ('FIXED_POOL', 'FULL_SPACE')):
            raise ValueError('Invalid bounded cross-model source configuration.')
        if target_credits is not None and (_number(target_credits) is None or _number(target_credits) <= 0):
            raise ValueError('Invalid exact-credit target.')
        with self.lock:
            if any(job['status'] == 'running' for job in self.jobs.values()):
                raise ValueError('A cross-model evaluation is already running.')
            if self.validation is None:
                from .validation_service import ValidationService
                self.validation = ValidationService(root=self.root)
            source_ref = {'kind': 'benchmark', 'run_id': source_ref['run_id']}
            source = deepcopy(self.validation.recommendations(sample_id, snapshot_id=snapshot_id,
                source_ref=source_ref, strategy=strategy, budget=budget, scope=scope,
                target_credits=target_credits, allow_historical=False))
            run_id = 'cross_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S') + '_' + uuid4().hex[:10]
            request = dict(sample_id=sample_id, snapshot_id=snapshot_id, source_ref=source_ref,
                           strategy=strategy, budget=budget, scope=scope, target_credits=target_credits)
            self.jobs[run_id] = {'run_id': run_id, 'status': 'running', 'completed': 0, 'total': 4}
            self.futures[run_id] = self.executor.submit(self._execute, run_id, request, source)
            return run_id

    def _guard(self, started, limits):
        if perf_counter() - started >= limits.max_seconds:
            raise CrossModelBlocked('CROSS_MODEL_RUNTIME_LIMIT')
        used = memory_mb()
        if used is not None and used > limits.max_memory_mb:
            raise CrossModelBlocked('CROSS_MODEL_MEMORY_LIMIT')

    @staticmethod
    def _source_proof(request, source):
        if source.get('status') != 'AVAILABLE':
            raise CrossModelBlocked(source.get('reason') or 'SAVED_RECOMMENDATIONS_UNAVAILABLE')
        proof = source.get('provenance') or {}
        if (proof.get('snapshot_id') != request['snapshot_id'] or
                proof.get('part_id') != TARGET_PART or proof.get('sample_id') != request['sample_id']):
            raise CrossModelBlocked('CROSS_MODEL_SOURCE_IDENTITY_MISMATCH')
        if (proof.get('actual_course_injection') is not False or proof.get('legacy') or
                proof.get('candidate_mode', 'original') != 'original'):
            raise CrossModelBlocked('CROSS_MODEL_LEGACY_OR_INJECTED_SOURCE')
        if any(proof.get(key) != request[key] for key in ('strategy', 'budget', 'scope')):
            raise CrossModelBlocked('CROSS_MODEL_SOURCE_CONFIGURATION_MISMATCH')
        for model in 'BC':
            if not ((source.get('models') or {}).get(model) or {}).get('top_plans'):
                raise CrossModelBlocked('CROSS_MODEL_BOTH_SOURCE_TOP1_REQUIRED')
        return proof

    @staticmethod
    def _match_context(request, proof, context):
        if FORBIDDEN_INPUTS & set(context.base.columns):
            raise CrossModelBlocked('CROSS_MODEL_OUTCOME_INPUT_FORBIDDEN')
        if proof.get('input_fingerprints') != context.inputs or not context.inputs:
            raise CrossModelBlocked('CROSS_MODEL_INPUT_FINGERPRINT_MISMATCH')
        if proof.get('candidate_sha256') != _digest(context.base.to_dict('records')):
            raise CrossModelBlocked('CROSS_MODEL_CANDIDATE_FINGERPRINT_MISMATCH')
        target = _number(proof.get('target_credits'))
        current = context.target_resolution
        if (target is None or current.get('status') != 'RESOLVED' or
                current.get('target_credits_source') != 'API' or
                target != _number(current.get('target_credits')) or
                (request['target_credits'] is not None and target != _number(request['target_credits']))):
            raise CrossModelBlocked('CROSS_MODEL_TARGET_MISMATCH')
        old_assets = proof.get('model_assets') or {}
        for model in 'BC':
            old, live = old_assets.get(model) or {}, context.assets.get(model) or {}
            required = ('model_version', 'artifact_sha256', 'manifest_sha256', 'grade_scale_sha256', 'history_as_of_part')
            if (old.get('status') != 'READY' or live.get('status') != 'READY' or
                    any(old.get(key) is None or live.get(key) is None for key in required) or
                    _assets({model: old})[model] != _assets({model: live})[model]):
                raise CrossModelBlocked('CROSS_MODEL_MODEL_ASSET_MISMATCH')
        return target

    @staticmethod
    def _select_plans(source, context, target):
        base = context.base
        ids = list(map(str, base.course_id))
        if len(ids) != len(set(ids)):
            raise CrossModelBlocked('CROSS_MODEL_AMBIGUOUS_CANDIDATES')
        index = {key: position for position, key in enumerate(ids)}
        selected, sources = {}, {}
        for model in 'BC':
            plan = source['models'][model]['top_plans'][0]
            courses = plan.get('courses') or []
            course_ids = [str(course.get('course_id', '')) for course in courses]
            if (not course_ids or len(course_ids) != len(set(course_ids)) or
                    any(key not in index for key in course_ids)):
                raise CrossModelBlocked('CROSS_MODEL_SOURCE_COURSE_SET_INVALID')
            canonical = canonical_plan_id(course_ids)
            if canonical != plan.get('canonical_id'):
                raise CrossModelBlocked('CROSS_MODEL_CANONICAL_ID_MISMATCH')
            for course, key in zip(courses, course_ids):
                if _number(course.get('course_credits')) != _number(base.iloc[index[key]].course_credits):
                    raise CrossModelBlocked('CROSS_MODEL_SOURCE_CREDITS_MISMATCH')
            indices = tuple(sorted(index[key] for key in course_ids))
            try:
                rank = context.space.rank(indices)
            except ValueError:
                raise CrossModelBlocked('CROSS_MODEL_SOURCE_PLAN_NOT_FEASIBLE') from None
            if _number(plan.get('total_credits')) != target:
                raise CrossModelBlocked('CROSS_MODEL_SOURCE_TOTAL_CREDITS_MISMATCH')
            selected.setdefault(canonical, (indices, rank))
            sources[model] = canonical
        return selected, sources

    def _execute(self, run_id, request, source):
        started, rows = perf_counter(), []
        limits = ResourceLimits(max_seconds=300., chunk_size=2, max_oracle_plans=2,
                                max_disk_mb=8., max_memory_mb=2048.)
        manifest = {'format_version': 1, 'run_id': run_id, 'created_at': datetime.now(timezone.utc).isoformat(),
            **request, 'status': 'running', 'target_outcomes_used': False,
            'actual_course_injection': False, 'complete_plan_model_evaluations': 0,
            'unique_source_plan_count': 0, 'maximum_complete_plan_model_evaluations': 4,
            'official_registration_validated': False, 'purpose': 'optional_saved_top1_cross_model_comparison',
            'resource_limits': asdict(limits),
            'code_sha256': {**code_fingerprints(), 'tools/academic_advisor_streamlit/cross_model_service.py': sha256(Path(__file__))},
            'elapsed_seconds_scope': 'worker context preparation, validation and scoring; excludes source loading and persistence',
            'timings': {}}
        reason = None
        try:
            proof = self._source_proof(request, source)
            if self.search is None:
                self.search = SearchBenchmarkService(root=self.root)
            students = [s for s in self.search.cohort() if s.get('sample_id') == request['sample_id']]
            if len(students) != 1 or students[0].get('part_id') != TARGET_PART:
                raise CrossModelBlocked('CROSS_MODEL_CURRENT_SAMPLE_UNAVAILABLE')
            self._guard(started, limits)
            context = self.search._context(students[0], limits)
            self._guard(started, limits)
            target = self._match_context(request, proof, context)
            selected, sources = self._select_plans(source, context, target)
            manifest.update(target_credits=target, part_id=TARGET_PART,
                target_credits_source='API', input_fingerprints=deepcopy(context.inputs),
                model_assets=_assets(context.assets), candidate_sha256=proof['candidate_sha256'],
                source_fingerprint=proof.get('fingerprint'), source_canonical_ids=sources,
                unique_source_plan_count=len(selected), source_selection_provenance={
                    key: deepcopy(proof[key]) for key in ('snapshot_id', 'part_id', 'sample_id',
                    'strategy', 'budget', 'scope', 'target_credits', 'candidate_sha256') if key in proof})
            manifest['source_selection'] = {model: {key: deepcopy(value) for key, value in source['models'][model].items()
                if key in {'status', 'prediction_status', 'scope', 'strategy', 'budget', 'target_credits',
                           'target_credits_source', 'evaluated_plans', 'search_truncated', 'score_fingerprint'}}
                for model in 'BC'}
            plan_indices = [value[0] for value in selected.values()]
            ranks = [value[1] for value in selected.values()]
            for model in 'BC':
                self._guard(started, limits)
                # The same complete plans/ranks are passed unchanged to both models.
                scored, timing = score_chunk(context.base, plan_indices, ranks, context.scorer, model)
                manifest['complete_plan_model_evaluations'] += len(plan_indices)
                manifest['timings'][model] = timing
                indexed = {plan['canonical_id']: plan for plan in scored}
                if set(indexed) != set(selected) or len(scored) != len(selected):
                    raise CrossModelBlocked('CROSS_MODEL_SCORE_ALIGNMENT_MISMATCH')
                for source_model, canonical in sources.items():
                    plan = indexed[canonical]
                    rows.append({'source_model': source_model, 'scoring_model': model, 'canonical_id': canonical,
                        'expected_plan_gpa': plan['expected_plan_gpa'], 'expected_failed_credits': plan['expected_failed_credits'],
                        'max_fail_probability': plan['plan_difficulty_balance']['max_fail_probability'],
                        'total_credits': plan['total_credits'], 'courses': [
                            {key: deepcopy(value) for key, value in course.items() if key in COURSE_FIELDS}
                            for course in plan['courses']]})
                with self.lock:
                    self.jobs[run_id]['completed'] = manifest['complete_plan_model_evaluations']
            self._guard(started, limits)
            manifest['status'] = 'completed'
        except Exception as error:
            reason = str(error) if isinstance(error, CrossModelBlocked) else 'CROSS_MODEL_' + type(error).__name__.upper()
            manifest.update(status='BLOCKED', reason=reason)
            rows = []
        manifest['total_wall_seconds'] = perf_counter() - started
        directory = self._directory(run_id)
        try:
            if len(json.dumps(rows, ensure_ascii=False).encode('utf-8')) > limits.max_disk_mb * 1024 ** 2:
                rows = []
                reason = 'CROSS_MODEL_DISK_LIMIT'
                manifest.update(status='BLOCKED', reason=reason)
            directory.mkdir(parents=True, exist_ok=False)
            atomic_json(directory / 'run_manifest.json', manifest)
            atomic_json(directory / 'rows.json', rows)
            atomic_json(directory / 'integrity.json', {'sha256': {
                name: sha256(directory / name) for name in ('run_manifest.json', 'rows.json')}})
        except Exception:
            with self.lock:
                self.jobs[run_id].update(status='failed', reason='CROSS_MODEL_PERSISTENCE_UNAVAILABLE')
            raise
        with self.lock:
            self.jobs[run_id].update(status=manifest['status'], reason=reason,
                completed=manifest['complete_plan_model_evaluations'],
                total=2 * manifest['unique_source_plan_count'], total_wall_seconds=manifest['total_wall_seconds'])

    def progress(self, run_id):
        self._directory(run_id)
        with self.lock:
            if run_id in self.jobs:
                return deepcopy(self.jobs[run_id])
        saved = self.load_run(run_id)
        manifest = saved['run_manifest']
        return {key: manifest.get(key) for key in ('run_id', 'status', 'reason', 'total_wall_seconds')}

    def list_runs(self):
        """List sealed saved summaries without preparing a context or scorer."""
        results = []
        for path in sorted(self.output.glob('cross_*/run_manifest.json'), reverse=True):
            try:
                saved = self.load_run(path.parent.name)
            except (OSError, ValueError, KeyError):
                continue
            results.append({key: saved['run_manifest'].get(key) for key in
                ('run_id', 'created_at', 'sample_id', 'status', 'reason', 'strategy', 'budget', 'scope', 'target_credits')})
        return sorted(results, key=lambda row: row.get('created_at') or '', reverse=True)

    def load_run(self, run_id):
        """Verify the immutable result seal; never infer missing scores."""
        directory = self._directory(run_id)
        seal = json.loads((directory / 'integrity.json').read_text(encoding='utf-8'))
        if set(seal.get('sha256', {})) != {'run_manifest.json', 'rows.json'}:
            raise ValueError('Cross-model integrity seal is incomplete.')
        for name, expected in seal['sha256'].items():
            path = directory / name
            if path.is_symlink() or sha256(path) != expected:
                raise ValueError('Cross-model saved file hash integrity mismatch.')
        manifest = json.loads((directory / 'run_manifest.json').read_text(encoding='utf-8'))
        rows = json.loads((directory / 'rows.json').read_text(encoding='utf-8'))
        if manifest.get('run_id') != run_id or manifest.get('snapshot_id') != AFTER:
            raise ValueError('Cross-model saved identity integrity mismatch.')
        return {'run_manifest': manifest, 'rows': rows, 'status': manifest['status'], 'reason': manifest.get('reason')}
