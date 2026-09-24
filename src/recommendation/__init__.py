"""Public API for local academic plan recommendations."""

from .artifacts import model_training_provenance
from .engine import AcademicPlanRecommender, resolve_current_gpa_credits
from .inputs import CANDIDATE_COURSE_COLUMNS, STUDENT_SNAPSHOT_COLUMNS
from .plan_generation import build_plan_rows, enumerate_plan_indices, resolve_credit_bounds
from .plan_scoring import (
    COURSE_OUTPUT_COLUMNS, SUMMARY_COLUMNS, empty_summaries,
    project_cumulative_gpa, rank_plans, summarize_scored_plans,
)

__all__ = [
    "AcademicPlanRecommender",
    "CANDIDATE_COURSE_COLUMNS",
    "COURSE_OUTPUT_COLUMNS",
    "STUDENT_SNAPSHOT_COLUMNS",
    "SUMMARY_COLUMNS",
    "build_plan_rows",
    "empty_summaries",
    "enumerate_plan_indices",
    "model_training_provenance",
    "project_cumulative_gpa",
    "rank_plans",
    "resolve_credit_bounds",
    "resolve_current_gpa_credits",
    "summarize_scored_plans",
]
