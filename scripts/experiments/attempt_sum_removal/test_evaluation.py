"""Behavioral checks for isolated observed-plan evaluation and uncertainty."""
import numpy as np
import pandas as pd
import pytest

from scripts.experiments.attempt_sum_removal.evaluation import evaluate, paired_intervals
from src.grade_scale import GradeScale


def fixture():
    rows = pd.DataFrame({
        'student_course_id': range(6), 'student_id': [1,1,1,1,2,3],
        'degree_id': [1]*6, 'part_id': [20251,20251,20252,20252,20251,20251],
        'course_id': range(6), 'course_name_sl': ['x']*6,
        'course_credits': [1,1,1,1,4,2], 'grade_version_id': [1]*6,
        'final_mark': [60]*6, 'points': [2.]*6, 'gpa_points': [2.]*6,
        'is_fail': [0,1,0,1,0,1], 'start_agpa_points': [1.,1.,1.,1.,0.,0.],
        'gpa_prev_1': [2.]*6, 'prior_registered_semesters': [2]*6,
        'prior_observed_completed_semesters': [1,1,1,1,0,np.nan],
    })
    scale = GradeScale(pd.DataFrame({'grade_version_id':[1]*5,
        'from_percent':[0,40,60,80,100], 'points':[0,1,2,3,4],
        'grade_show':['F','D','C','B','A']}))
    return rows, scale


def test_observed_plan_cancellation_weighting_and_student_macro():
    rows, scale = fixture()
    before = rows.copy(deep=True)
    metrics, courses, plans, cohorts = evaluate(rows, [80,40,80,40,80,60], [.2]*6, scale)
    assert metrics['points_mae'] == pytest.approx(5/6)
    assert metrics['plan_gpa_mae'] == pytest.approx(.25)
    assert metrics['plan_gpa_credits_weighted_mae'] == pytest.approx(.4)
    assert metrics['student_macro_plan_mae'] == pytest.approx(1/3)
    assert metrics['student_macro_points_mae'] == pytest.approx(2/3)
    assert set(['predicted_mark','actual_mark','predicted_points','fail_probability']) <= set(courses)
    assert 'start_agpa_points' in plans
    assert cohorts.set_index('cohort').loc['positive_prior_gpa_0_1','n_plans'] == 2
    assert cohorts.set_index('cohort').loc['zero_no_observed_prior_outcomes','n_plans'] == 1
    assert cohorts.set_index('cohort').loc['zero_history_unknown','n_plans'] == 1
    pd.testing.assert_frame_equal(rows, before)


def test_zero_gpa_categories_missing_and_threshold_endpoints():
    rows, scale = fixture()
    rows['student_id'] = range(6)
    rows['start_agpa_points'] = [0,0,0,np.nan,2,4]
    rows['prior_observed_completed_semesters'] = [1,0,np.nan,1,1,1]
    _, _, _, cohorts = evaluate(rows, [60]*6, [.2]*6, scale)
    c = cohorts.set_index('cohort')
    for name in ['zero_with_observed_prior_outcomes','zero_no_observed_prior_outcomes',
                 'zero_history_unknown','missing_prior_gpa','positive_prior_gpa_1_2',
                 'positive_prior_gpa_3_4','positive_prior_gpa_le_2']:
        assert c.loc[name,'n_plans'] == 1
    assert 'left-censor' in c.loc['zero_no_observed_prior_outcomes','history_caveat']


@pytest.mark.parametrize('grades,probs', [([60]*5,[.2]*6), ([[60]]*6,[.2]*6),
    ([60]*6,[.2]*5), ([60]*6,[np.nan]*6), ([np.inf]*6,[.2]*6),([60]*6,[1.1]*6)])
def test_invalid_predictions_rejected(grades, probs):
    rows, scale = fixture()
    with pytest.raises(ValueError):
        evaluate(rows, grades, probs, scale)


def test_one_class_auc_unavailable_without_warning():
    rows, scale = fixture()
    rows['is_fail'] = 0
    m, *_ = evaluate(rows, [60]*6, [.2]*6, scale)
    assert np.isnan(m['fail_pr_auc']) and np.isnan(m['fail_roc_auc'])
    assert np.isfinite(m['fail_log_loss'])


def test_cluster_bootstrap_pairs_by_keys_and_preserves_student_denominators():
    rows, scale = fixture()
    _, bc, bp, _ = evaluate(rows,[60]*6,[.2]*6,scale)
    _, cc, cp, _ = evaluate(rows,[80]*4+[60]*2,[.3]*6,scale)
    result = paired_intervals(rows,bc,cc.sample(frac=1,random_state=2),bp,
                              cp.sample(frac=1,random_state=2),draws=2000)
    overall = result[result.cohort.eq('overall')].set_index('metric')
    assert overall.loc['points_mae','delta'] == pytest.approx(4/6)
    assert overall.loc['student_macro_plan_mae','delta'] == pytest.approx(1/3)
    assert overall.loc['points_mae','n_students'] == 3
    assert overall.loc['points_mae','ci_low'] == 0
    assert overall.loc['points_mae','ci_high'] == 1
    pd.testing.assert_frame_equal(result,paired_intervals(rows,bc,cc,bp,cp,draws=2000))


@pytest.mark.parametrize('bad', ['duplicate','null','missing'])
def test_invalid_pair_keys_rejected(bad):
    rows, scale = fixture()
    _, bc,bp,_ = evaluate(rows,[60]*6,[.2]*6,scale)
    cc = bc.copy()
    if bad == 'duplicate': cc = pd.concat([cc,cc.iloc[:1]])
    if bad == 'null': cc.loc[0,'student_course_id'] = np.nan
    if bad == 'missing': cc = cc.iloc[1:]
    with pytest.raises(ValueError): paired_intervals(rows,bc,cc,bp,bp,draws=10)


def test_plan_pair_keys_and_source_identity_checked_and_inputs_unchanged():
    rows, scale = fixture()
    _, bc,bp,_ = evaluate(rows,[60]*6,[.2]*6,scale)
    before_c,before_p = bc.copy(deep=True),bp.copy(deep=True)
    paired_intervals(rows,bc,bc,bp,bp,draws=10)
    pd.testing.assert_frame_equal(bc,before_c)
    pd.testing.assert_frame_equal(bp,before_p)
    with pytest.raises(ValueError):
        paired_intervals(rows,bc,bc,bp,pd.concat([bp,bp.iloc[:1]]),draws=10)
    changed = bc.copy()
    changed.loc[0,'course_id'] = 9999
    with pytest.raises(ValueError):
        paired_intervals(rows,changed,changed,bp,bp,draws=10)


def test_inconsistent_plan_context_and_duplicate_source_rows_rejected():
    rows, scale = fixture()
    rows.loc[1,'start_agpa_points'] = 3
    with pytest.raises(ValueError,match='Inconsistent'):
        evaluate(rows,[60]*6,[.2]*6,scale)
    rows, scale = fixture()
    rows.loc[1,'student_course_id'] = rows.loc[0,'student_course_id']
    with pytest.raises(ValueError,match='duplicate'):
        evaluate(rows,[60]*6,[.2]*6,scale)
