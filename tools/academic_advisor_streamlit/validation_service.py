"""Read-only, privacy-limited views over immutable Pilot and search experiments.

This facade never starts a runner or constructs a prediction context. Historical
actual-plan forecasts and saved search recommendations retain separate provenance.
"""
from copy import deepcopy
from contextlib import closing
import json
import math
from pathlib import Path
import re
import sqlite3

from tools.academic_advisor_streamlit.pilot_service import PilotService, present_saved_result
from tools.recommendation_pilot_20251.actual_metrics import _error_statistics, _number, _prediction_metrics
from tools.recommendation_pilot_20251.adapter import PILOT_ROOT, load_student_inputs
from tools.recommendation_pilot_20251.search_benchmark import SearchBenchmarkService, compare_oracle
from tools.recommendation_pilot_20251.snapshots import AFTER, validate_snapshot


SUMMARY_FIELDS = ('start_agpa_points', 'start_total_in_credits', 'degree_credits_count', 'faculty_id',
                  'grade_version_id', 'prior_registered_semesters', 'previous_gpa', 'completed_credits',
                  'gpa_category', 'source')
COURSE_FIELDS = ('course_id', 'course_name', 'course_credits', 'grade_version_id', 'actual_mark',
                 'actual_points', 'result_status', 'course_outcome_status', 'predicted_mark',
                 'expected_points', 'fail_probability', 'actual_mark_reason', 'prediction_context',
                 'is_actual_course', 'error', 'fail_label', 'expected_grade',
                 'course_history_fallback_level', 'course_history_effective_support',
                 'similar_peer_support', 'peer_support_status', 'peer_minimum_support')
PLAN_FIELDS = ('rank', 'plan_id', 'canonical_id', 'total_credits', 'expected_plan_gpa',
               'expected_failed_credits', 'overlap_count', 'overlap_fraction')
EXPERIMENT_FIELDS = ('model', 'status', 'prediction_status', 'reason', 'scope', 'strategy', 'budget',
    'target_credits', 'target_credits_source', 'evaluated_plans', 'evaluated_plan_count', 'feasible_plan_count',
    'scope_plan_count', 'unique_plans_discovered', 'evaluated_plan_model_calls', 'heuristic_model_calls',
    'shared_plan_set_across_models', 'model_guidance', 'visited_search_states', 'candidate_exploration_coverage',
    'search_truncated', 'budget_shortfall', 'runtime_seconds', 'standalone_runtime_seconds',
    'search_preselection_seconds', 'shared_preparation_seconds', 'peak_process_memory_mb', 'best_gpa',
    'academic_validity', 'oracle_gpa', 'gpa_gap', 'top3_recall', 'score_equivalent_top3_recall',
    'oracle_equivalent_top1', 'score_fingerprint', 'oracle_fingerprint')
RESOLUTION_FIELDS = ('status', 'reason', 'target_credits', 'target_credits_source', 'minimum_credits', 'maximum_credits')
ASSET_FIELDS = ('status', 'reason', 'model_version', 'feature_count', 'training_as_of_part',
                'history_as_of_part', 'manifest_sha256', 'artifact_sha256', 'grade_scale_sha256',
                'reference_sha256', 'individual_source_sha256', 'roster_source_sha256')


