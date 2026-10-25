"""Thin offline orchestration and saved-result presentation for Streamlit.

Scoring, ranking and features belong to the existing Pilot engine. Outcomes
enter only the runner's post-score callback. Reading a saved run never scores.
"""
from collections import OrderedDict
from copy import deepcopy
from functools import partial
from pathlib import Path
from threading import RLock

from tools.recommendation_pilot_20251.adapter import (
    PILOT_ROOT, PilotInputError, load_student_inputs, read_students, read_verified_json, sha256,
)
from tools.recommendation_pilot_20251.actual_metrics import (
    _actual_registration, _course_id, _course_map, _credits_equal, _number,
    attach_prediction_metrics, attach_recommendation_metrics,
)
from tools.recommendation_pilot_20251.engine import PilotEngine, build_snapshot, student_summary
from tools.recommendation_pilot_20251.credit_target import resolve_credit_target
from tools.recommendation_pilot_20251.history import EXPECTED_PARTS, build_experimental_university_history
from tools.recommendation_pilot_20251.observed import ObservedPlanStore
from tools.recommendation_pilot_20251.observed_prediction import ObservedPlanPredictor
from tools.recommendation_pilot_20251.runner import ComparisonRunner, RunStore
from tools.recommendation_pilot_20251.snapshots import (
    AFTER, BEFORE, api_data_root, model_versions_root, run_read_roots, run_root, validate_snapshot,
)


class PilotPreflightError(ValueError):
    """Safe per-sample failures that let callers select a valid subset."""

    def __init__(self, blocked):
        self.blocked = blocked
        super().__init__('PILOT_PREFLIGHT_BLOCKED: ' + ', '.join(
            f"{row['sample_id']}:{row['reason']}" for row in blocked))


def _models(manifest, result):
    recorded = manifest.get('selected_models')
    return tuple(recorded) if recorded else tuple(result.get('experiments', {}))


def _actual_summary(observed, forecasts, metrics, selected):
    actual = _actual_registration(observed)
    courses = list((actual or {}).values())
    graded = [c for c in courses if c.get('result_status') == 'AVAILABLE' and
              _number(c.get('actual_mark')) is not None and 0 <= _number(c['actual_mark']) <= 100]
    points = [c for c in graded if _number(c.get('actual_points')) is not None and
              0 <= _number(c['actual_points']) and _number(c.get('course_credits')) is not None and
              _number(c['course_credits']) > 0]
    partial = (sum(_number(c['actual_points']) * _number(c['course_credits']) for c in points) /
               sum(_number(c['course_credits']) for c in points)) if points else None
    complete = bool(courses) and len(points) == len(courses)
    gpa = partial if complete else None
    result = {'actual_course_count': len(courses) if actual else None,
              'graded_course_count': len(graded) if actual else None,
              'total_credits': sum(_number(c['course_credits']) for c in courses) if actual else None,
              'descriptive_gpa': gpa,
              'descriptive_gpa_reason': None if complete else 'COMPLETE_VALID_OUTCOME_POINTS_AND_CREDITS_UNAVAILABLE',
              'partial_graded_gpa': partial if not complete else None,
              'partial_graded_gpa_reason': 'PARTIAL_VALID_GRADED_COURSES_ONLY' if points and not complete else
                  ('NOT_APPLICABLE_COMPLETE_RESULTS' if complete else 'NO_VALID_GRADED_POINTS'),
              'official_gpa': None, 'official_gpa_reason': 'OFFICIAL_SEMESTER_GPA_POLICY_NOT_VERIFIED', 'models': {}}
    for name in selected:
        forecast = forecasts.get(name) or {}
        ready = forecast.get('prediction_status', forecast.get('status')) == 'PREDICTION_AVAILABLE'
        prediction = _number(forecast.get('expected_plan_gpa')) if ready else None
        model_metrics = metrics.get(name) or {}
        forecast_reason = forecast.get('reason') or (None if ready else 'SAVED_ACTUAL_PLAN_PREDICTION_UNAVAILABLE')
        result['models'][name] = {'predicted_actual_plan_gpa': prediction,
            'predicted_actual_plan_gpa_reason': forecast_reason or ('SAVED_ACTUAL_PLAN_GPA_UNAVAILABLE' if prediction is None else None),
            'actual_plan_gpa_error': prediction - gpa if prediction is not None and gpa is not None else None,
            'actual_plan_gpa_absolute_error': abs(prediction - gpa) if prediction is not None and gpa is not None else None,
            **{key: _number(model_metrics.get(key)) if ready else None for key in ('mae', 'rmse', 'bias')},
            'grade_error_course_count': model_metrics.get('course_count') if ready else None,
            'missing_prediction_count': model_metrics.get('missing_prediction_count') if ready else None,
            **{key + '_reason': forecast_reason or 'NO_VALID_SAVED_ACTUAL_PLAN_ERROR_PAIRS'
               for key in ('mae', 'rmse', 'bias') if not ready or _number(model_metrics.get(key)) is None},
            'status': forecast.get('prediction_status', forecast.get('status', 'UNAVAILABLE')),
            'reason': forecast_reason}
    return result


