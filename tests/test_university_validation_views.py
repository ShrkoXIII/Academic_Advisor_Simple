"""Read-only comparisons never turn missing values into grades or reorder plans."""
import csv
import io


def plan(ids, gpa=2.5, risk=.2):
    return {'expected_plan_gpa': gpa, 'expected_failed_credits': risk,
        'total_credits': len(ids) * 3,
        'plan_difficulty_balance': {'max_fail_probability': risk},
        'courses': [{'course_id': key, 'course_name': key, 'course_credits': 3,
            'predicted_mark': 60 + i} for i, key in enumerate(ids)]}


def test_matrix_groups_common_courses_and_preserves_rank_order():
    from tools.academic_advisor_streamlit.validation_views import plan_comparison
    plans = [plan('ABC'), plan('ABD'), plan('ABE')]
    result = plan_comparison(plans, ['Top 1', 'Top 2', 'Top 3'])
    assert result['common_ids'] == ['A', 'B']
    assert result['unique_ids'] == {'Top 1': ['C'], 'Top 2': ['D'], 'Top 3': ['E']}
    assert [r['course_id'] for r in result['matrix']] == list('ABCDE')
    assert result['pairs'][0]['jaccard'] == .5
    assert result['pairs'][0]['identical_gpa'] is True
    assert [p['courses'][-1]['course_id'] for p in plans] == list('CDE')


def test_different_predictions_for_identical_course_set_remain_visible():
    from tools.academic_advisor_streamlit.validation_views import plan_comparison
    result = plan_comparison([plan('AB', 2), plan('BA', 3)], ['B', 'C'])
    pair = result['pairs'][0]
    assert pair['identical_course_set'] and pair['jaccard'] == 1
    assert pair['gpa_difference_second_minus_first'] == 1
    assert result['shared_predictions'][0]['predicted_mark_difference_second_minus_first'] == 1
    assert result['near_identical']


def test_missing_scores_stay_missing_and_incomplete_top3_is_supported():
    from tools.academic_advisor_streamlit.validation_views import plan_comparison
    result = plan_comparison([{'courses': [{'course_id': 'A'}]}, {'courses': []}], ['B', 'C'])
    assert result['pairs'][0]['gpa_difference_second_minus_first'] is None
    assert not result['pairs'][0]['identical_gpa']
    assert plan_comparison([])['matrix'] == []


def test_exports_allowlist_public_fields_and_preserve_missing_values():
    from tools.academic_advisor_streamlit.validation_views import csv_bytes
    data = csv_bytes([{'sample_id': 'S01', 'student_id': 'PRIVATE', 'student_name': 'SECRET',
        'course_name': '=EXEC()', 'actual_mark': None, 'B_error': -2, 'source_run': 'saved'}])
    text = data.decode('utf-8-sig')
    assert 'PRIVATE' not in text and 'SECRET' not in text
    row = next(csv.DictReader(io.StringIO(text)))
    assert row['actual_mark'] == '' and row['B_error'] == '-2'
    assert row['course_name'].startswith("'") and row['source_run'] == 'saved'
