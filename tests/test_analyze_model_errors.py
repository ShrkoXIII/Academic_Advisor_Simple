import ast
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.evaluation import analyze_model_errors as analysis


def test_modeling_does_not_import_evaluation():
    modeling = Path(__file__).resolve().parents[1] / "src" / "modeling"
    for source in modeling.glob("*.py"):
        tree = ast.parse(source.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(not alias.name.startswith("src.evaluation") for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                assert not (node.module or "").startswith("src.evaluation")


def course_rows():
    return pd.DataFrame({
        "student_id": ["A", "B", "C"], "degree_id": [1, 1, 2],
        "part_id": [20231, 20243, 20251], "academic_year": [2023, 2024, 2025],
        "predicted_mark": [55, 75, 95], "actual_mark": [50, 65, 100],
        "course_history_missing": [False, True, False],
        "gpa_trend_missing": [True, False, True],
    })


def plan_rows():
    return pd.DataFrame({
        "student_id": ["A", "B", "C"], "degree_id": [1, 1, 2],
        "part_id": [20231, 20243, 20251], "academic_year": [2023, 2024, 2025],
        "degree_name_sl_status": ["First", "First", "Second"],
        "plan_gpa_absolute_error": [0.25, 0.5, 1.0],
        "plan_gpa_error": [0.25, -0.5, 1.0],
        "gpa_prev_1": [2.0, np.nan, 3.5],
        "actual_plan_gpa": [2.5, 3.0, 2.5],
        "course_count": [1, 3, 8],
    })


def test_course_metrics():
    result = analysis.course_metrics(course_rows())
    assert result["course_rows"] == 3
    assert result["mark_mae"] == pytest.approx(20 / 3)
    assert result["mark_rmse"] == pytest.approx(np.sqrt(150 / 3))
    assert result["mark_bias"] == pytest.approx(10 / 3)
    assert result["mark_within_5"] == pytest.approx(2 / 3)
    assert result["mark_within_10"] == 1


def test_plan_metrics_previous_gpa_coverage_and_boundaries():
    result = analysis.plan_metrics(plan_rows())
    assert result["plans"] == 3
    assert result["plan_gpa_mae"] == pytest.approx(1.75 / 3)
    assert result["plan_gpa_rmse"] == pytest.approx(np.sqrt(1.3125 / 3))
    assert result["plan_gpa_bias"] == pytest.approx(0.75 / 3)
    assert result["plan_within_0_25"] == pytest.approx(1 / 3)
    assert result["plan_within_0_50"] == pytest.approx(2 / 3)
    assert result["plan_within_1_00"] == 1
    assert result["previous_gpa_coverage"] == pytest.approx(2 / 3)
    assert result["model_mae_on_previous_gpa_rows"] == pytest.approx(0.625)
    assert result["previous_gpa_baseline_mae"] == pytest.approx(0.75)
    assert result["improvement_over_previous_gpa"] == pytest.approx(1 - 0.625 / 0.75)


def test_selected_fold_iterations():
    metadata = {"grade_regressor": {"selected_candidate": {"folds": [
        {"fold": "validate_2023", "best_iteration": 17},
        {"fold": "validate_2024", "best_iteration": 29},
    ]}}}
    assert analysis.selected_fold_iterations(metadata) == {2023: 17, 2024: 29}


def test_build_plan_frame_attaches_context_and_year():
    courses = pd.DataFrame({
        "student_id": ["A", "A", "B", "C"], "degree_id": [1, 1, 1, 2],
        "part_id": [20231, 20231, 20243, 20251],
        "course_id": [11, 12, 13, 14], "course_credits": [2, 1, 3, 2],
        "actual_quality_points": [4, 3, 9, 8],
        "predicted_quality_points": [6, 2, 6, 6],
        "source_semester_gpa": [2.5, 2.5, 3, 4],
        "degree_name_sl_status": ["First", "First", "First", "Second"],
        "gpa_prev_1": [2.0, 2.0, np.nan, 3.5],
    })
    plans = analysis.build_plan_frame(courses)
    assert len(plans) == 3
    keyed = plans.set_index("part_id")
    assert keyed.loc[20231, "course_count"] == 2
    assert keyed.loc[20231, "actual_plan_gpa"] == pytest.approx(7 / 3)
    assert keyed.loc[20231, "degree_name_sl_status"] == "First"
    assert keyed.loc[20231, "gpa_prev_1"] == 2.0
    assert keyed.loc[20243, "academic_year"] == 2024
    assert keyed.loc[20251, "academic_year"] == 2025
    assert keyed.loc[20231, "academic_year"] == 2023


def test_year_degree_and_year_degree_analyses_keep_grouping_and_support():
    courses, plans = course_rows(), plan_rows()
    years = analysis.build_year_analysis(courses, plans).set_index("academic_year")
    assert set(years.index) == {2023, 2024, 2025}
    assert years.loc[2023, "course_rows"] == 1
    assert years.loc[2024, "mark_mae"] == 10
    assert years.loc[2025, "plan_gpa_mae"] == 1

    degrees = analysis.build_degree_analysis(courses, plans).set_index("degree_id")
    assert degrees.loc[1, "degree_name"] == "First"
    assert degrees.loc[1, "plans"] == 2
    assert not bool(degrees.loc[1, "enough_support"])
    assert analysis.MIN_RELIABLE_DEGREE_PLANS == 100
    repeated_courses = pd.concat([courses.iloc[[0]]] * 100, ignore_index=True)
    repeated_plans = pd.concat([plans.iloc[[0]]] * 100, ignore_index=True)
    supported = analysis.build_degree_analysis(repeated_courses, repeated_plans)
    assert bool(supported.loc[0, "enough_support"])

    year_degrees = analysis.build_year_degree_analysis(courses, plans)
    assert set(map(tuple, year_degrees[["academic_year", "degree_id"]].to_numpy())) == {
        (2023, 1), (2024, 1), (2025, 2)}
    assert year_degrees["plans"].tolist() == [1, 1, 1]
    assert not year_degrees["enough_support"].any()
    repeated_courses = pd.concat([courses.iloc[[0]]] * 30, ignore_index=True)
    repeated_plans = pd.concat([plans.iloc[[0]]] * 30, ignore_index=True)
    assert bool(analysis.build_year_degree_analysis(repeated_courses, repeated_plans).loc[0, "enough_support"])


def test_plan_segments_use_existing_gpa_and_count_bands():
    plans = pd.concat([plan_rows()] * 2, ignore_index=True)
    plans["actual_plan_gpa"] = [0, 0.5, 1.5, 2.5, 3.5, 4]
    plans["course_count"] = [1, 2, 4, 6, 8, 8]
    result = analysis.build_plan_segments(plans).set_index(["segment", "level"])
    assert result.loc[("actual_plan_gpa", "0"), "plans"] == 1
    assert result.loc[("actual_plan_gpa", "0-1"), "plans"] == 1
    assert result.loc[("actual_plan_gpa", "1-2"), "plans"] == 1
    assert result.loc[("actual_plan_gpa", "2-3"), "plans"] == 1
    assert result.loc[("actual_plan_gpa", "3-4"), "plans"] == 2
    assert result.loc[("course_count", "8+"), "plans"] == 2


def test_course_segments_return_metrics_by_mark_and_missing_flags():
    courses = course_rows()
    result = analysis.build_course_segments(courses).set_index(["segment", "level"])
    assert result.loc[("actual_mark", "50-59"), "course_rows"] == 1
    assert result.loc[("actual_mark", "60-69"), "course_rows"] == 1
    assert result.loc[("actual_mark", "90-100"), "course_rows"] == 1
    assert result.loc[("course_history_missing", "False"), "course_rows"] == 2
    assert result.loc[("gpa_trend_missing", "True"), "course_rows"] == 2
    assert result.loc[("actual_mark", "60-69"), "mark_mae"] == 10


@pytest.mark.parametrize(("feature", "family"), [
    ("course_history_fail_rate", "course_history"),
    ("peer_average", "plan_load"),
    ("plan_total_credits", "plan_load"),
    ("diploma_average", "pre_university"),
    ("grade_version_id", "calendar_and_policy"),
    ("course_credits", "course_and_degree_plan"),
    ("gpa_prev_1", "student_history"),
])
def test_feature_family(feature, family):
    assert analysis.feature_family(feature) == family


def test_one_way_effect_size_uses_current_anova_formula():
    frame = pd.DataFrame({"group": ["A", "A", "B", "B"],
                          "value": [1.0, 2.0, 3.0, 4.0]})
    result = analysis.one_way_effect_size(frame, "group", "value")
    assert result["groups"] == 2
    assert result["rows"] == 4
    assert np.isfinite(result["eta_squared"])
    assert np.isfinite(result["omega_squared"])
    assert result["eta_squared"] == pytest.approx(0.8)
    assert result["omega_squared"] == pytest.approx(3.5 / 5.5)


def test_build_shap_importance_uses_absolute_contributions_and_family_sums(monkeypatch):
    class FakeModel:
        def predict(self, matrix, pred_contrib=False):
            assert pred_contrib and len(matrix) == 2
            return np.array([[2.0, -1.0, 0.0, 0.5], [-4.0, 3.0, 0.0, 0.5]])

        def feature_importance(self, importance_type):
            assert importance_type == "gain"
            return [6.0, 3.0, 1.0]

        def feature_name(self):
            return ["course_history_fail_rate", "plan_total_credits", "gpa_prev_1"]

    monkeypatch.setattr(analysis, "load_category_levels", lambda path: {})
    monkeypatch.setattr(analysis, "prepare_model_matrix", lambda sample, levels: sample)
    importance, families = analysis.build_shap_importance(FakeModel(), pd.DataFrame({"x": [1, 2]}))
    assert importance.feature.tolist() == ["course_history_fail_rate", "plan_total_credits", "gpa_prev_1"]
    np.testing.assert_allclose(importance.mean_absolute_shap_mark, [3, 2, 0])
    np.testing.assert_allclose(importance.shap_share, [0.6, 0.4, 0])
    np.testing.assert_allclose(importance.gain_share, [0.6, 0.3, 0.1])
    assert importance.family.tolist() == ["course_history", "plan_load", "student_history"]
    assert importance.shap_share.sum() == pytest.approx(1)
    assert importance.gain_share.sum() == pytest.approx(1)
    indexed = families.set_index("family")
    assert indexed.loc["course_history", "mean_absolute_shap_mark"] == 3
    assert indexed.loc["plan_load", "shap_share"] == pytest.approx(0.4)
    assert indexed.loc["student_history", "gain_share"] == pytest.approx(0.1)
