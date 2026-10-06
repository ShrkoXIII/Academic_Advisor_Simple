"""Public API for local academic plan recommendations."""

from .artifacts import model_training_provenance
from .engine import AcademicPlanRecommender, resolve_current_gpa_credits
from .inputs import CANDIDATE_COURSE_COLUMNS, STUDENT_SNAPSHOT_COLUMNS
from .inputs import (
    PreparedRecommendationInputs, normalize_candidate_payloads,
    normalize_request_payload, normalize_student_payload, prepare_recommendation_payloads,
)
from .constraints import PlanConstraints, enumerate_feasible_plan_indices, normalize_requirement_policies
from .course_status import classify_candidate_status, normalize_previous_status
from .history_update import FrozenHistoryManager, HistorySnapshot, apply_history_delta, normalize_history_delta
from .plan_generation import build_plan_rows, enumerate_plan_indices, resolve_credit_bounds
from .plan_scoring import (
    COURSE_OUTPUT_COLUMNS, SUMMARY_COLUMNS, empty_summaries,
    project_cumulative_gpa, rank_plans, summarize_scored_plans,
)

__all__ = [
    "AcademicPlanRecommender",
    "FrozenHistoryManager",
    "HistorySnapshot",
    "apply_history_delta",
    "normalize_history_delta",
    "PreparedRecommendationInputs",
    "PlanConstraints",
    "CANDIDATE_COURSE_COLUMNS",
    "COURSE_OUTPUT_COLUMNS",
    "STUDENT_SNAPSHOT_COLUMNS",
    "SUMMARY_COLUMNS",
    "build_plan_rows",
    "empty_summaries",
    "enumerate_plan_indices",
    "enumerate_feasible_plan_indices",
    "classify_candidate_status",
    "normalize_previous_status",
    "normalize_candidate_payloads",
    "normalize_request_payload",
    "normalize_requirement_policies",
    "normalize_student_payload",
    "prepare_recommendation_payloads",
    "model_training_provenance",
    "project_cumulative_gpa",
    "rank_plans",
    "resolve_credit_bounds",
    "resolve_current_gpa_credits",
    "summarize_scored_plans",
]
