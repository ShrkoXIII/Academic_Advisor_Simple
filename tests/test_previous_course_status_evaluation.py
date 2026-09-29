"""Holdout comparisons keep per-status outcomes visible."""

import numpy as np

from src.experiments.previous_course_status_evaluation import status_slices


def test_status_slices_measure_retake_errors_without_small_group_pr_auc():
    result = status_slices(
        actual_grade=np.array([40, 60, 80]),
        actual_fail=np.array([1, 0, 0]),
        baseline_grade=np.array([50, 50, 70]),
        augmented_grade=np.array([42, 59, 75]),
        baseline_fail=np.array([0.5, 0.5, 0.1]),
        augmented_fail=np.array([0.8, 0.2, 0.1]),
        status=np.array(["FAILED", "FAILED", "NEVER_TAKEN"]),
    )

    failed = result["FAILED"]
    assert failed["rows"] == 2
    assert failed["grade_mae_baseline"] == 10
    assert failed["grade_mae_augmented"] == 1.5
    assert failed["grade_mae_delta"] == -8.5
    assert failed["fail_log_loss_augmented"] < failed["fail_log_loss_baseline"]
    assert failed["pr_auc_baseline"] is None
    assert result["WITHDRAWN"]["rows"] == 0
