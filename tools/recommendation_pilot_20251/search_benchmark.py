"""Offline search experiments, sharing Pilot inference and analytical ranking.

No network, training, observed-plan access or oracle-guided selection occurs here.
SQLite commits scores and the resume cursor in one transaction. Only the best
three plans retain expanded course predictions; all scores remain auditable.
"""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import argparse
import csv
import hashlib
import itertools
import json
import math
from pathlib import Path
import re
import sqlite3
from threading import RLock
from time import perf_counter, sleep
from uuid import uuid4

import numpy as np
import pandas as pd

from src import paths
from src.recommendation.plan_generation import build_plan_rows
from .adapter import PILOT_ROOT, TARGET_PART, TIMING_LIMITATION, PilotInputError, load_student_inputs, read_students, sha256
from .engine import POLICY_ISSUES, PilotEngine, _candidates, _digest, _json_safe, build_snapshot, student_summary
from .snapshots import AFTER, manifest_context


STRATEGIES = ('FIRST_N', 'DIVERSE_N', 'SMART_SEARCH')
SCOPES = ('FIXED_POOL', 'FULL_SPACE', 'EXHAUSTIVE')
BUDGETS = (200, 1000, 2000)
FORMAT_VERSION = 1


class IntegrityError(ValueError):
    """A persisted result cannot be certified or safely resumed."""


def canonical_plan_id(course_ids):
    return _digest(sorted(map(str, course_ids)))


def ranking_key(plan):
    """Original Pilot final tie break is the deterministic include-first ordinal."""
    return (-plan['expected_plan_gpa'], plan['expected_failed_credits'],
            plan['plan_difficulty_balance']['max_fail_probability'], int(plan['plan_id']))


