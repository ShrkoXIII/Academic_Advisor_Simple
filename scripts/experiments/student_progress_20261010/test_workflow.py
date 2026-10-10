"""Safeguards for isolated student-progress experiments."""
import numpy as np
import pandas as pd
import pytest

from scripts.experiments.student_progress_20261010.workflow import (
    FIELDS, VARIANTS, feature_subset, temporal_partition, aggregate_points,
    configuration_signature, validate_signature,
    experiment_directories,
)


def test_subsets_preserve_other_features_and_order():
    original = ['gpa', *FIELDS, 'prior_fail_credit_ratio', 'context']
    assert len(VARIANTS) == 9
    assert feature_subset(original, 'A') == original
    assert feature_subset(original, 'C') == ['gpa', 'prior_total_reg_credits', 'prior_fail_credit_ratio', 'context']
    assert feature_subset(original, 'E') == ['gpa', 'prior_fail_credit_ratio', 'context']
    assert original == ['gpa', *FIELDS, 'prior_fail_credit_ratio', 'context']
    for field, variant in zip(FIELDS, ['F1', 'F2', 'F3', 'F4']):
        assert feature_subset(original, variant) == [x for x in original if x != field]
    with pytest.raises(ValueError):
        feature_subset(original, 'unknown')


def test_inner_partition_never_sees_outer_or_holdout():
    frame = pd.DataFrame({'part_id': [20211, 20223, 20231, 20243, 20251]})
    fit, inner = temporal_partition(frame, 2023)
    assert fit.part_id.tolist() == [20211]
    assert inner.part_id.tolist() == [20223]
    fit, inner = temporal_partition(frame, 2024)
    assert fit.part_id.tolist() == [20211, 20223]
    assert inner.part_id.tolist() == [20231]


def test_plan_gpa_weights_credits_and_excludes_zero_denominator():
    frame = pd.DataFrame({'student_id': ['a','a','b'], 'degree_id': ['d']*3,
                          'part_id': [20231]*3, 'course_credits': [1.,3.,0.],
                          'points': [4.,0.,4.]})
    plans = aggregate_points(frame, np.array([2.,4.,0.]))
    assert len(plans) == 1
    assert plans.iloc[0].actual_plan_gpa == 1.
    assert plans.iloc[0].predicted_plan_gpa == 3.5


def test_signature_rejects_different_features_and_parameters():
    a = configuration_signature({'features': ['a','b'], 'params': {'seed':42}})
    b = configuration_signature({'features': ['a'], 'params': {'seed':42}})
    c = configuration_signature({'features': ['a','b'], 'params': {'seed':43}})
    validate_signature(a, a)
    for signature in [b,c]:
        with pytest.raises(ValueError, match='signature'):
            validate_signature(a, signature)


@pytest.mark.parametrize('name',['..','../escaped','C:/outside','nested/name','', 'a'*81])
def test_experiment_names_cannot_escape_isolated_roots(name):
    with pytest.raises(ValueError,match='experiment name'):
        experiment_directories(name)


def test_named_experiment_uses_both_isolated_roots():
    output,models=experiment_directories('student_progress_followup')
    assert output.parent.name=='experiments'
    assert output.parent.parent.name=='evaluation'
    assert models.parent.name=='experiments'
    assert models.parent.parent.name=='models'