def _valid_actual_mark(course, actual):
    if actual is None:
        return None, 'NO_MATCHING_ACTUAL_COURSE'
    if not _credits_equal(course.get('course_credits'), actual.get('course_credits')):
        return None, 'ACTUAL_COURSE_CREDIT_MISMATCH'
    if (course.get('grade_version_id') is not None and actual.get('grade_version_id') is not None and
            str(course['grade_version_id']) != str(actual['grade_version_id'])):
        return None, 'GRADE_VERSION_MISMATCH'
    mark = _number(actual.get('actual_mark'))
    if actual.get('result_status') != 'AVAILABLE' or mark is None or not 0 <= mark <= 100:
        return None, actual.get('result_status') or 'ACTUAL_MARK_UNAVAILABLE'
    return mark, None


def present_saved_result(saved, sample_id, *, scenario=None):
    """Project persisted scores only; keep missing evidence explicitly unavailable."""
    matches = [r for r in saved.get('student_results', []) if r.get('sample_id') == sample_id]
    if scenario is not None:
        matches = [r for r in matches if (r.get('candidate_mode'), r.get('credit_experiment')) == tuple(scenario)]
    if len(matches) > 1:
        raise ValueError('Select a saved scenario explicitly for this sample.')
    if not matches:
        raise ValueError('Sample not present in saved run.')
    result = matches[0]
    manifest = saved.get('run_manifest') or {}
    selected = _models(manifest, result)
    observed = result.get('observed_plan') or {}
    actual = _actual_registration(observed)
    forecasts = (result.get('observed_plan_prediction') or {}).get('experiments') or {}
    prediction_metrics = result.get('prediction_metrics') or {}
    actual_summary = _actual_summary(observed, forecasts, prediction_metrics, selected)
    plans_by_model, summary_rows, timing_rows = {}, [], []
    search = result.get('search') or {}
    shared_latency = result.get('latency') or {}
    for stage in ('candidate_preparation_seconds', 'plan_generation_seconds', 'shared_plan_context_seconds',
                  'total_request_seconds', 'comparison_wall_seconds'):
        seconds = _number(shared_latency.get(stage))
        timing_rows.append({'model': 'shared', 'stage': stage, 'seconds': seconds,
                            'reason': None if seconds is not None else 'STAGE_NOT_MEASURED_IN_SAVED_RUN',
                            'measurement_scope': 'student including observed-plan enrichment' if stage == 'comparison_wall_seconds'
                                else 'recommendation engine only; overlapping with totals'})
    for name in selected:
        experiment = (result.get('experiments') or {}).get(name) or {}
        plans = experiment.get('analytical_plans')
        if plans is None:
            plans = experiment.get('plans') or []
        prepared = []
        for rank, plan in enumerate(plans[:3], 1):
            course_rows = []
            ids = set()
            for course in plan.get('courses') or []:
                key = _course_id(course.get('course_id'))
                if key is not None:
                    ids.add(key)
                registered = (actual or {}).get(key)
                mark, reason = _valid_actual_mark(course, registered)
                course_rows.append({**deepcopy(course), 'actual_mark': mark, 'actual_mark_reason': reason,
                                    'prediction_context': 'selected_alternative_plan',
                                    'is_actual_course': key in actual if actual else None})
            overlap = len(ids & set(actual)) if actual else None
            prepared.append({**deepcopy(plan), 'rank': rank, 'overlap_count': overlap,
                             'overlap_fraction': overlap / len(actual) if actual else None, 'course_rows': course_rows})
        plans_by_model[name] = prepared
        coverage = experiment.get('recommendation_metrics') or {}
        actual_model = actual_summary['models'][name]
        latency = experiment.get('latency') or {}
        for stage in ('feature_extraction_seconds', 'prediction_seconds', 'ranking_seconds'):
            seconds = _number(latency.get(stage))
            timing_rows.append({'model': name, 'stage': stage, 'seconds': seconds,
                'reason': None if seconds is not None else latency.get(stage + '_reason') or latency.get('reason') or 'STAGE_NOT_MEASURED_IN_SAVED_RUN',
                'provenance': latency.get('provenance', 'SAVED_PILOT_STAGE_MEASUREMENT'),
                'measurement_scope': 'recommendation scorer only; feature time includes non-inference scorer preparation and frame overhead'})
        elapsed = _number(experiment.get('elapsed_seconds'))
        timing_rows.append({'model': name, 'stage': 'elapsed_seconds', 'seconds': elapsed,
                            'reason': None if elapsed is not None else 'MODEL_TOTAL_NOT_MEASURED_IN_SAVED_RUN',
                            'measurement_scope': 'recommendation model only; excludes independent actual-plan prediction'})
        actual_elapsed = _number(forecasts.get(name, {}).get('elapsed_seconds'))
        timing_rows.append({'model': name, 'stage': 'actual_registered_plan_elapsed_seconds', 'seconds': actual_elapsed,
            'reason': None if actual_elapsed is not None else 'ACTUAL_PLAN_TIME_NOT_MEASURED_IN_SAVED_RUN',
            'measurement_scope': 'saved original actual-plan forecast time; reused value if observed forecast is cached'})
        available = experiment.get('prediction_status', experiment.get('status')) == 'PREDICTION_AVAILABLE'
        count = experiment.get('evaluated_plan_count', experiment.get('full_scored_plan_count'))
        if count is None and available:
            count = len(experiment.get('diagnostic_plans') or []) or None
        if not available:
            count = None
        summary_rows.append({'model': name, 'target_credits': result.get('target_credits'),
            'target_credits_source': result.get('target_credits_source'),
            'minimum_credits': result.get('minimum_credits'), 'maximum_credits': result.get('maximum_credits'),
            'candidate_count': result.get('candidate_count'),
            'candidate_count_reason': 'CANDIDATES_NOT_PREPARED_OR_NOT_SAVED',
            'evaluated_plans': count, 'evaluated_plans_reason': None if count is not None else
                'MODEL_SCORED_PLAN_COUNT_UNAVAILABLE',
            'search_truncated': search.get('truncated', search.get('search_truncated')),
            'best_predicted_plan_gpa': _number(plans[0].get('expected_plan_gpa')) if plans else None,
            'top1_actual_overlap': coverage.get('top1_actual_overlap'),
            'top3_union_actual_overlap': coverage.get('top3_union_actual_overlap'),
            'top1_actual_overlap_fraction': coverage.get('top1_actual_overlap_fraction'),
            'top3_union_actual_overlap_fraction': coverage.get('top3_union_actual_overlap_fraction'),
            'top1_actual_overlap_reason': 'VALID_SAVED_OBSERVATIONS_OR_RECOMMENDATIONS_UNAVAILABLE',
            'top3_union_actual_overlap_reason': 'VALID_SAVED_OBSERVATIONS_OR_RECOMMENDATIONS_UNAVAILABLE',
            'predicted_actual_plan_gpa': actual_model['predicted_actual_plan_gpa'],
            'predicted_actual_plan_gpa_reason': actual_model['predicted_actual_plan_gpa_reason'],
            'actual_plan_gpa': actual_summary['descriptive_gpa'],
            'actual_plan_gpa_reason': actual_summary['descriptive_gpa_reason'],
            'actual_plan_gpa_error': actual_model['actual_plan_gpa_error'],
            'actual_plan_gpa_absolute_error': actual_model['actual_plan_gpa_absolute_error'],
            'actual_plan_gpa_error_reason': actual_summary['descriptive_gpa_reason'] or actual_model['reason'],
            'actual_plan_gpa_absolute_error_reason': actual_summary['descriptive_gpa_reason'] or actual_model['reason'],
            'elapsed_seconds': elapsed,
            'total_elapsed_seconds': _number(shared_latency.get('comparison_wall_seconds')),
            'total_elapsed_seconds_reason': 'STUDENT_WALL_TIME_NOT_MEASURED_IN_SAVED_RUN',
            'status': experiment.get('prediction_status', experiment.get('status', 'UNAVAILABLE')),
            'reason': experiment.get('reason') or (None if plans else 'SAVED_RECOMMENDATIONS_UNAVAILABLE')})
    actual_rows = []
    for key, course in (actual or {}).items():
        row = deepcopy(course)
        for name in selected:
            forecast = forecasts.get(name) or {}
            indexed, ambiguous = _course_map(forecast.get('course_predictions') or [])
            prediction = indexed.get(key)
            ready = forecast.get('prediction_status', forecast.get('status')) == 'PREDICTION_AVAILABLE'
            valid = ready and prediction is not None and key not in ambiguous and _credits_equal(
                prediction.get('course_credits'), course.get('course_credits'))
            if valid and course.get('grade_version_id') is not None and prediction.get('grade_version_id') is not None:
                valid = str(course['grade_version_id']) == str(prediction['grade_version_id'])
            for field in ('predicted_mark', 'expected_points', 'fail_probability'):
                row[f'{name}_{field}'] = _number(prediction.get(field)) if valid else None
            errors = {e['course_id']: e for e in (prediction_metrics.get(name) or {}).get('course_errors', [])}
            row[f'{name}_error'] = (errors.get(key) or {}).get('error') if valid else None
            row[f'{name}_reason'] = None if valid else forecast.get('reason', 'SAVED_ACTUAL_PLAN_COURSE_PREDICTION_UNAVAILABLE')
            if not row.get('course_name') and valid:
                row['course_name'] = prediction.get('course_name')
        actual_rows.append(row)
    warnings = list(result.get('warnings') or [])
    if not observed:
        warnings.append('HISTORICAL_OBSERVED_DATA_UNAVAILABLE_NO_RECOMPUTATION')
    warnings.extend(issue.get('code') if isinstance(issue, dict) else str(issue) for issue in result.get('issues', []))
    completion = saved.get('completion') or {}
    wall = _number(completion.get('total_wall_seconds'))
    execution = {'total_wall_seconds': wall, 'total_wall_seconds_reason': None if wall is not None else
                     'RUN_WALL_TIME_NOT_MEASURED_IN_SAVED_RUN',
                 'provenance': completion.get('provenance', 'SAVED_STAGE_TIMINGS_ONLY_NO_TOTAL_INFERENCE'),
                 'result_source': 'saved_run',
                 'observed_prediction_cache_status': result.get('observed_prediction_cache_status', 'UNKNOWN_LEGACY_RUN'),
                 'presentation_load_cache_status': saved.get('presentation_load_cache_status', 'UNKNOWN')}
    return {'sample_id': sample_id, 'snapshot_id': saved.get('snapshot_id') or manifest.get('snapshot_id'),
            'candidate_mode': result.get('candidate_mode', 'original'), 'credit_experiment': result.get('credit_experiment'),
            'search': deepcopy(search), 'execution': execution,
            'student_summary': deepcopy(result.get('student_summary') or {}), 'summary_rows': summary_rows,
            'plans_by_model': plans_by_model, 'actual_course_rows': actual_rows, 'actual_summary': actual_summary,
            'timing_rows': timing_rows, 'warnings': warnings}