def _safe_value(value):
    if value is None or isinstance(value, (bool, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, str):
        # Paths and free-form engine exceptions are never presentation data.
        if re.search(r'(?:[A-Za-z]:[\\/]|\\\\|(?:^|\s)/[\w.]+/)', value):
            return 'DETAIL_WITHHELD'
        return value
    if isinstance(value, (tuple, list)):
        return [_safe_value(v) for v in value if not isinstance(v, dict)]
    return None


def _pick(value, fields):
    return {key: _safe_value(value[key]) for key in fields if key in (value or {})}


def _fingerprints(value):
    """Keep source names and hash values, never arbitrary metadata or paths."""
    return {key: item for key, item in (value or {}).items()
            if key in ('student_response', 'courses_response', 'student_response.json', 'courses_response.json')
            and isinstance(item, str) and re.fullmatch('[a-fA-F0-9]{64}', item)}


def _asset(value):
    result = _pick(value, ASSET_FIELDS)
    hashes = value.get('artifact_sha256')
    if isinstance(hashes, dict):
        result['artifact_sha256'] = {key: digest for key, digest in hashes.items()
            if isinstance(key, str) and not re.search(r'[\\/:]', key)
            and isinstance(digest, str) and re.fullmatch('[a-fA-F0-9]{64}', digest)}
    history_hash = value.get('history_artifact_sha256')
    if isinstance(history_hash, str) and re.fullmatch('[a-fA-F0-9]{64}', history_hash):
        result['history_artifact_sha256'] = history_hash
    elif isinstance(history_hash, dict):
        result['history_artifact_sha256'] = {key: digest for key, digest in history_hash.items()
            if isinstance(key, str) and not re.search(r'[\\/:]', key)
            and isinstance(digest, str) and re.fullmatch('[a-fA-F0-9]{64}', digest)}
    return result


def _issues(value):
    return [_safe_value(item.get('code', 'SAVED_INPUT_ISSUE') if isinstance(item, dict) else str(item))
            for item in value or []]


def _course(course):
    fields = (*COURSE_FIELDS, *(f'{m}_{key}' for m in ('B', 'C')
                               for key in ('predicted_mark', 'expected_points', 'fail_probability', 'error', 'reason')))
    return _pick(course, fields)


def _plan(plan, rank=None):
    result = _pick(plan, PLAN_FIELDS)
    if rank is not None:
        result['rank'] = plan.get('rank', rank)
    result['courses'] = [_course(c) for c in plan.get('courses') or plan.get('course_rows') or []]
    result['course_rows'] = [_course(c) for c in plan.get('course_rows') or plan.get('courses') or []]
    result['plan_difficulty_balance'] = _pick(plan.get('plan_difficulty_balance') or {},
                                            ('max_fail_probability', 'mean_fail_probability', 'std_fail_probability'))
    return result


def _experiment(value):
    result = _pick(value, EXPERIMENT_FIELDS)
    result['top_plans'] = [_plan(p, i) for i, p in enumerate(value.get('top_plans') or [], 1)]
    return result


def _reference(ref, default='historical'):
    if not isinstance(ref, dict) or ref.get('kind', default) not in ('historical', 'benchmark'):
        raise ValueError('Select an explicit saved source.')
    run_id = ref.get('run_id')
    if not isinstance(run_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]+', run_id):
        raise ValueError('Invalid saved run identifier.')
    family = ref.get('family', 'comparison')
    if family not in ('comparison', 'actual_candidate_injection'):
        raise ValueError('Unknown historical family.')
    return {'kind': ref.get('kind', default), 'run_id': run_id, 'family': family}


class ValidationService:
    """Saved-data facade; injectable collaborators make absence of scoring testable."""

    def __init__(self, root=PILOT_ROOT, pilot=None, search=None):
        self.root = Path(root)
        self.pilot = pilot if pilot is not None else PilotService(root=self.root)
        self.search = search if search is not None else SearchBenchmarkService(root=self.root)

    def cohort(self):
        return [_pick(row, ('sample_id', 'part_id')) for row in self.pilot.cohort()]

    def catalog(self, snapshot_id=AFTER):
        validate_snapshot(snapshot_id)
        historical = []
        for item in self.pilot.list_runs():
            if item.get('snapshot_id') != snapshot_id:
                continue
            row = _pick(item, ('run_id', 'family', 'snapshot_id', 'student_count', 'status', 'created_at', 'target_credits'))
            row['key'] = f"{row.get('family', 'comparison')}:{row['run_id']}"
            historical.append(row)
        benchmark = []
        for item in self.search.list_runs():
            saved = self.search.load_run(item['run_id'])
            manifest = saved.get('run_manifest') or {}
            if manifest.get('snapshot_id') != snapshot_id:
                continue
            row = _pick(manifest, ('run_id', 'snapshot_id', 'status', 'created_at'))
            row.update(key='benchmark:' + item['run_id'], student_count=len(saved.get('student_results') or []),
                       configuration=_pick(manifest.get('configuration') or {},
                                           ('models', 'strategies', 'budgets', 'scopes', 'seed', 'manual_target')))
            benchmark.append(row)
        return {'historical': historical, 'benchmark': benchmark}

    def preview(self, sample_id, snapshot_id=AFTER):
        validate_snapshot(snapshot_id)
        students = {s['sample_id']: s for s in self.pilot.cohort(include_reserve=True)}
        if sample_id not in students:
            raise ValueError('Unknown saved sample.')
        student = students[sample_id]
        result = {'sample_id': sample_id, 'snapshot_id': snapshot_id, 'part_id': student.get('part_id'),
                  'status': 'BLOCKED', 'reason': None, 'student_summary': {}, 'issues': [], 'input_fingerprints': {}}
        try:
            preview = self.pilot.preview(sample_id, snapshot_id=snapshot_id)
            result.update(_pick(preview, ('status', 'reason')))
            result['student_summary'] = _pick(preview.get('student_summary') or {}, SUMMARY_FIELDS)
            result['credit_target_resolution'] = _pick(preview.get('credit_target_resolution') or {}, RESOLUTION_FIELDS)
            result['issues'] = _issues(preview.get('issues'))
            result['input_fingerprints'] = _fingerprints(preview.get('input_fingerprints'))
        except (ValueError, KeyError, OSError, RuntimeError) as error:
            result['reason'] = getattr(error, 'code', 'SAVED_INPUT_UNAVAILABLE')
        if not result['input_fingerprints']:
            try:
                inputs = load_student_inputs(student, self.root, snapshot_id=snapshot_id)
                result['input_fingerprints'] = _fingerprints(inputs.get('fingerprints'))
            except (ValueError, KeyError, OSError, RuntimeError):
                pass
        return result

    def _load(self, ref):
        return (self.search.load_run(ref['run_id']) if ref['kind'] == 'benchmark'
                else self.pilot.load_run(ref['run_id'], family=ref['family']))

    def _select(self, saved, sample_id, snapshot_id, scenario=None):
        manifest = saved.get('run_manifest') or {}
        if (saved.get('snapshot_id') or manifest.get('snapshot_id')) != snapshot_id:
            return None, 'SNAPSHOT_MISMATCH'
        rows = [r for r in saved.get('student_results') or [] if r.get('sample_id') == sample_id]
        if scenario is not None:
            rows = [r for r in rows if (r.get('candidate_mode'), r.get('credit_experiment')) == tuple(scenario)]
        if not rows:
            return None, 'SAMPLE_NOT_IN_SAVED_RUN'
        if len(rows) != 1:
            return None, 'EXPLICIT_SCENARIO_REQUIRED'
        cohort = {r['sample_id']: r for r in self.cohort()}
        if sample_id not in cohort:
            return None, 'UNKNOWN_SAVED_SAMPLE'
        expected = cohort[sample_id].get('part_id')
        recorded = rows[0].get('part_id', manifest.get('part_id'))
        if recorded is not None and expected is not None and str(recorded) != str(expected):
            return None, 'SEMESTER_MISMATCH'
        if rows[0].get('snapshot_id', snapshot_id) != snapshot_id:
            return None, 'SNAPSHOT_MISMATCH'
        return rows[0], None

    def _provenance(self, saved, row, ref):
        manifest = saved.get('run_manifest') or {}
        models = row.get('model_assets') or manifest.get('models') or {}
        return {'source_ref': deepcopy(ref), 'run_id': ref['run_id'], 'family': ref['family'],
            'kind': ref['kind'], 'snapshot_id': manifest.get('snapshot_id') or saved.get('snapshot_id'),
            'part_id': row.get('part_id', manifest.get('part_id')) or next(
                (r.get('part_id') for r in self.cohort() if r['sample_id'] == row.get('sample_id')), None),
            'sample_id': row.get('sample_id'), 'history_as_of_part': manifest.get('history_as_of_part'),
            'input_fingerprints': _fingerprints(row.get('input_fingerprints') or (manifest.get('student_inputs') or {}).get(row.get('sample_id'))),
            'model_versions': _pick(manifest.get('model_versions') or {}, ('B', 'C')),
            'model_assets': {m: _asset(models.get(m) or {}) for m in ('B', 'C')},
            'fingerprint': _safe_value(row.get('fingerprint')), 'candidate_sha256': _safe_value(row.get('candidate_sha256')),
            'target_resolution': _pick(row.get('target_resolution') or row.get('credit_target_resolution') or {}, RESOLUTION_FIELDS),
            'configuration': _pick(manifest.get('configuration') or {}, ('models', 'strategies', 'budgets', 'scopes', 'seed', 'manual_target')),
            'actual_course_injection': manifest.get('actual_course_injection', False),
            'result_source': 'saved_run', 'historical_observations_independent_of_search': True}

    def student(self, sample_id, *, snapshot_id=AFTER, historical_ref, scenario=None):
        validate_snapshot(snapshot_id)
        ref = _reference(historical_ref)
        saved = self._load(ref)
        row, reason = self._select(saved, sample_id, snapshot_id, scenario)
        if reason:
            return {'status': 'UNAVAILABLE', 'reason': reason, 'student_summary': {}, 'actual_summary': {},
                    'actual_course_rows': [], 'issues': [reason], 'provenance': {}}
        presentation = present_saved_result(saved, sample_id, scenario=scenario)
        # The existing presenter owns grade/point and saved forecast semantics.
        result = {'sample_id': sample_id, 'status': 'AVAILABLE', 'reason': None,
            'recommendation_status': row.get('status'), 'student_summary': _pick(presentation['student_summary'], SUMMARY_FIELDS),
            'actual_summary': deepcopy(presentation['actual_summary']),
            'actual_course_rows': [_course(r) for r in presentation['actual_course_rows']],
            'summary_rows': [_pick(r, (*EXPERIMENT_FIELDS, 'best_predicted_plan_gpa', 'actual_plan_gpa',
                                      'actual_plan_gpa_error', 'actual_plan_gpa_absolute_error')) for r in presentation['summary_rows']],
            'issues': _issues(presentation['warnings']), 'provenance': self._provenance(saved, row, ref),
            'prediction_metrics': {m: _prediction_metrics(row.get('observed_plan'),
                ((row.get('observed_plan_prediction') or {}).get('experiments') or {}).get(m)) for m in ('B', 'C')}}
        return result

    def _compatible(self, saved, row, sample_id, snapshot_id, target_credits):
        preview = self.preview(sample_id, snapshot_id)
        expected = preview.get('input_fingerprints')
        actual = row.get('input_fingerprints') or ((saved.get('run_manifest') or {}).get('student_inputs') or {}).get(sample_id)
        if not expected or not actual:
            return None, 'INPUT_FINGERPRINT_UNAVAILABLE'
        if actual != expected:
            return None, 'INPUT_FINGERPRINT_MISMATCH'
        target = _number(target_credits)
        if target_credits is None:
            target = _number((preview.get('credit_target_resolution') or {}).get('target_credits'))
        if target is None or target <= 0:
            return None, 'TARGET_CREDITS_UNAVAILABLE'
        recorded = _number(row.get('target_credits', (row.get('target_resolution') or {}).get('target_credits')))
        if recorded != target:
            return target, 'TARGET_CREDITS_MISMATCH'
        return target, None

    def recommendations(self, sample_id, *, snapshot_id=AFTER, source_ref, strategy='SMART_SEARCH',
                        budget=1000, scope='FULL_SPACE', target_credits=None, allow_historical=False):
        validate_snapshot(snapshot_id)
        ref = _reference(source_ref)
        saved = self._load(ref)
        row, reason = self._select(saved, sample_id, snapshot_id)
        empty = {'status': 'UNAVAILABLE', 'reason': reason, 'models': {}, 'provenance': {}}
        if reason:
            return empty
        provenance = self._provenance(saved, row, ref)
        target, reason = self._compatible(saved, row, sample_id, snapshot_id, target_credits)
        provenance.update(target_credits=target, strategy=strategy, budget=budget, scope=scope)
        if reason and not (ref['kind'] == 'historical' and allow_historical and reason == 'TARGET_CREDITS_MISMATCH'):
            return {**empty, 'reason': reason, 'provenance': provenance}
        if ref['kind'] == 'historical':
            manifest = saved.get('run_manifest') or {}
            settings = manifest.get('generation_settings') or {}
            recorded = {'strategy': (row.get('search') or {}).get('strategy', 'FIRST_N'),
                        'budget': settings.get('max_plans'), 'scope': 'FULL_SPACE',
                        'target_credits': row.get('target_credits', manifest.get('target_credits'))}
            provenance.update(recorded_configuration=recorded, legacy=True,
                              requested_configuration={'strategy': strategy, 'budget': budget, 'scope': scope, 'target_credits': target})
            if not allow_historical:
                return {**empty, 'reason': 'LEGACY_SOURCE_REQUIRES_EXPLICIT_OPT_IN', 'provenance': provenance}
            presentation = present_saved_result(saved, sample_id)
            models = {m: {**_pick((row.get('experiments') or {}).get(m) or {}, EXPERIMENT_FIELDS), **recorded,
                           'top_plans': [_plan(p, i) for i, p in enumerate(presentation['plans_by_model'].get(m) or [], 1)]}
                      for m in ('B', 'C') if m in (row.get('experiments') or {})}
            return {'status': 'AVAILABLE_LEGACY', 'reason': 'ORIGINAL_RECORDED_CONFIGURATION', 'models': models, 'provenance': provenance}
        experiments = row.get('experiments') or []
        selected = [e for e in experiments if e.get('strategy') == strategy and e.get('scope') == scope
                    and e.get('budget') == budget and _number(e.get('target_credits')) == target and e.get('model') in ('B', 'C')]
        if not selected or len({e['model'] for e in selected}) != len(selected):
            return {**empty, 'reason': 'EXACT_SAVED_CONFIGURATION_UNAVAILABLE', 'provenance': provenance}
        return {'status': 'AVAILABLE', 'reason': None, 'models': {e['model']: _experiment(e) for e in selected}, 'provenance': provenance}

    def source_compatibility(self, sample_id, *, snapshot_id=AFTER, historical_ref, source_ref):
        """Keep actual-plan model/input compatibility separate from plan load matching."""
        validate_snapshot(snapshot_id)
        historical = _reference(historical_ref)
        source = _reference(source_ref)
        first, second = self._load(historical), self._load(source)
        a, a_reason = self._select(first, sample_id, snapshot_id)
        b, b_reason = self._select(second, sample_id, snapshot_id)
        issues = [reason for reason in (a_reason, b_reason) if reason]
        if issues:
            return {'status': 'INCOMPATIBLE', 'observed_forecast_compatible': False,
                    'recommendation_target_compatible': False, 'issues': issues}
        pa, pb = self._provenance(first, a, historical), self._provenance(second, b, source)
        if not pa['input_fingerprints'] or not pb['input_fingerprints']:
            issues.append('INPUT_FINGERPRINT_UNAVAILABLE')
        elif pa['input_fingerprints'] != pb['input_fingerprints']:
            issues.append('INPUT_FINGERPRINT_MISMATCH')
        for model in ('B', 'C'):
            left, right = pa['model_assets'][model], pb['model_assets'][model]
            left_version = left.get('model_version') or pa['model_versions'].get(model)
            right_version = right.get('model_version') or pb['model_versions'].get(model)
            if not left_version or not right_version:
                issues.append('MODEL_FINGERPRINT_UNAVAILABLE:' + model)
            elif left_version != right_version:
                issues.append('MODEL_FINGERPRINT_MISMATCH:' + model)
            elif any(left.get(key) != right.get(key) for key in ASSET_FIELDS
                     if key not in ('status', 'reason', 'model_version') and (left.get(key) is not None or right.get(key) is not None)):
                issues.append('MODEL_FINGERPRINT_MISMATCH:' + model)
        observed = not issues
        ta = _number(a.get('target_credits', (a.get('target_resolution') or {}).get('target_credits')))
        tb = _number(b.get('target_credits', (b.get('target_resolution') or {}).get('target_credits')))
        target_match = ta is not None and ta == tb
        if not target_match:
            issues.append('TARGET_CREDITS_MISMATCH' if ta is not None and tb is not None else 'TARGET_CREDITS_UNAVAILABLE')
        return {'status': 'COMPATIBLE' if observed and target_match else 'PARTIAL' if observed else 'INCOMPATIBLE',
                'observed_forecast_compatible': observed, 'recommendation_target_compatible': target_match,
                'historical_target_credits': ta, 'source_target_credits': tb,
                'issues': issues, 'historical_provenance': pa, 'source_provenance': pb}

    @staticmethod
    def _oracle_complete(experiment):
        proof = experiment.get('completeness_proof') or {}
        count = _number(experiment.get('feasible_plan_count'))
        return (experiment.get('status') == 'EXHAUSTIVE_COMPLETE' and experiment.get('scope') == 'EXHAUSTIVE'
                and experiment.get('strategy') == 'EXHAUSTIVE' and count is not None and count > 0
                and proof.get('all_feasible_plans_scored') is True
                and proof.get('sequential_dfs_ordinals') is True and proof.get('transactional_checkpoint') is True
                and proof.get('unique_scored_count') == count == proof.get('expected_feasible_count')
                and experiment.get('evaluated_plans') == count and bool(proof.get('score_chain_sha256')))

    def _oracle_journal(self, saved, row, oracle, selected):
        """Optional ordinal/tie diagnostics use SQLite URI mode=ro; never ScoreLedger."""
        storage = saved.get('storage_path')
        if not storage:
            return {'status': 'UNAVAILABLE', 'reason': 'SAVED_SCORE_JOURNAL_UNAVAILABLE'}
        base = Path(storage).resolve()
        approved = (self.root / 'experiments' / AFTER / 'search_benchmark').resolve()
        journal = base / row['sample_id'] / 'scores.sqlite'
        if not base.is_relative_to(approved) or not journal.resolve().is_relative_to(base) or not journal.is_file():
            return {'status': 'UNAVAILABLE', 'reason': 'SAVED_SCORE_JOURNAL_UNAVAILABLE'}
        job = f"EXHAUSTIVE/EXHAUSTIVE/None/{oracle['model']}"
        try:
            with closing(sqlite3.connect(journal.as_uri() + '?mode=ro', uri=True)) as connection:
                connection.execute('PRAGMA query_only=ON')
                best = oracle['top_plans'][0]['expected_plan_gpa']
                count = connection.execute('SELECT COUNT(*) FROM scores WHERE job=?', (job,)).fetchone()[0]
                if count != oracle['feasible_plan_count']:
                    return {'status': 'UNAVAILABLE', 'reason': 'ORACLE_JOURNAL_COUNT_MISMATCH'}
                ties = connection.execute('SELECT COUNT(*) FROM scores WHERE job=? AND ABS(gpa-?)<=1e-10', (job, best)).fetchone()[0]
                ranks = []
                for strategy, plans in selected.items():
                    for rank, plan in enumerate(plans, 1):
                        match = connection.execute('SELECT ordinal,gpa,failed,risk FROM scores WHERE job=? AND canonical=?',
                                                   (job, plan.get('canonical_id'))).fetchone()
                        if match:
                            ordinal, gpa, failed, risk = match
                            better = connection.execute('''SELECT COUNT(*) FROM scores WHERE job=? AND
                                (gpa>? OR (gpa=? AND failed<?) OR (gpa=? AND failed=? AND risk<?) OR
                                (gpa=? AND failed=? AND risk=? AND (LENGTH(ordinal)<? OR
                                  (LENGTH(ordinal)=? AND ordinal<?))))''',
                                (job,gpa,gpa,failed,gpa,failed,risk,gpa,failed,risk,len(ordinal),len(ordinal),ordinal)).fetchone()[0]
                            ranks.append({'strategy': strategy, 'rank': rank, 'oracle_rank': better + 1,
                                          'canonical_id': plan.get('canonical_id')})
                return {'status': 'AVAILABLE', 'tied_optimal_count': ties, 'ordinal_ranks': ranks}
        except (sqlite3.Error, OSError, KeyError, IndexError):
            return {'status': 'UNAVAILABLE', 'reason': 'SAVED_SCORE_JOURNAL_UNAVAILABLE'}

    def search_comparison(self, sample_id, *, snapshot_id=AFTER, run_id, model='B', budget=1000,
                          scope='FULL_SPACE', target_credits=None):
        validate_snapshot(snapshot_id)
        if model not in ('B', 'C'):
            raise ValueError('Select model B or C.')
        ref = _reference({'kind': 'benchmark', 'run_id': run_id})
        saved = self._load(ref)
        row, reason = self._select(saved, sample_id, snapshot_id)
        result = {'status': 'UNAVAILABLE', 'reason': reason, 'rows': [], 'plans_by_strategy': {},
                  'oracle_status': 'UNAVAILABLE', 'oracle_summary': {}, 'provenance': {}}
        if reason:
            return result
        result['provenance'] = self._provenance(saved, row, ref)
        target, reason = self._compatible(saved, row, sample_id, snapshot_id, target_credits)
        if reason:
            return {**result, 'reason': reason}
        experiments = [e for e in row.get('experiments') or [] if e.get('model') == model
                       and _number(e.get('target_credits')) == target]
        selected = [e for e in experiments if e.get('scope') == scope and e.get('budget') == budget
                    and e.get('strategy') in ('FIRST_N', 'DIVERSE_N', 'SMART_SEARCH')]
        if len({e['strategy'] for e in selected}) != len(selected):
            return {**result, 'reason': 'AMBIGUOUS_SAVED_CONFIGURATION'}
        oracles = [e for e in experiments if self._oracle_complete(e)]
        oracle = oracles[0] if len(oracles) == 1 else None
        result['oracle_status'] = 'EXHAUSTIVE_COMPLETE' if oracle else 'EXHAUSTIVE_INCOMPLETE_OR_UNAVAILABLE'
        for experiment in selected:
            safe = _experiment(experiment)
            # Previously saved oracle-derived numbers are withheld unless proof survives.
            comparison = compare_oracle(experiment.get('top_plans') or [], oracle.get('top_plans') or [] if oracle else [],
                                       oracle_complete=oracle is not None)
            # Discovery recall includes every examined plan, not merely displayed top-three.
            for metric in ('top3_recall', 'score_equivalent_top3_recall'):
                comparison[metric] = (experiment.get(metric) if oracle is not None and
                    experiment.get('oracle_fingerprint') == oracle.get('score_fingerprint') and
                    bool(oracle.get('score_fingerprint')) else None)
            safe.update(comparison)
            result['rows'].append({key: value for key, value in safe.items() if key != 'top_plans'})
            result['plans_by_strategy'][experiment['strategy']] = safe['top_plans']
        for strategy in ('FIRST_N', 'DIVERSE_N', 'SMART_SEARCH'):
            if strategy not in result['plans_by_strategy']:
                result['rows'].append({'model': model, 'strategy': strategy, 'scope': scope, 'budget': budget,
                    'target_credits': target, 'status': 'UNAVAILABLE', 'reason': 'EXACT_SAVED_CONFIGURATION_UNAVAILABLE'})
                result['plans_by_strategy'][strategy] = []
        result['rows'].sort(key=lambda item: ('FIRST_N', 'DIVERSE_N', 'SMART_SEARCH').index(item['strategy']))
        if oracle:
            safe = _experiment(oracle)
            result['rows'].append({key: value for key, value in safe.items() if key != 'top_plans'})
            result['plans_by_strategy']['EXHAUSTIVE'] = safe['top_plans']
            result['oracle_summary'] = {**_pick(oracle, ('best_gpa', 'evaluated_plans', 'feasible_plan_count', 'score_fingerprint')),
                'completeness_proof': _pick(oracle.get('completeness_proof') or {},
                    ('all_feasible_plans_scored', 'unique_scored_count', 'expected_feasible_count',
                     'sequential_dfs_ordinals', 'transactional_checkpoint', 'score_chain_sha256')),
                **self._oracle_journal(saved, row, oracle, result['plans_by_strategy'])}
        return {**result, 'status': 'AVAILABLE' if selected else 'UNAVAILABLE',
                'reason': None if selected else 'EXACT_SAVED_CONFIGURATION_UNAVAILABLE'}

    def cohort_evaluation(self, historical_ref, *, snapshot_id=AFTER, sample_ids=None, models=('B', 'C'),
                          statuses=None, starting_category=None, actual_gpa_range=None):
        validate_snapshot(snapshot_id)
        ref = _reference(historical_ref)
        saved = self._load(ref)
        wanted = set(sample_ids) if sample_ids is not None else None
        status_filter = {statuses} if isinstance(statuses, str) else set(statuses or [])
        selected_models = [m for m in dict.fromkeys(models) if m in ('B', 'C')]
        students, courses, plans, seen, selected_ids = [], [], [], set(), set()
        signatures, conflicts, issues = {}, set(), []
        for raw in saved.get('student_results') or []:
            sample = raw.get('sample_id')
            if wanted is not None and sample not in wanted or status_filter and raw.get('status') not in status_filter:
                continue
            for model in selected_models:
                forecast = ((raw.get('observed_plan_prediction') or {}).get('experiments') or {}).get(model) or {}
                signature = json.dumps({'metrics': _prediction_metrics(raw.get('observed_plan'), forecast),
                    'predicted_actual_plan_gpa': _number(forecast.get('expected_plan_gpa')),
                    'observed_courses': [_course(c) for c in (raw.get('observed_plan') or {}).get('courses') or []]},
                    sort_keys=True, allow_nan=False)
                key = (sample, model)
                if key in signatures and signatures[key] != signature:
                    conflicts.add(key)
                signatures[key] = signature
        provenance = {'source_ref': ref, 'snapshot_id': snapshot_id,
                      'run_id': ref['run_id'],
                      'model_versions': _pick((saved.get('run_manifest') or {}).get('model_versions') or {}, ('B', 'C')),
                      'part_id': (saved.get('run_manifest') or {}).get('part_id'),
                      'metric_context': 'independent_saved_actual_registered_plan_forecasts',
                      'filters_applied_before_aggregation': True}
        if ((saved.get('run_manifest') or {}).get('snapshot_id') or saved.get('snapshot_id')) != snapshot_id:
            return {'status': 'UNAVAILABLE', 'reason': 'SNAPSHOT_MISMATCH', 'metrics': [], 'students': [],
                    'courses': [], 'plans': [], 'provenance': provenance, 'total_students': 0}
        for raw in saved.get('student_results') or []:
            sample = raw.get('sample_id')
            if wanted is not None and sample not in wanted or status_filter and raw.get('status') not in status_filter:
                continue
            if sample in seen:
                # Scenarios must never multiply the cohort's label denominators.
                continue
            seen.add(sample)
            scenario = (raw.get('candidate_mode'), raw.get('credit_experiment')) if raw.get('candidate_mode') is not None else None
            view = self.student(sample, snapshot_id=snapshot_id, historical_ref=ref, scenario=scenario)
            if view.get('status') != 'AVAILABLE':
                continue
            summary, actual = view['student_summary'], view['actual_summary']
            starting_gpa = _number(summary.get('start_agpa_points'))
            category = ('unavailable' if starting_gpa is None else 'below_2' if starting_gpa < 2 else 'at_least_2')
            if starting_category is not None and (category != starting_category if starting_category in
                    ('below_2', 'at_least_2', 'unavailable') else summary.get('gpa_category') != starting_category):
                continue
            actual_gpa = _number(actual.get('descriptive_gpa'))
            if actual_gpa_range is not None and (actual_gpa is None or not actual_gpa_range[0] <= actual_gpa <= actual_gpa_range[1]):
                continue
            selected_ids.add(sample)
            presentation = present_saved_result({'run_manifest': saved.get('run_manifest'), 'student_results': [raw]}, sample)
            for model in selected_models:
                if (sample, model) in conflicts:
                    issues.append(f'CONFLICTING_SAVED_ACTUAL_FORECAST:{sample}:{model}')
                    students.append({'sample_id': sample, 'model': model, 'status': 'CONFLICTING_SAVED_ACTUAL_FORECAST',
                        'source_run_id': ref['run_id'], 'starting_gpa': _number(summary.get('start_agpa_points')),
                        'actual_plan_gpa': actual_gpa, 'predicted_actual_plan_gpa': None,
                        'actual_plan_gpa_error': None, 'actual_plan_gpa_absolute_error': None,
                        'course_count': 0, 'reason': 'SCENARIO_FORECASTS_DIFFER'})
                    continue
                metrics = view['prediction_metrics'][model]
                forecast = (actual.get('models') or {}).get(model) or {}
                students.append({'sample_id': sample, 'model': model, 'status': raw.get('status'),
                    'source_run_id': ref['run_id'], 'runtime_seconds': _number(
                        ((raw.get('experiments') or {}).get(model) or {}).get('elapsed_seconds')),
                    'starting_gpa': starting_gpa, 'starting_category': category,
                    'candidate_count': _number(raw.get('candidate_count')),
                    'prediction_status': forecast.get('status'),
                    'recommendation_status': ((raw.get('experiments') or {}).get(model) or {}).get('prediction_status',
                        ((raw.get('experiments') or {}).get(model) or {}).get('status')),
                    'actual_plan_gpa': actual_gpa, **_pick(forecast, ('predicted_actual_plan_gpa', 'actual_plan_gpa_error',
                        'actual_plan_gpa_absolute_error')), **_pick(metrics, ('mae', 'rmse', 'bias', 'course_count', 'fail_count',
                        'fail_brier', 'fail_log_loss', 'fail_roc_auc'))})
                courses.extend({'sample_id': sample, 'model': model, **_course(c)} for c in metrics['course_errors'])
                plans.extend({'sample_id': sample, 'model': model, **_plan(plan, rank)}
                             for rank, plan in enumerate(presentation['plans_by_model'].get(model) or [], 1))
        metric_rows = []
        for model in selected_models:
            model_students = [s for s in students if s['model'] == model]
            usable = [c for c in courses if c['model'] == model]
            stats = _error_statistics(usable)
            for metric in ('mae', 'rmse', 'bias', 'fail_brier', 'fail_log_loss', 'fail_roc_auc'):
                pairs = [c for c in usable if c.get('fail_label') is not None and c.get('fail_probability') is not None] if metric.startswith('fail_') else usable
                metric_rows.append({'model': model, 'metric': metric, 'value': stats[metric],
                    'student_count': len({c['sample_id'] for c in pairs}), 'course_observations': len(pairs)})
            errors = [s['actual_plan_gpa_error'] for s in students if s['model'] == model and _number(s.get('actual_plan_gpa_error')) is not None]
            for metric, value in (('plan_gpa_mae', sum(abs(e) for e in errors) / len(errors) if errors else None),
                                  ('plan_gpa_rmse', math.sqrt(sum(e * e for e in errors) / len(errors)) if errors else None),
                                  ('plan_gpa_bias', sum(errors) / len(errors) if errors else None)):
                metric_rows.append({'model': model, 'metric': metric, 'value': value,
                                    'student_count': len(errors), 'course_observations': None})
            def append_metric(metric, value, observations):
                metric_rows.append({'model': model, 'metric': metric, 'value': value,
                    'student_count': len(observations), 'course_observations': None})
            append_metric('total_students', len(model_students), model_students)
            append_metric('actual_prediction_available', sum(_number(s.get('predicted_actual_plan_gpa')) is not None
                          for s in model_students), model_students)
            available = [s for s in model_students if s.get('recommendation_status') == 'PREDICTION_AVAILABLE']
            append_metric('recommendation_available', len(available), model_students)
            append_metric('recommendation_coverage', len(available) / len(model_students) if model_students else None, model_students)
            for status in ('BLOCKED', 'NO_MATCHING_PLAN'):
                append_metric(status, sum(s.get('status') == status or s.get('recommendation_status') == status
                    for s in model_students), model_students)
            for field, metric in [('candidate_count', 'mean_candidate_count'), ('runtime_seconds', 'mean_runtime_seconds')]:
                measured = [s for s in model_students if _number(s.get(field)) is not None]
                append_metric(metric, sum(s[field] for s in measured) / len(measured) if measured else None, measured)
            from tools.academic_advisor_streamlit.validation_views import plan_comparison
            similarities = []
            for student in model_students:
                selected_plans = [p for p in plans if p['model'] == model and p['sample_id'] == student['sample_id']]
                pairs = plan_comparison(selected_plans[:3])['pairs']
                if pairs:
                    similarities.append(sum(p['jaccard'] for p in pairs) / len(pairs))
            metric_rows.append({'model': model, 'metric': 'mean_top3_jaccard',
                'value': sum(similarities) / len(similarities) if similarities else None,
                'student_count': len(similarities), 'course_observations': None})
        return {'status': 'AVAILABLE', 'reason': None, 'metrics': metric_rows, 'students': students,
                'courses': courses, 'plans': plans, 'provenance': provenance, 'total_students': len(selected_ids), 'issues': issues}
