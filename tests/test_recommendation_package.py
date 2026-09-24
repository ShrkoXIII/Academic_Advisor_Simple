"""Package import compatibility for recommendation callers."""
from pathlib import Path
import subprocess
import sys


def test_public_and_component_imports_do_not_load_models():
    code = """
import lightgbm as lgb

def fail_if_loaded(*args, **kwargs):
    raise AssertionError("A model was loaded during import")

lgb.Booster = fail_if_loaded
from src.recommendation import AcademicPlanRecommender
from src.recommendation.engine import AcademicPlanRecommender as Engine
from src.recommendation.plan_generation import resolve_credit_bounds
from src.recommendation.plan_scoring import rank_plans
from src.recommendation.inputs import normalize_candidates
from src.recommendation.output import save_recommendations

assert AcademicPlanRecommender is Engine
assert callable(resolve_credit_bounds)
assert callable(rank_plans)
assert callable(normalize_candidates)
assert callable(save_recommendations)
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