class PilotService:
    """Bounded process resource; one sequential runner and engine per snapshot."""

    def __init__(self, root=PILOT_ROOT, *, engine_factory=None, runner_factory=None,
                 observed_store=None, predictor_factory=None, max_cached_runs=8):
        self.root = Path(root)
        self.engine_factory = engine_factory or PilotEngine
        self.runner_factory = runner_factory or ComparisonRunner
        self.predictor_factory = predictor_factory or ObservedPlanPredictor
        self.observed_store = observed_store
        self.max_cached_runs = max(1, int(max_cached_runs))
        self._runners, self._predictors = {}, {}
        self._saved = OrderedDict()
        self._lock = RLock()

    def cohort(self, include_reserve=False):
        return read_students(self.root, include_reserve=include_reserve)

    def preview(self, sample_id, snapshot_id=AFTER):
        snapshot_id = validate_snapshot(snapshot_id)
        students = {s['sample_id']: s for s in self.cohort(include_reserve=True)}
        if sample_id not in students:
            raise ValueError('Unknown saved sample.')
        inputs = load_student_inputs(students[sample_id], self.root, snapshot_id=snapshot_id)
        snapshot, issues = build_snapshot(inputs)
        resolution = resolve_credit_target(inputs)
        return {'sample_id': sample_id, 'snapshot_id': snapshot_id,
                'status': 'READY' if resolution['status'] == 'RESOLVED' else 'BLOCKED', 'reason': resolution['reason'],
                'credit_target_resolution': resolution,
                'student_summary': student_summary(snapshot, students[sample_id]), 'issues': issues}

    def completeness(self, snapshot_id=AFTER, include_reserve=False):
        snapshot_id = validate_snapshot(snapshot_id)
        students = self.cohort(include_reserve=include_reserve)
        directory = api_data_root(self.root, snapshot_id)
        history = build_experimental_university_history(self.root, snapshot_id=snapshot_id)
        history_count, history_issues = history['accepted_file_count'], history['issues']
        records, blocked = [], []
        for student in students:
            row = {'sample_id': student['sample_id'], 'student_saved': False, 'courses_saved': False,
                   'ready': False, 'reason': None, 'field': None}
            expected = {key: student[key] for key in ('student_id', 'degree_id', 'part_id')}
            for kind in ('student', 'courses'):
                try:
                    read_verified_json(directory / 'students' / student['sample_id'] / f'{kind}_response.json', expected=expected)
                    row[kind + '_saved'] = True
                except PilotInputError as error:
                    if row['reason'] is None:
                        row.update(reason=error.code, field=error.field)
            try:
                inputs = load_student_inputs(student, self.root, snapshot_id=snapshot_id)
                build_snapshot(inputs)
                resolution = resolve_credit_target(inputs)
                row['credit_target_resolution'] = resolution
                if not history['usable_for_b_c']:
                    row.update(reason='INCOMPLETE_OR_INVALID_FROZEN_HISTORY', field='frozen_history')
                elif resolution['status'] != 'RESOLVED':
                    row.update(reason=resolution['reason'], field='credit_target')
                else:
                    row['ready'] = True
            except (PilotInputError, ValueError, KeyError) as error:
                row.update(reason=getattr(error, 'code', 'INVALID_SAVED_INPUT'), field=getattr(error, 'field', None))
            if not row['ready']:
                blocked.append({key: row[key] for key in ('sample_id', 'reason', 'field')})
            records.append(row)
        return {'snapshot_id': snapshot_id, 'student_saved': sum(r['student_saved'] for r in records),
                'courses_saved': sum(r['courses_saved'] for r in records), 'history_saved': history_count,
                'history_total': len(EXPECTED_PARTS), 'primary_count': sum(s['role'] == 'primary' for s in students),
                'ready_sample_ids': [r['sample_id'] for r in records if r['ready']], 'blocked': blocked,
                'records': records, 'history_issues': history_issues, 'history_status': history['status'],
                'history_usable_for_b_c': history['usable_for_b_c']}

    def _runner(self, snapshot_id):
        with self._lock:
            if snapshot_id not in self._runners:
                self._runners[snapshot_id] = self.runner_factory(self.root, snapshot_id=snapshot_id,
                    engine_factory=partial(self.engine_factory, snapshot_id=snapshot_id),
                    result_enricher=self._enrich, reuse_engine=True, max_retained_jobs=64)
            return self._runners[snapshot_id]

    def _enrich(self, result, student, engine, selected_models):
        snapshot_id = getattr(engine, 'snapshot_id', AFTER)
        with self._lock:
            if self.observed_store is None:
                self.observed_store = ObservedPlanStore()
            observed = self.observed_store.get(student)
            key = (snapshot_id, id(engine))
            if key not in self._predictors:
                self._predictors.clear()  # one reused active engine per snapshot
                self._predictors[key] = self.predictor_factory(root=self.root, engine=engine, snapshot_id=snapshot_id)
            predictor = self._predictors[key]
        registrations = [{'course_id': c['course_id'], 'course_credits': c['course_credits']}
                         for c in observed.get('courses', [])] if _actual_registration(observed) else []
        prediction = predictor.predict(student, registrations, models=selected_models)
        result['observed_plan'], result['observed_plan_prediction'] = observed, prediction
        result['observed_prediction_cache_status'] = getattr(predictor, 'last_cache_status', 'UNKNOWN')
        attach_recommendation_metrics(result, models=selected_models)
        return attach_prediction_metrics(result, models=selected_models)

    def start(self, sample_ids, models=('B', 'C'), snapshot_id=AFTER, target_credits=None, max_plans=200,
              include_reserve=False, *, diagnostic_override=False):
        snapshot_id = validate_snapshot(snapshot_id)
        if snapshot_id != AFTER:
            raise ValueError('The before_backend_fix snapshot is read-only.')
        if target_credits is not None and not diagnostic_override:
            raise ValueError('A manual target requires the separate diagnostic override.')
        from tools.recommendation_pilot_20251.selection import normalize_models
        selected = normalize_models(models)
        if not isinstance(sample_ids, list) or not sample_ids or len(set(sample_ids)) != len(sample_ids):
            raise ValueError('Select distinct saved sample identifiers.')
        complete = self.completeness(snapshot_id, include_reserve=include_reserve)
        known = {r['sample_id'] for r in complete['records']}
        if any(sample not in known for sample in sample_ids):
            raise ValueError('Unknown saved sample.')
        blocked = [r for r in complete['blocked'] if r['sample_id'] in sample_ids and
                   not (diagnostic_override and target_credits is not None and r.get('field') == 'credit_target')]
        if blocked:
            raise PilotPreflightError(blocked)
        students = {s['sample_id']: s for s in self.cohort(include_reserve=include_reserve)}
        for sample in sample_ids:
            inputs = load_student_inputs(students[sample], self.root, snapshot_id=snapshot_id)
            resolution = resolve_credit_target(inputs, target_credits, diagnostic_override=diagnostic_override)
            if resolution['status'] != 'RESOLVED':
                blocked.append({'sample_id': sample, 'reason': resolution['reason'], 'field': 'credit_target'})
        if blocked:
            raise PilotPreflightError(blocked)
        return self._runner(snapshot_id).start(sample_ids, models=selected, target_credits=target_credits,
                                                max_plans=max_plans, include_reserve=include_reserve)

    def _store(self, family):
        # The read-only root avoids creating archive directories while browsing.
        return RunStore(run_root(self.root, BEFORE, family), snapshot_id=BEFORE,
                        read_roots=run_read_roots(self.root, family), model_root=model_versions_root(self.root))

    def progress(self, run_id):
        with self._lock:
            for runner in self._runners.values():
                if run_id in runner.jobs:
                    return runner.progress(run_id)
        saved = self.load_run(run_id)
        count = len(saved.get('student_results', []))
        return {'run_id': run_id, 'status': saved['run_manifest'].get('status', 'completed'),
                'error': saved['run_manifest'].get('error'),
                'completed': count, 'total': count, 'total_wall_seconds': (saved.get('completion') or {}).get('total_wall_seconds'),
                'sample_statuses': [{'sample_id': r['sample_id'], 'status': r.get('status', 'completed')}
                                    for r in saved.get('student_results', [])]}

    def list_runs(self):
        rows = [{**row, 'family': family} for family in ('comparison', 'actual_candidate_injection')
                for row in self._store(family).list_runs()]
        return sorted(rows, key=lambda row: row.get('created_at') or '', reverse=True)

    def load_run(self, run_id, family='comparison'):
        registry = model_versions_root(self.root) / 'retired_bundles.json'
        key = (family, run_id, sha256(registry) if registry.is_file() else None)
        with self._lock:
            cached = key in self._saved
            if key not in self._saved:
                self._saved[key] = {**self._store(family).load_compact(run_id), 'family': family}
                while len(self._saved) > self.max_cached_runs:
                    self._saved.popitem(last=False)
            self._saved.move_to_end(key)
            return {**deepcopy(self._saved[key]), 'presentation_load_cache_status': 'CACHED' if cached else 'FRESH'}

    def presentation(self, saved_run, sample_id, *, scenario=None):
        return present_saved_result(saved_run, sample_id, scenario=scenario)
