import pandas as pd
import pytest
from .runner import folds, family_configuration, fingerprint, decision

def test_folds_exclude_validation_and_future_rows():
    rows = pd.DataFrame({'part_id':[20223,20231,20233,20241,20243,20251]})
    result = folds(rows)
    assert result[0][1].tolist() == [True,False,False,False,False,False]
    assert result[0][2].tolist() == [False,True,True,False,False,False]
    assert result[1][1].tolist() == [True,True,True,False,False,False]
    assert result[1][2].tolist() == [False,False,False,True,True,False]

def test_fingerprint_preserves_row_identity_and_order():
    a=pd.DataFrame({'student_course_id':[1,2], 'student_id':[7,8], 'degree_id':[3,3], 'part_id':[20251,20251]})
    assert fingerprint(a) != fingerprint(a.iloc[::-1])

def test_configuration_uses_archived_rounds_without_retuning():
    meta={'grade':{'parameters':{'seed':42,'objective':'regression'},'final_boost_rounds':125},
          'fail':{'parameters':{'seed':42,'objective':'binary'},'final_boost_rounds':85}}
    assert family_configuration('stage1',meta)['grade']['final_boost_rounds']==125
    assert meta['grade']['parameters']=={'seed':42,'objective':'regression'}

def test_comparable_requires_all_primary_upper_bounds_inside_fixed_margins():
    intervals=pd.DataFrame([
        {'cohort':'overall','metric':'plan_gpa_mae','delta':.002,'ci_low':.001,'ci_high':.003},
        {'cohort':'positive_prior_gpa_le_2','metric':'plan_gpa_mae','delta':0.,'ci_low':-.004,'ci_high':.004},
        {'cohort':'overall','metric':'fail_log_loss','delta':.0005,'ci_low':.0002,'ci_high':.0008},
        {'cohort':'overall','metric':'fail_brier','delta':0.,'ci_low':-.0001,'ci_high':.0001}])
    assert decision(intervals)[0]=='COMPARABLE'
    intervals.loc[0,'ci_high']=.011
    assert decision(intervals)[0]=='INCONCLUSIVE'
    intervals.loc[0,'ci_low']=.0105
    assert decision(intervals)[0]=='WORSE'
    assert decision(intervals.iloc[1:])[0]=='INCONCLUSIVE'
