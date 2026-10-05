# Project State — Productization Baseline

Reference: branch `Production`, commit `d24642c`, tag `v2-development-baseline` (2026-09-29). This is the accepted **Official V2** baseline for productization. The detailed PHP/Python boundary is in [Production Contract](docs/PRODUCTION_CONTRACT.md).

## A. Current Production Baseline

| Item | Accepted state |
| --- | --- |
| Data / temporal features | V2 / `feature_engineering_version=2` |
| Plan-aware model features | Ordered 47 `BASE_FEATURES` |
| Grade / fail models | `models/grade_regressor_v2.txt` (`capacity_63`, predicts `final_mark`) / `models/fail_risk_classifier_v2.txt` (`balanced_31`) |
| Supporting artifacts | `models/model_metadata_v2.json`, `data/artifacts/category_levels_v2.json`, shared `data/raw/v_acs_grade.parquet` |
| Frozen History | Base-only `data/artifacts/history_v2/as_of_<part>/`; `as_of_20243` for target `20251`, `as_of_20251` for `20252` |
| Recommendation | `src/recommendation/engine.py`: exhaustive exact-credit plan enumeration, per-plan prediction, ranking |
| Returned plans | Top 3 by default (`top_n=3` in engine and CLI) |

The official loader in `src/recommendation/artifacts.py` requires the V2 paths and ordered feature contract. Missing or incompatible official artifacts fail; they do not fall back to V1 or experiments.

## B. Current Recommendation Rules

- One credit value is the exact target. For a range such as `12–18`, the exact target is its upper bound, `18`; the lower bound is retained for provenance. There is no automatic reduction. No exact-credit combination returns an empty result with a reason.
- Current projected GPA is `(old_gpa * previous_credits + plan_quality_points) / (previous_credits + plan_credits)`. Here `previous_credits` is the resolved `current_gpa_credits`, normally the snapshot's `prior_total_reg_credits`.
- **Limitation:** Retake GPA replacement policy is not yet implemented/confirmed. Current projection is additive, including for repeat courses.

## C. Current Ranking

`projected_cumulative_gpa` DESC → `expected_failed_credits` ASC → `expected_plan_gpa` DESC → `plan_id` ASC (`src/recommendation/plan_scoring.py`).

## D. Validated Academic Rules

Prior-mark classification: failed `<50`; conditional pass `50 <= final_mark < 60`; normal pass `>=60`. Withdrawal comes from explicit registration/status data (`finish_status='W'` in the V2 registration roster), **never** from `final_mark`. These classifications do not themselves establish a production retake eligibility policy. University candidate data with `IS_REQUESTABLE='Y'` remains the primary source of requestable courses; Python must not invent candidates.

## E. University Term Policy

Conditional-pass retake permission is a semester policy, not a model feature and not a reason to retrain. The future versioned contract is `part_id`, `conditional_retake_allowed`, `conditional_retake_max_credits`, `policy_version`, `policy_source`. No policy engine is implemented or applied in the current recommendation path.

## F. EXPERIMENTAL — NOT PRODUCTION

- 33-feature Course-Only models (`models/experiments/course_only_recommendation/`): **KEEP EXPERIMENTAL**.
- 34-feature Course-Only and 48-feature Plan-Aware `previous_course_status` models (`models/experiments/previous_course_status/`): **NEEDS MORE DATA; not promoted**. `previous_course_status` is not among the official 47 ML features. `src/features/student_course_status.py` may be reused as a business/history utility only after its data contract is respected; that does not promote the ML feature.
- Degree/direct-points and specialty-history variants in `src/experiments/`, `models/experiments/`, and `data/evaluation/experiments/` remain research-only. A two-stage recommendation design has not been validated or promoted as the official serving path.

## G. Production Boundary

Serving may use `src/recommendation/`, `src/features/`, shared official utilities/contracts, official artifacts, and future `src/policy/` and `src/service/`. It must not depend on `src/experiments/`, `src/recommendation_experiments/`, `reports/`, `data/debug/`, experimental models, or experimental feature datasets. The current local adapter uses the pure `src/data/cleaning_utils.py`; offline data builders/trainers must not run per request.

**Future architecture test:** deleting experimental code and artifacts must not prevent the official production service from starting and producing recommendations. No service exists yet, so this is an acceptance invariant, not a passed service test.

## H. Current Workstreams

- **Track A — Validation:** actual-course prediction, historical recommendation, and cohort validation; isolate prediction, candidate, and ranking errors.
- **Track B — Productization:** production contract, policy layer, artifact registry/loader, recommendation service, API, logging/provenance, PHP integration, deployment preparation.