def atomic_json(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(_json_safe(value), ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    for attempt in range(5):
        try:
            temporary.replace(path)
            break
        except PermissionError:
            if attempt == 4:
                raise
            sleep(.02 * (attempt + 1))


def code_fingerprints():
    base = Path(__file__).resolve().parent
    repo = base.parents[1]
    files = [*base.glob('*.py'), *(repo / 'src').rglob('*.py'),
             *(repo / 'scripts/experiments/attempt_sum_removal').glob('*.py')]
    return {p.relative_to(base.parents[1]).as_posix(): sha256(p) for p in files}


def memory_mb():
    try:
        import psutil
        info = psutil.Process().memory_info()
        return max(info.rss, getattr(info, 'peak_wset', 0)) / 1024**2
    except ImportError:
        return None


@dataclass(frozen=True)
class ResourceLimits:
    max_seconds: float = 300.
    max_oracle_plans: int = 50000
    chunk_size: int = 128
    max_space_states: int = 2000000
    max_disk_mb: float = 512.
    max_memory_mb: float = 2048.

    def __post_init__(self):
        for key, value in asdict(self).items():
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
                raise ValueError('Invalid resource limit: ' + key)
        for key in ('max_oracle_plans', 'chunk_size', 'max_space_states'):
            if not isinstance(getattr(self, key), int):
                raise ValueError('Integer resource limit required: ' + key)
        if self.chunk_size > 512:
            raise ValueError('Chunk size must be at most 512 plans.')


def validate_configuration(models, strategies, budgets, scopes):
    for values, allowed in [(models, ('B', 'C')), (strategies, STRATEGIES), (budgets, BUDGETS), (scopes, SCOPES)]:
        if not values or len(set(values)) != len(values) or any(v not in allowed for v in values):
            raise ValueError('Invalid or duplicated benchmark configuration.')
    if any(isinstance(b, bool) for b in budgets):
        raise ValueError('Invalid plan budget.')


def score_chunk(base, plans, ranks, scorer, model):
    """Build every complete plan context and delegate unchanged B/C scoring."""
    from .actual_experiment import _TimedExperiments, _timings
    started = perf_counter()
    rows = build_plan_rows(base, plans)
    preparation = perf_counter() - started
    timings = {model: _timings()}
    timed = _TimedExperiments(scorer, timings)
    scored = timed.predict_course_rows(rows, model)
    ranking_started = perf_counter()
    experiment = {}
    PilotEngine._attach_scores(experiment, scored, model)
    result = experiment['diagnostic_plans']
    for plan in result:
        ordinal = int(ranks[plan['plan_id']])
        plan['plan_id'] = ordinal
        plan['canonical_id'] = canonical_plan_id(c['course_id'] for c in plan['courses'])
        for course in plan['courses']:
            course['plan_id'] = ordinal
        plan['enforceable_constraints_validated'] = True
    return result, {
        'feature_preparation_seconds': preparation + timings[model]['feature_extraction_seconds'],
        'full_plan_inference_seconds': timings[model]['prediction_seconds'],
        'ranking_seconds': perf_counter() - ranking_started,
        'scoring_wall_seconds': perf_counter() - started,
        'inference_timing_available': hasattr(scorer, '_load'),
        'scored_course_rows': len(scored),
        'scored_complete_plans': len(plans),
    }


def _compact(plan):
    return dict(ordinal=str(plan['plan_id']), canonical=plan['canonical_id'], credits=float(plan['total_credits']),
                gpa=float(plan['expected_plan_gpa']), failed=float(plan['expected_failed_credits']),
                risk=float(plan['plan_difficulty_balance']['max_fail_probability']))


class ScoreLedger:
    """Bounded-memory score journal; cursors and top-three are transactionally durable."""
    def __init__(self, path, fingerprint):
        self.path = Path(path)
        self.connection = sqlite3.connect(path)
        self.connection.execute('PRAGMA journal_mode=DELETE')
        self.connection.executescript('''
            CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS scores (
                job TEXT, sequence INTEGER, ordinal TEXT, canonical TEXT, credits REAL,
                gpa REAL, failed REAL, risk REAL, checksum TEXT,
                PRIMARY KEY(job,sequence), UNIQUE(job,ordinal), UNIQUE(job,canonical));
            CREATE TABLE IF NOT EXISTS checkpoints (
                job TEXT PRIMARY KEY, count INTEGER, chain TEXT, top_json TEXT, timing_json TEXT, top_checksum TEXT);
        ''')
        prior = self.connection.execute("SELECT value FROM metadata WHERE key='fingerprint'").fetchone()
        if prior and prior[0] != fingerprint:
            self.close()
            raise IntegrityError('Resume fingerprint mismatch.')
        self.connection.execute("INSERT OR IGNORE INTO metadata VALUES ('fingerprint',?)", (fingerprint,))
        self.connection.commit()

    def close(self):
        self.connection.close()

    def _checkpoint(self, job):
        row = self.connection.execute('SELECT count,chain,top_json,timing_json,top_checksum FROM checkpoints WHERE job=?', (job,)).fetchone()
        if row and _digest(json.loads(row[2])) != row[4]:
            raise IntegrityError('Expanded top-three checksum mismatch.')
        return (row[0], row[1], json.loads(row[2]), json.loads(row[3])) if row else (0, '', [], {})

    def cursor(self, job):
        return self._checkpoint(job)[0]

    def commit(self, job, plans, timings):
        count, chain, top, total_time = self._checkpoint(job)
        # Scoring and feature/ranking timers are disjoint; scoring_wall is an overlapping diagnostic total.
        for key, value in timings.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                total_time[key] = total_time.get(key, 0.) + value
        with self.connection:
            for plan in plans:
                summary = _compact(plan)
                checksum = _digest(summary)
                chain = hashlib.sha256((chain + checksum).encode('ascii')).hexdigest()
                self.connection.execute('INSERT INTO scores VALUES (?,?,?,?,?,?,?,?,?)',
                    (job, count, summary['ordinal'], summary['canonical'], summary['credits'],
                     summary['gpa'], summary['failed'], summary['risk'], checksum))
                count += 1
            top = sorted([*top, *plans], key=ranking_key)[:3]
            self.connection.execute('INSERT OR REPLACE INTO checkpoints VALUES (?,?,?,?,?,?)',
                (job, count, chain, json.dumps(_json_safe(top), ensure_ascii=False, allow_nan=False), json.dumps(total_time), _digest(top)))

    def verify(self, job, *, exhaustive=False):
        count, expected_chain, top, _ = self._checkpoint(job)
        chain, checked = '', 0
        for sequence, ordinal, canonical, credits, gpa, failed, risk, checksum in self.connection.execute(
                'SELECT sequence,ordinal,canonical,credits,gpa,failed,risk,checksum FROM scores WHERE job=? ORDER BY sequence', (job,)):
            summary = dict(ordinal=ordinal, canonical=canonical, credits=credits, gpa=gpa, failed=failed, risk=risk)
            if sequence != checked or (exhaustive and int(ordinal) != checked):
                raise IntegrityError('Noncontiguous score sequence.')
            if _digest(summary) != checksum:
                raise IntegrityError('Score checksum mismatch.')
            chain = hashlib.sha256((chain + checksum).encode('ascii')).hexdigest()
            checked += 1
        if checked != count or chain != expected_chain:
            raise IntegrityError('Checkpoint count/checksum mismatch.')
        # Verify the expanded top three against their compact durable summaries.
        for plan in top:
            row = self.connection.execute('SELECT checksum FROM scores WHERE job=? AND canonical=?', (job, plan['canonical_id'])).fetchone()
            if row is None or row[0] != _digest(_compact(plan)):
                raise IntegrityError('Top-three checksum mismatch.')
        expected_top = self.connection.execute('''SELECT ordinal,canonical,credits,gpa,failed,risk FROM scores
            WHERE job=? ORDER BY gpa DESC,failed ASC,risk ASC,LENGTH(ordinal) ASC,ordinal ASC LIMIT 3''', (job,)).fetchall()
        retained = [_compact(plan) for plan in top]
        recomputed = [dict(ordinal=r[0],canonical=r[1],credits=r[2],gpa=r[3],failed=r[4],risk=r[5]) for r in expected_top]
        if retained != recomputed:
            raise IntegrityError('Retained top-three is not the actual ranked top-three.')
        return {'unique_scored_count': count, 'sequential_dfs_ordinals': exhaustive,
                'score_chain_sha256': chain, 'transactional_checkpoint': True}

    def summary(self, job, *, expected_count, exhaustive=False):
        proof = self.verify(job, exhaustive=exhaustive)
        count, chain, top, timings = self._checkpoint(job)
        complete = count == expected_count
        proof.update(expected_feasible_count=expected_count, all_feasible_plans_scored=complete if exhaustive else False)
        return {'evaluated_plans': count, 'best_gpa': top[0]['expected_plan_gpa'] if top else None,
                'top_plans': top, 'timings': timings, 'score_fingerprint': chain,
                'completeness_proof': proof,
                'status': ('EXHAUSTIVE_COMPLETE' if complete else 'EXHAUSTIVE_INCOMPLETE') if exhaustive else
                          ('COMPLETE' if complete else 'SEARCH_INCOMPLETE')}

    def contains(self, job, canonical):
        return self.connection.execute('SELECT 1 FROM scores WHERE job=? AND canonical=?', (job, canonical)).fetchone() is not None

    def bind_selection(self, job, ranks):
        """Reject a resume cursor applied to a different selected order."""
        value = _digest(list(ranks))
        key = 'selection:' + job
        prior = self.connection.execute('SELECT value FROM metadata WHERE key=?', (key,)).fetchone()
        if prior and prior[0] != value:
            if self.cursor(job):
                raise IntegrityError('Resume selection fingerprint mismatch.')
            # A deadline may defer discovery entirely. No scored prefix exists
            # yet, so binding its first real selection cannot mix evaluations.
            with self.connection:
                self.connection.execute('DELETE FROM metadata WHERE key=?', (key,))
        for sequence, ordinal in self.connection.execute('SELECT sequence,ordinal FROM scores WHERE job=? ORDER BY sequence', (job,)):
            if sequence >= len(ranks) or int(ordinal) != ranks[sequence]:
                raise IntegrityError('Resume scored prefix differs from selected sequence.')
        with self.connection:
            self.connection.execute('INSERT OR IGNORE INTO metadata VALUES (?,?)', (key, value))


def diversity(plans):
    pairs = []
    for first, second in itertools.combinations(plans[:3], 2):
        a = {str(c['course_id']) for c in first['courses']}
        b = {str(c['course_id']) for c in second['courses']}
        pairs.append({'first': first['canonical_id'], 'second': second['canonical_id'],
                      'jaccard': len(a & b) / len(a | b) if a | b else 1., 'shared_course_count': len(a & b)})
    return {'mean_jaccard': sum(p['jaccard'] for p in pairs) / len(pairs) if pairs else None,
            'mean_shared_courses': sum(p['shared_course_count'] for p in pairs) / len(pairs) if pairs else None,
            'pairs': pairs}


def compare_oracle(search_top, oracle_top, *, oracle_complete, oracle_score_counts=None, discovered_ids=None):
    unavailable = {'oracle_gpa': None, 'gpa_gap': None, 'top3_recall': None,
                   'score_equivalent_top3_recall': None, 'oracle_equivalent_top1': None}
    if not oracle_complete or not oracle_top or not search_top:
        return unavailable
    ids = set(discovered_ids if discovered_ids is not None else [p['canonical_id'] for p in search_top])
    exact = sum(p['canonical_id'] in ids for p in oracle_top) / len(oracle_top)
    # Match tied GPA slots with multiplicity, rather than counting every tie as all top-three slots.
    available = list(oracle_score_counts or [(p['expected_plan_gpa'], 1) for p in search_top])
    scores = list(p['expected_plan_gpa'] for p in oracle_top)
    matched = 0
    for gpa, count in available:
        for _ in range(min(count, len(scores))):
            index = next((i for i, target in enumerate(scores) if math.isclose(gpa, target, abs_tol=1e-10, rel_tol=0)), None)
            if index is not None:
                scores.pop(index)
                matched += 1
    gap = oracle_top[0]['expected_plan_gpa'] - search_top[0]['expected_plan_gpa']
    return {'oracle_gpa': oracle_top[0]['expected_plan_gpa'], 'gpa_gap': gap,
            'top3_recall': exact, 'score_equivalent_top3_recall': matched / len(oracle_top),
            'oracle_equivalent_top1': math.isclose(gap, 0., abs_tol=1e-10, rel_tol=0)}


@dataclass
class BenchmarkContext:
    student: dict
    target_resolution: dict
    base: pd.DataFrame
    space: object
    scorer: object
    assets: dict
    inputs: dict
    issues: list
    utilities: list
    preparation_seconds: float
    heuristic_seconds: float
    summary: dict

    @property
    def fingerprint(self):
        return _digest({'inputs': self.inputs, 'target_resolution': self.target_resolution,
                        'candidates': self.base.to_dict('records'), 'assets': self.assets,
                        'code': code_fingerprints(), 'constraints': 'pilot_approved_eligibility_exact_decimal_v1'})


def prepare_context(student, root, engine, limits, *, manual_target=None, diagnostic_override=False):
    from .credit_target import resolve_credit_target
    from .search_space import ExactPlanSpace
    started = perf_counter()
    inputs = load_student_inputs(student, root=root, snapshot_id=AFTER)
    resolution = resolve_credit_target(inputs, manual_target, diagnostic_override=diagnostic_override)
    if resolution['status'] != 'RESOLVED':
        raise PilotInputError(resolution.get('reason') or 'API_TARGET_UNRESOLVED')
    snapshot, issues = build_snapshot(inputs)
    # A new attested constraint contract must be implemented rather than silently ignored.
    if inputs.get('integration_context', {}).get('registration_policy'):
        raise PilotInputError('BENCHMARK_CONFIRMED_POLICY_REQUIRES_CONSTRAINT_SPACE_ADAPTER')
    if engine._catalog is None:
        engine._catalog = pd.read_parquet(paths.CLEAN_DEGREE_COURSE_PATH_V2)
    candidates, rules, course_issues, rejected = _candidates(inputs, engine._catalog)
    base = candidates.copy()
    for key, value in snapshot.items():
        base[key] = value
    base['part_semester'] = TARGET_PART % 10
    space = ExactPlanSpace(candidates, resolution['target_credits'], max_states=limits.max_space_states)
    assets = engine.inspect_experiments()
    heuristic_started = perf_counter()
    # University history is strictly prior, already verified by the B/C bundle loader.
    # No B/C model is called to guide search; no plan-invariant prediction is assumed.
    if engine._experimental is not None and hasattr(engine._experimental, '_load'):
        history = engine._experimental._load()['history'].apply(base)
        utility = pd.to_numeric(history['course_history_avg_mark'], errors='coerce')
        # Missing guide values have neutral zero utility only in candidate discovery.
        utilities = utility.fillna(0.).tolist()
    else:
        utilities = [0.] * len(base)
    heuristic_seconds = perf_counter() - heuristic_started
    return BenchmarkContext(student, resolution, base, space, engine._experimental, assets,
        inputs['fingerprints'], list(dict.fromkeys([*POLICY_ISSUES, *issues, *course_issues])), utilities,
        perf_counter() - started, heuristic_seconds, student_summary(snapshot, student))


def _safe_run_name(value):
    if not isinstance(value, str) or not re.fullmatch(r'benchmark_[A-Za-z0-9_]+', value):
        raise ValueError('Invalid benchmark run identifier.')
    return value


class SearchBenchmarkService:
    """Single offline worker, independently persisted from the normal Pilot jobs."""
    def __init__(self, root=PILOT_ROOT, *, context_factory=None):
        self.root = Path(root).resolve()
        self.output = self.root / 'experiments' / AFTER / 'search_benchmark'
        self.context_factory = context_factory
        self.engine = None
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='search-benchmark')
        self.jobs, self.futures, self.lock = {}, {}, RLock()

    def cohort(self):
        return read_students(self.root)

    def _context(self, student, limits, manual_target=None, diagnostic_override=False):
        if self.context_factory:
            return self.context_factory(student, limits, manual_target, diagnostic_override)
        if self.engine is None:
            self.engine = PilotEngine(root=self.root, snapshot_id=AFTER)
        return prepare_context(student, self.root, self.engine, limits, manual_target=manual_target,
                               diagnostic_override=diagnostic_override)

    def inspect(self, sample_ids):
        from .credit_target import resolve_credit_target
        from .search_space import ExactPlanSpace
        students = {s['sample_id']: s for s in self.cohort()}
        records = []
        for sample in sample_ids:
            row = {'sample_id': sample, 'status': 'BLOCKED', 'reason': None}
            try:
                student = students[sample]
                inputs = load_student_inputs(student, self.root, snapshot_id=AFTER)
                resolution = resolve_credit_target(inputs)
                row['target_resolution'] = resolution
                if resolution['status'] != 'RESOLVED':
                    row['reason'] = resolution['reason']
                else:
                    if inputs.get('integration_context', {}).get('registration_policy'):
                        raise PilotInputError('BENCHMARK_CONFIRMED_POLICY_REQUIRES_CONSTRAINT_SPACE_ADAPTER')
                    snapshot, issues = build_snapshot(inputs)
                    if self.engine is None:
                        self.engine = PilotEngine(root=self.root, snapshot_id=AFTER)
                    if self.engine._catalog is None:
                        self.engine._catalog = pd.read_parquet(paths.CLEAN_DEGREE_COURSE_PATH_V2)
                    candidates, _, course_issues, _ = _candidates(inputs, self.engine._catalog)
                    space = ExactPlanSpace(candidates, resolution['target_credits'])
                    row.update(status='READY' if space.count else 'NO_MATCHING_PLAN', candidate_count=len(candidates),
                        feasible_plan_count=space.count, previous_gpa=snapshot['start_agpa_points'],
                        input_fingerprints=inputs['fingerprints'], count_states=space.states,
                        issues=[*POLICY_ISSUES, *issues, *course_issues])
            except (ValueError, KeyError, OSError, RuntimeError) as error:
                row['reason'] = getattr(error, 'code', type(error).__name__)
            records.append(row)
        return records

    def start(self, sample_ids, *, models=('B', 'C'), strategies=STRATEGIES, budgets=BUDGETS,
              scopes=('FIXED_POOL', 'FULL_SPACE'), seed=42, manual_target=None, diagnostic_override=False,
              limits=None, resume_run_id=None):
        resource_limits = limits if isinstance(limits, ResourceLimits) else ResourceLimits(**(limits or {}))
        if resume_run_id:
            directory = self.output / _safe_run_name(resume_run_id)
            manifest = json.loads((directory / 'run_manifest.json').read_text(encoding='utf-8'))
            config = manifest['configuration']
            if manifest['snapshot_id'] != AFTER:
                raise IntegrityError('Only the After snapshot can run.')
            sample_ids = config['sample_ids']
            models, strategies, budgets, scopes = [config[key] for key in ('models', 'strategies', 'budgets', 'scopes')]
            seed, manual_target, diagnostic_override = [config[key] for key in ('seed', 'manual_target', 'diagnostic_override')]
        else:
            manifest = None
        if list(scopes) == ['EXHAUSTIVE']:
            strategies = strategies or STRATEGIES
            budgets = budgets or BUDGETS
        validate_configuration(models, strategies, budgets, scopes)
        if not isinstance(seed, int) or isinstance(seed, bool):
            raise ValueError('An integer random seed is required.')
        students = {s['sample_id']: s for s in self.cohort()}
        if (not isinstance(sample_ids, list) or not sample_ids or len(set(sample_ids)) != len(sample_ids)
                or any(s not in students for s in sample_ids)):
            raise ValueError('Choose distinct saved primary students.')
        if 'EXHAUSTIVE' in scopes and len(sample_ids) > 5:
            raise ValueError('Select at most five students for an explicit exhaustive benchmark.')
        configuration = dict(sample_ids=sample_ids, models=list(models), strategies=list(strategies), budgets=list(budgets),
            scopes=list(scopes), seed=seed, manual_target=manual_target, diagnostic_override=diagnostic_override)
        with self.lock:
            if any(j['status'] == 'running' for j in self.jobs.values()):
                raise ValueError('A search benchmark is already running.')
            run_id = resume_run_id or 'benchmark_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S') + '_' + uuid4().hex[:8]
            self.output.mkdir(parents=True, exist_ok=True)
            directory = self.output / run_id
            if not resume_run_id:
                directory.mkdir(exist_ok=False)
                manifest = {'format_version': FORMAT_VERSION, 'run_id': run_id, 'created_at': datetime.now(timezone.utc).isoformat(),
                    'snapshot_id': AFTER, 'configuration': configuration, 'status': 'running', 'limits': asdict(resource_limits),
                    'code_sha256': code_fingerprints(), 'actual_course_injection': False,
                    'guidance_model': 'NONE', 'heuristic': 'strictly_prior_university_history_avg_mark_credit_weighted',
                    'ranking': 'semester_gpa_desc_failed_credits_asc_max_risk_asc_global_DFS_ordinal',
                    'timing_limitation': TIMING_LIMITATION,
                    'scope_limitation': 'FIXED_POOL measures selection inside first up to 2000; FULL_SPACE independently discovers candidates.',
                    'registration_validity': 'PROVISIONAL: only currently enforceable Pilot constraints; unconfirmed policies remain flagged'}
                atomic_json(directory / 'run_manifest.json', manifest)
            elif manifest['code_sha256'] != code_fingerprints():
                raise IntegrityError('Resume code fingerprint mismatch.')
            if resume_run_id:
                # Verify the prior snapshot before unsealing it. A resume mutates
                # context, scores and exports; its old hashes cannot certify live
                # files. A persisted running state also makes a crashed worker
                # explicitly resumable instead of advertising prior completion.
                self.load_run(run_id)
                (directory / 'integrity.json').unlink(missing_ok=True)
                manifest['status'] = 'running'
                atomic_json(directory / 'run_manifest.json', manifest)
            self.jobs[run_id] = {'run_id': run_id, 'status': 'running', 'completed': 0, 'total': len(sample_ids)}
            self.futures[run_id] = self.executor.submit(self._execute, directory, manifest,
                [students[s] for s in sample_ids], resource_limits)
            # Bound process metadata without removing any persisted runs.
            for old in list(self.jobs)[:-32]:
                if self.jobs[old]['status'] != 'running':
                    self.jobs.pop(old, None)
                    self.futures.pop(old, None)
        return run_id

    def run_sync(self, sample_ids, **kwargs):
        run_id = self.start(sample_ids, **kwargs)
        self.futures[run_id].result()
        return self.load_run(run_id)

    def progress(self, run_id):
        with self.lock:
            if run_id in self.jobs:
                return json.loads(json.dumps(self.jobs[run_id]))
        saved = self.load_run(run_id)
        return {'run_id': run_id, 'status': saved['run_manifest']['status'],
                'completed': len(saved['student_results']), 'total': len(saved['run_manifest']['configuration']['sample_ids'])}

    def list_runs(self):
        rows = []
        for path in self.output.glob('benchmark_*/run_manifest.json'):
            try:
                value = json.loads(path.read_text(encoding='utf-8'))
                row = {k: value.get(k) for k in ('run_id', 'status', 'created_at')}
                if row['status'] == 'running' and self.jobs.get(row['run_id'], {}).get('status') != 'running':
                    row['status'] = 'EXHAUSTIVE_INCOMPLETE'
                rows.append(row)
            except (OSError, ValueError):
                continue
        return sorted(rows, key=lambda r: r.get('created_at') or '', reverse=True)

    def load_run(self, run_id):
        directory = self.output / _safe_run_name(run_id)
        manifest = json.loads((directory / 'run_manifest.json').read_text(encoding='utf-8'))
        results = json.loads((directory / 'student_results.json').read_text(encoding='utf-8')) if (directory / 'student_results.json').exists() else []
        # Immutable completed exports carry file hashes; reading never constructs a scorer.
        integrity_path = directory / 'integrity.json'
        if integrity_path.exists():
            for filename, expected in json.loads(integrity_path.read_text(encoding='utf-8')).get('sha256', {}).items():
                if sha256(directory / filename) != expected:
                    raise IntegrityError('Saved result hash mismatch: ' + filename)
        if manifest['status'] == 'running' and self.jobs.get(run_id, {}).get('status') != 'running':
            manifest = {**manifest, 'status': 'EXHAUSTIVE_INCOMPLETE', 'reason': 'WORKER_INTERRUPTED_RESUME_REQUIRED'}
        return {'run_manifest': manifest, 'student_results': results, 'storage_path': str(directory)}

    @staticmethod
    def _seal(directory, results):
        atomic_json(directory / 'integrity.json', {'status': 'PASS', 'sha256': {
            p.relative_to(directory).as_posix(): sha256(p) for p in directory.rglob('*')
            if p.is_file() and p.suffix in ('.json', '.csv', '.sqlite') and p.name != 'integrity.json'},
            'oracle_completeness': {r['sample_id']: {e['model']: e['completeness_proof'] for e in r['experiments']
                if e['scope'] == 'EXHAUSTIVE'} for r in results}})

    def _guard(self, directory, limits, started):
        if perf_counter() - started >= limits.max_seconds:
            return 'RUNTIME_LIMIT'
        if sum(p.stat().st_size for p in directory.rglob('*') if p.is_file()) > limits.max_disk_mb * 1024**2:
            return 'DISK_LIMIT'
        usage = memory_mb()
        if usage is not None and usage > limits.max_memory_mb:
            return 'MEMORY_LIMIT'
        return None

    def _execute(self, directory, manifest, students, limits):
        started = perf_counter()
        config = manifest['configuration']
        results = []
        run_id = manifest['run_id']
        try:
            manifest.update(manifest_context(self.root, AFTER, students))
            for student in students:
                sample = student['sample_id']
                with self.lock:
                    self.jobs[run_id].update(current_sample=sample)
                try:
                    guard_reason = self._guard(directory, limits, started)
                    if guard_reason:
                        raise RuntimeError(guard_reason)
                    context = self._context(student, limits, config['manual_target'], config['diagnostic_override'])
                    result = self._evaluate_context(directory, context, config, limits, started, run_id)
                except (ValueError, OSError, KeyError, TypeError, RuntimeError) as error:
                    result = {'sample_id': sample, 'status': 'BLOCKED', 'reason': getattr(error, 'code', str(error)), 'experiments': []}
                results.append(result)
                atomic_json(directory / 'student_results.json', results)
                with self.lock:
                    self.jobs[run_id].update(completed=len(results))
            manifest.update(status='completed' if all(r['status'] == 'COMPLETE' for r in results) else 'partial',
                student_inputs={r['sample_id']: r.get('input_fingerprints') for r in results},
                credit_targets={r['sample_id']: r.get('target_resolution') for r in results},
                model_artifacts={r['sample_id']: r.get('model_assets') for r in results},
                feasible_space_sizes={r['sample_id']: r.get('feasible_plan_count') for r in results},
                limits=asdict(limits), elapsed_seconds=perf_counter() - started, peak_process_memory_mb=memory_mb())
            export_started = perf_counter()
            self._export(directory, results)
            manifest['final_export_seconds'] = perf_counter() - export_started
            manifest['total_wall_seconds'] = perf_counter() - started
            manifest.setdefault('attempts', []).append({'finished_at': datetime.now(timezone.utc).isoformat(),
                'wall_seconds': manifest['total_wall_seconds'], 'limits': asdict(limits), 'status': manifest['status']})
            manifest['cumulative_attempt_wall_seconds'] = sum(a['wall_seconds'] for a in manifest['attempts'])
            atomic_json(directory / 'run_manifest.json', manifest)
            self._seal(directory, results)
            with self.lock:
                self.jobs[run_id].update(status=manifest['status'], total_wall_seconds=manifest['total_wall_seconds'])
        except Exception as error:
            manifest.update(status='failed', error=type(error).__name__ + ': ' + str(error), elapsed_seconds=perf_counter() - started)
            atomic_json(directory / 'run_manifest.json', manifest)
            self._seal(directory, results)
            with self.lock:
                self.jobs[run_id].update(status='failed', reason=manifest['error'])

    def _evaluate_context(self, directory, context, config, limits, started, run_id):
        sample = context.student['sample_id']
        sample_dir = directory / sample
        sample_dir.mkdir(exist_ok=True)
        fingerprint = context.fingerprint
        context_file = sample_dir / 'context.json'
        metadata = {'fingerprint': fingerprint, 'sample_id': sample, 'target_resolution': context.target_resolution,
            'candidate_order': context.space.candidate_ids, 'candidate_sha256': _digest(context.base.to_dict('records')),
            'feasible_plan_count': context.space.count, 'input_fingerprints': context.inputs,
            'model_assets': context.assets, 'student_summary': context.summary, 'issues': context.issues}
        previous_metadata = json.loads(context_file.read_text(encoding='utf-8')) if context_file.exists() else None
        if previous_metadata and previous_metadata['fingerprint'] != fingerprint:
            raise IntegrityError('Resume source/model/target fingerprint mismatch.')
        preparation_attempts = list((previous_metadata or {}).get('preparation_attempts', []))
        preparation_attempts.append({'preparation_seconds': context.preparation_seconds,
                                     'heuristic_seconds': context.heuristic_seconds})
        cumulative_preparation = sum(a['preparation_seconds'] for a in preparation_attempts)
        metadata.update(preparation_attempts=preparation_attempts, cumulative_preparation_seconds=cumulative_preparation)
        atomic_json(context_file, metadata)
        pool = list(range(min(2000, context.space.count)))
        pool_value = [{'dfs_ordinal': rank, 'canonical_id': context.space.canonical_id(context.space.unrank(rank))} for rank in pool]
        atomic_json(sample_dir / 'reference_pool.json', {'plans': pool_value, 'fingerprint': _digest(pool_value),
            'scope': 'first_up_to_2000_include_first_DFS', 'eligible_count': len(pool)})
        row = {**metadata, 'status': 'COMPLETE', 'experiments': [],
               'preparation_seconds': context.preparation_seconds, 'heuristic_preparation_seconds': context.heuristic_seconds,
               'heuristic_model_inference_count': 0, 'peak_process_memory_mb': memory_mb()}
        ledger = ScoreLedger(sample_dir / 'scores.sqlite', fingerprint)
        try:
            for scope in config['scopes']:
                variants = [('EXHAUSTIVE', None)] if scope == 'EXHAUSTIVE' else list(itertools.product(config['strategies'], config['budgets']))
                for strategy, budget in variants:
                    search_started = perf_counter()
                    selection = None
                    selection_path = sample_dir / f'{scope}_{strategy}_{budget}.json'
                    deferred_reason = self._guard(directory, limits, started)
                    if scope != 'EXHAUSTIVE':
                        if selection_path.exists():
                            from .search_space import Selection
                            saved = json.loads(selection_path.read_text(encoding='utf-8'))
                            selected_ranks = saved['ranks']
                            selected_plans = [context.space.unrank(rank) for rank in selected_ranks]
                            ids = [context.space.canonical_id(plan) for plan in selected_plans]
                            if ids != saved['canonical_ids'] or _digest(sorted(ids)) != saved['selected_set_fingerprint']:
                                raise IntegrityError('Persisted selection identity mismatch.')
                            selection = Selection(plans=selected_plans, ranks=selected_ranks, **saved['selection_statistics'])
                        elif deferred_reason:
                            from .search_space import Selection
                            selection = Selection([], [], 0, True, False, 0, deferred_reason, True,
                                len(pool) if scope == 'FIXED_POOL' else context.space.count, 0., 0.)
                        else:
                            selection = context.space.select(strategy, budget, seed=config['seed'],
                                pool=pool if scope == 'FIXED_POOL' else None, utilities=context.utilities,
                                max_states=limits.max_space_states)
                        ranks = selection.ranks
                    else:
                        ranks = range(context.space.count)
                    search_seconds = perf_counter() - search_started
                    if selection is not None and not selection_path.exists() and not deferred_reason:
                        atomic_json(selection_path, {'ranks': ranks, 'canonical_ids': [context.space.canonical_id(p) for p in selection.plans],
                            'selected_set_fingerprint': _digest(sorted(context.space.canonical_id(p) for p in selection.plans)),
                            'scope': scope, 'seed': config['seed'], 'strategy': strategy, 'budget': budget,
                            'visited_states': selection.visited_states, 'reason': selection.reason,
                            'selection_statistics': {k:v for k,v in asdict(selection).items() if k not in ('plans','ranks')}})
                    for model in config['models']:
                        job = f'{scope}/{strategy}/{budget}/{model}'
                        job_started = perf_counter()
                        reason = None
                        ledger.verify(job, exhaustive=scope == 'EXHAUSTIVE')
                        if scope != 'EXHAUSTIVE':
                            ledger.bind_selection(job, ranks)
                        selected_count = context.space.count if scope == 'EXHAUSTIVE' else len(ranks)
                        cap = min(selected_count, limits.max_oracle_plans) if scope == 'EXHAUSTIVE' else selected_count
                        if context.assets.get(model, {}).get('status') != 'READY':
                            reason = context.assets.get(model, {}).get('reason', 'MODEL_UNAVAILABLE')
                        else:
                            while ledger.cursor(job) < cap:
                                reason = self._guard(directory, limits, started)
                                if reason:
                                    break
                                cursor = ledger.cursor(job)
                                chunk_ranks = list(ranks[cursor:min(cursor + limits.chunk_size, cap)])
                                plans = [context.space.unrank(rank) for rank in chunk_ranks]
                                # Every strategy uses the very same counted exact-credit space.
                                if any(context.space.rank(plan) != rank for rank, plan in zip(chunk_ranks, plans)):
                                    raise IntegrityError('Selected plan rank mismatch.')
                                detailed, timings = score_chunk(context.base, plans, chunk_ranks, context.scorer, model)
                                persistence_started = perf_counter()
                                ledger.commit(job, detailed, timings)
                                atomic_json(sample_dir / 'checkpoint_status.json', {'scope': scope, 'strategy': strategy, 'model': model,
                                    'status': 'EXHAUSTIVE_INCOMPLETE' if scope == 'EXHAUSTIVE' else 'SEARCH_INCOMPLETE',
                                    'evaluated_plans': ledger.cursor(job), 'feasible_plan_count': context.space.count,
                                    'fingerprint': fingerprint, 'global_optimum_guaranteed': False})
                                # Persistence time is stored independently of scorer timers.
                                with self.lock:
                                    self.jobs[run_id].update(details={'scope': scope, 'strategy': strategy, 'budget': budget,
                                        'model': model, 'evaluated_plans': ledger.cursor(job), 'feasible_plan_count': context.space.count})
                                ledger.commit(job, [], {'persistence_seconds': perf_counter() - persistence_started})
                        if scope == 'EXHAUSTIVE' and cap < selected_count and ledger.cursor(job) >= cap:
                            reason = 'ORACLE_PLAN_RESOURCE_LIMIT'
                        attempt_wall = perf_counter() - job_started + search_seconds
                        ledger.commit(job, [], {'job_wall_seconds': attempt_wall})
                        result = ledger.summary(job, expected_count=selected_count, exhaustive=scope == 'EXHAUSTIVE')
                        if reason and ledger.cursor(job) < selected_count:
                            result['reason'] = reason
                        if context.space.count == 0:
                            result['status'] = 'NO_MATCHING_PLAN'
                            result['reason'] = 'NO_EXACT_CREDIT_SUBSET'
                        if selection is not None and len(ranks) < min(budget, len(pool) if scope == 'FIXED_POOL' else context.space.count):
                            result.update(status='SEARCH_INCOMPLETE', reason=selection.reason)
                        discovered_count = result['evaluated_plans'] if scope == 'EXHAUSTIVE' else len(ranks)
                        result.update(sample_id=sample, model=model, scope=scope, strategy=strategy, budget=budget,
                            target_credits=context.target_resolution['target_credits'],
                            target_credits_source=context.target_resolution['target_credits_source'],
                            feasible_plan_count=context.space.count, scope_plan_count=len(pool) if scope == 'FIXED_POOL' else context.space.count,
                            unique_plans_discovered=discovered_count, evaluated_plan_model_calls=result['evaluated_plans'],
                            heuristic_model_calls=0, shared_plan_set_across_models=True, model_guidance='NONE',
                            visited_search_states=selection.visited_states if selection is not None else
                                context.space.states + result['evaluated_plans'] * (len(context.space.candidate_ids) + 1),
                            count_preparation_states=context.space.states,
                            candidate_exploration_coverage=(discovered_count/context.space.count if context.space.count else None),
                            search_truncated=discovered_count < context.space.count or result['evaluated_plans'] < context.space.count,
                            budget_shortfall=budget is not None and len(ranks) < budget,
                            search_preselection_seconds=search_seconds,
                            heuristic_bound_preparation_seconds=selection.heuristic_preparation_seconds if selection is not None else 0.,
                            selection_only_seconds=selection.selection_seconds if selection is not None else 0.,
                            shared_preparation_seconds=cumulative_preparation,
                            latest_attempt_preparation_seconds=context.preparation_seconds,
                            shared_heuristic_seconds=context.heuristic_seconds,
                            runtime_seconds=result['timings'].get('job_wall_seconds', attempt_wall),
                            current_attempt_wall_seconds=attempt_wall,
                            standalone_runtime_seconds=result['timings'].get('job_wall_seconds', attempt_wall) + cumulative_preparation,
                            peak_process_memory_mb=memory_mb(),
                            runtime_scope='job scoring/persistence plus shared selection; shared context preparation reported separately',
                            diversity=diversity(result['top_plans']), academic_validity='ENFORCEABLE_PILOT_CONSTRAINTS_ONLY',
                            unconfirmed_policies=context.issues, oracle_gpa=None, gpa_gap=None, top3_recall=None,
                            oracle_equivalent_top1=None, score_equivalent_top3_recall=None, _job=job)
                        row['experiments'].append(result)
                        if result['status'] in ('EXHAUSTIVE_INCOMPLETE', 'SEARCH_INCOMPLETE'):
                            row['status'] = 'PARTIAL'
                        atomic_json(sample_dir / 'results.json', row)
            # Oracle comparisons occur after all independent selection and scoring have finished.
            for model in config['models']:
                oracle = next((e for e in row['experiments'] if e['scope'] == 'EXHAUSTIVE' and e['model'] == model), None)
                if oracle is None:
                    continue
                for experiment in row['experiments']:
                    if experiment['model'] != model:
                        continue
                    discovered = [p['canonical_id'] for p in oracle['top_plans'] if ledger.contains(experiment['_job'], p['canonical_id'])]
                    score_counts = ledger.connection.execute('SELECT gpa,COUNT(*) FROM scores WHERE job=? GROUP BY gpa', (experiment['_job'],)).fetchall()
                    experiment.update(compare_oracle(experiment['top_plans'], oracle['top_plans'],
                        oracle_complete=oracle['status'] == 'EXHAUSTIVE_COMPLETE', discovered_ids=discovered,
                        oracle_score_counts=score_counts), oracle_complete=oracle['status'] == 'EXHAUSTIVE_COMPLETE',
                        oracle_fingerprint=oracle['score_fingerprint'] if oracle['status'] == 'EXHAUSTIVE_COMPLETE' else None)
            for experiment in row['experiments']:
                experiment.pop('_job', None)
            atomic_json(sample_dir / 'results.json', row)
            return row
        finally:
            ledger.close()

    @staticmethod
    def _export(directory, results):
        rows = []
        for student in results:
            for experiment in student.get('experiments', []):
                row = {key: value for key, value in experiment.items() if not isinstance(value, (list, dict))}
                row.update(top3_mean_jaccard=experiment['diversity']['mean_jaccard'],
                           top3_mean_shared_courses=experiment['diversity']['mean_shared_courses'])
                for position, plan in enumerate(experiment['top_plans'], 1):
                    row[f'top{position}_canonical_id'] = plan['canonical_id']
                    row[f'top{position}_dfs_ordinal'] = plan['plan_id']
                    row[f'top{position}_expected_gpa'] = plan['expected_plan_gpa']
                rows.append(row)
        columns = list(dict.fromkeys(key for row in rows for key in row)) or ['sample_id', 'status']
        with (directory / 'search_comparison.csv').open('w', encoding='utf-8-sig', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=columns)
            writer.writeheader()
            writer.writerows(rows)
        atomic_json(directory / 'oracle_summaries.json', [{'sample_id': s['sample_id'], **e} for s in results
            for e in s.get('experiments', []) if e['scope'] == 'EXHAUSTIVE'])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=PILOT_ROOT)
    parser.add_argument('--inspect', action='store_true')
    parser.add_argument('--sample', action='append', default=[])
    parser.add_argument('--models', nargs='+', default=['B', 'C'])
    parser.add_argument('--strategies', nargs='+', default=list(STRATEGIES))
    parser.add_argument('--budgets', type=int, nargs='+', default=list(BUDGETS))
    parser.add_argument('--scopes', nargs='+', default=['FIXED_POOL', 'FULL_SPACE'])
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--max-seconds', type=float, default=300.)
    parser.add_argument('--max-oracle-plans', type=int, default=50000)
    parser.add_argument('--chunk-size', type=int, default=128)
    parser.add_argument('--resume')
    args = parser.parse_args(argv)
    service = SearchBenchmarkService(args.root)
    try:
        samples = args.sample or ([s['sample_id'] for s in service.cohort()] if args.inspect else [])
        if args.inspect:
            print(json.dumps(service.inspect(samples), indent=2))
        else:
            run_id = service.start(samples, models=args.models, strategies=args.strategies, budgets=args.budgets,
                scopes=args.scopes, seed=args.seed, resume_run_id=args.resume,
                limits=ResourceLimits(max_seconds=args.max_seconds, max_oracle_plans=args.max_oracle_plans, chunk_size=args.chunk_size))
            print('RUN_ID=' + run_id, flush=True)
            service.futures[run_id].result()
            print(json.dumps(service.progress(run_id), indent=2))
            return 0 if service.progress(run_id)['status'] == 'completed' else 2
    finally:
        service.executor.shutdown(wait=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
