"""Shared API additions preserve legacy behavior and model feature contracts."""
from copy import deepcopy
from decimal import Decimal

import pandas as pd
import pytest

from src.features import temporal_features
from src.recommendation.constraints import PlanConstraints, enumerate_feasible_plan_indices
from src.recommendation.history_update import FrozenHistoryManager
from tests.two_stage_fixtures import history_manager, new_history_delta


def test_requirement_groups_do_not_merge_by_model_category():
    candidates = pd.DataFrame({
        "course_credits": [2, 2, 2, 2], "plan_requirement_type_id": ["R"] * 4,
        "candidate_group": ["NEW"] * 4, "requirement_group_id": ["A", "A", "A", "B"],
    })
    constraints = PlanConstraints(Decimal(6), {"R": Decimal(20)}, Decimal(6),
                                  requirement_group_policies={"A": Decimal(4), "B": Decimal(2)})
    assert list(enumerate_feasible_plan_indices(candidates, constraints)) == [(0, 1, 3), (0, 2, 3), (1, 2, 3)]


def test_max_new_courses_is_an_optional_plan_constraint():
    candidates = pd.DataFrame({"course_credits": [2, 2], "plan_requirement_type_id": ["R", "R"],
                               "candidate_group": ["NEW", "NEW"]})
    assert list(enumerate_feasible_plan_indices(candidates, PlanConstraints(4, {"R": 8}, 4))) == [(0, 1)]
    assert list(enumerate_feasible_plan_indices(candidates, PlanConstraints(4, {"R": 8}, 4, max_new_courses=1))) == []


def test_exact_history_selection_and_explicit_backtesting(tmp_path):
    history_manager(tmp_path, part=20242)
    history_manager(tmp_path, part=20243)
    manager = FrozenHistoryManager.load(root=tmp_path)
    assert manager.capture(target_part=20252).as_of_part == 20243  # Legacy call.
    with pytest.raises(ValueError, match="older"):
        manager.capture(target_part=20251, history_as_of_part=20242)
    assert manager.capture(target_part=20251, history_as_of_part=20242, allow_older_history=True).as_of_part == 20242
    assert manager.capture(target_part=20251, history_as_of_part=20243).as_of_part == 20243
    with pytest.raises(ValueError, match="forbidden"):
        manager.capture(target_part=20243, history_as_of_part=20243, allow_older_history=True)


def test_delta_preview_never_publishes_or_claims_finalization(tmp_path):
    manager = history_manager(tmp_path)
    delta = new_history_delta()
    delta.pop("finalized")
    original = deepcopy(delta)
    preview = manager.preview_delta(history_payload=delta)
    assert preview["status"] == "new_delta"
    assert preview["finalization_verified"] is False
    assert manager.capture(target_part=20252).as_of_part == 20243
    assert not (tmp_path / "as_of_20251").exists()
    assert delta == original


def test_partial_summary_reuses_original_gpa_shift_and_nonregistered_semesters():
    frame = pd.DataFrame({"student_status_id": ["1", "2", "3", "4"], "student_id": ["S"] * 4,
                          "part_id": [20241, 20242, 20243, 20251],
                          "semester_reg_courses": [2, 0, 2, 1], "gpa_points": [2.5, 0., 3., None]})
    result = temporal_features.compute_student_gpa_history(frame)
    target = result.iloc[-1]
    assert target.gpa_prev_1 == 3.
    assert target.gpa_prev_2 == 2.5
    assert target.gpa_trend_delta == .5
    assert target.gpa_trend_missing == 0


def test_loaded_artifact_factory_enforces_approval_without_reloading(tmp_path):
    from src.recommendation.two_stage_engine import TwoStagePlanRecommender
    from tests.two_stage_fixtures import synthetic_artifacts
    artifacts = synthetic_artifacts()
    with pytest.raises(ValueError):
        TwoStagePlanRecommender.from_loaded_artifacts(artifacts, history_manager(tmp_path))
