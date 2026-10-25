"""Pure presentation comparisons and privacy-limited CSV exports, without inference."""
import csv
import io
import itertools
import math

from tools.recommendation_pilot_20251.search_benchmark import canonical_plan_id


def numeric(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def _difference(second, first):
    a, b = numeric(second), numeric(first)
    return a - b if a is not None and b is not None else None


def plan_comparison(plans, labels=None):
    """Compare sets and saved scores in supplied rank order; never rerank plans."""
    labels = list(labels or [f'Top {i + 1}' for i in range(len(plans))])
    if len(labels) != len(plans) or len(set(labels)) != len(labels):
        raise ValueError('Supply one distinct label per plan.')
    maps = [{str(c['course_id']): c for c in p.get('courses', p.get('course_rows', []))}
            for p in plans]
    sets = [set(m) for m in maps]
    common = set.intersection(*sets) if sets else set()
    union = set.union(*sets) if sets else set()
    matrix = []
    for key in sorted(union, key=lambda course: (course not in common, course)):
        row = next(m[key] for m in maps if key in m)
        matrix.append({'course_id': key, 'course_name': row.get('course_name'),
            'shared_by_all': key in common, **{label: key in ids for label, ids in zip(labels, sets)}})
    unique = {label: sorted(ids - set.union(*(other for j, other in enumerate(sets) if j != i)))
              if len(sets) > 1 else sorted(ids) for i, (label, ids) in enumerate(zip(labels, sets))}
    pairs, shared = [], []
    for i, j in itertools.combinations(range(len(plans)), 2):
        a, b = sets[i], sets[j]
        delta = _difference(plans[j].get('expected_plan_gpa'), plans[i].get('expected_plan_gpa'))
        pairs.append({'first': labels[i], 'second': labels[j],
            'first_canonical_id': canonical_plan_id(a), 'second_canonical_id': canonical_plan_id(b),
            'jaccard': len(a & b) / len(a | b) if a | b else 1., 'shared_course_count': len(a & b),
            'identical_course_set': a == b, 'identical_gpa': delta is not None and abs(delta) <= 1e-10,
            'gpa_difference_second_minus_first': delta,
            'failed_credits_difference_second_minus_first': _difference(plans[j].get('expected_failed_credits'), plans[i].get('expected_failed_credits')),
            'max_risk_difference_second_minus_first': _difference(
                (plans[j].get('plan_difficulty_balance') or {}).get('max_fail_probability'),
                (plans[i].get('plan_difficulty_balance') or {}).get('max_fail_probability')),
            'first_credits': plans[i].get('total_credits'), 'second_credits': plans[j].get('total_credits'),
            'removed_from_first': ', '.join(sorted(a - b)), 'added_in_second': ', '.join(sorted(b - a))})
        for course in sorted(a & b):
            first, second = maps[i][course], maps[j][course]
            shared.append({'first': labels[i], 'second': labels[j], 'course_id': course,
                'course_name': first.get('course_name'), 'first_predicted_mark': first.get('predicted_mark'),
                'second_predicted_mark': second.get('predicted_mark'),
                'predicted_mark_difference_second_minus_first': _difference(second.get('predicted_mark'), first.get('predicted_mark')),
                'first_fail_probability': first.get('fail_probability'), 'second_fail_probability': second.get('fail_probability')})
    return {'matrix': matrix, 'pairs': pairs, 'shared_predictions': shared,
            'common_ids': sorted(common), 'unique_ids': unique,
            'near_identical': bool(pairs) and all(p['jaccard'] >= .8 for p in pairs)}


EXPORT_FIELDS = set('''sample_id part_id semester snapshot_id source_run run_id historical_run_id benchmark_run_id
family model model_version B_model_version C_model_version strategy budget scope target_credits target_credits_source minimum_credits maximum_credits
status reason recommendation_status prediction_status candidate_count evaluated_plans feasible_plan_count
best_gpa oracle_gpa gpa_gap top3_recall score_equivalent_top3_recall oracle_equivalent_top1
runtime_seconds standalone_runtime_seconds elapsed_seconds mean_jaccard top3_mean_jaccard
metric value student_count course_observations course_count evaluated_students
actual_gpa descriptive_gpa predicted_actual_plan_gpa actual_plan_gpa actual_plan_gpa_error actual_plan_gpa_absolute_error
previous_gpa starting_gpa starting_category actual_course_count actual_registered_credits
mae rmse bias gpa_mae fail_brier fail_roc_auc fail_log_loss fail_count actual_fail_count missing_prediction_count
course_id course_name course_credits actual_mark actual_points course_outcome_status result_status
predicted_mark expected_points expected_grade fail_probability error absolute_error fail_label
B_predicted_mark C_predicted_mark B_error C_error B_fail_probability C_fail_probability
rank plan_id canonical_id total_credits expected_plan_gpa expected_failed_credits max_fail_probability
overlap_count overlap_ids course_ids input_fingerprint model_fingerprint
first second jaccard shared_course_count identical_course_set identical_gpa
gpa_difference_second_minus_first failed_credits_difference_second_minus_first
max_risk_difference_second_minus_first first_credits second_credits removed_from_first added_in_second
'''.split())


def csv_bytes(rows):
    """Whitelist public scalar fields and prevent formula execution in spreadsheets."""
    fields = list(dict.fromkeys(k for row in rows for k in row if k in EXPORT_FIELDS))
    output = io.StringIO(newline='')
    writer = csv.DictWriter(output, fieldnames=fields or ['sample_id'])
    writer.writeheader()
    for row in rows:
        safe = {}
        for key in fields:
            value = row.get(key)
            if isinstance(value, (dict, list, tuple, set)):
                continue
            if isinstance(value, str) and value.lstrip().startswith(('=', '+', '-', '@')):
                value = "'" + value
            if isinstance(value, float) and not math.isfinite(value):
                value = None
            safe[key] = value
        writer.writerow(safe)
    return output.getvalue().encode('utf-8-sig')
