# Production Contract — PHP ↔ Python Recommendation Service

**Status:** Architecture contract, 2026-09-29. No API, policy engine, or production service is implemented by this document. The accepted runtime behavior is summarized in [Project State](../PROJECT_STATE.md). `docs/` already holds [Model Artifact Policy](MODEL_ARTIFACT_POLICY.md), so this contract sits beside the existing artifact boundary.

## 1. Baseline and deployment direction

```text
PHP backend → HTTP → long-running Python Recommendation Service → Official V2 recommendation core
```

Use a long-running process so the official models, category levels, metadata, GradeScale, and appropriate Frozen History bundles can be loaded and validated once, then reused. PHP spawning a Python process per request would repeatedly load these artifacts. This is an architecture direction, not an endpoint or deployment implementation.

The current local entry point is `src/recommendation/local_cli.py` (also `src/recommend_local.py`). Its core is `AcademicPlanRecommender` in `src/recommendation/engine.py`. Official artifacts are selected by `src/recommendation/artifacts.py` through `src/paths.py`: Grade `models/grade_regressor_v2.txt` (`capacity_63`, target `final_mark`), Fail `models/fail_risk_classifier_v2.txt` (`balanced_31`), `models/model_metadata_v2.json`, `data/artifacts/category_levels_v2.json`, shared `data/raw/v_acs_grade.parquet`, and base-only `data/artifacts/history_v2/as_of_<part>/`. The metadata/loader require ordered 47 `BASE_FEATURES` and feature engineering version 2. The metadata does not currently contain an explicit `dataset_version`; the strict loader treats its absence as V2 and validates the V2 artifact paths and identities.

## 2. Recommendation request contract

Proposed logical body; transport path, authentication, and schema validation remain implementation work:

```json
{
  "student_id": "29485.111",
  "degree_id": "42.111",
  "target_part": 20251,
  "min_credits": 12,
  "max_credits": 18
}
```

Exactly one credit form is allowed: `credits` for a single exact target, **or** both `min_credits` and `max_credits` for a range. As in `resolve_credit_bounds`, require finite values with `0 <= min <= max` and `max > 0`; the exact target is `credits` or `max_credits`. `12–18` therefore means exactly `18`, with no lower-credit fallback. Keep the supplied bounds in provenance.

| Category | Field / fact | Owner and rule |
| --- | --- | --- |
| Required | `student_id`, `target_part`, one credit form | PHP/caller supplies the selected student, requested semester, and requested credit target. |
| Required for first service contract | `degree_id` | PHP/caller supplies the degree context. The current snapshot/catalog lookup needs it; a later service may derive it only when a unique active degree is proven. |
| Optional | `request_id` | Caller can provide an idempotency/correlation ID; Python generates one if absent. It cannot alter inference. |
| Derived internally | candidate courses and candidate snapshot identity | Python queries the university's current procedure/source for this student, degree, and target term; database/procedure owns requestability and source version/time. The current local CLI instead reads a supplied JSON/Parquet candidate export. |
| Derived internally | student snapshot, prior student-course history, current GPA and GPA credits, degree catalog | Python loads/normalizes authoritative university data. Current local adapter uses V2 cleaned tables; production source mapping and freshness rules must be fixed before implementation. Do not send these values in every PHP request. |
| Derived internally | Frozen History cutoff/bundle, official models, category levels, GradeScale | Python selects and validates versioned official artifacts/config. The target's previous academic part is the normal Frozen History cutoff; older history requires explicit backtest mode, not an ordinary production request. |
| Derived internally | University Term Policy | Python resolves the approved, immutable version for `target_part`; policy authority is the university/config owner, not a per-request PHP value. This layer does not yet exist. |

The current local CLI requires explicit `--history-as-of-part` and permits snapshot/GPA overrides for local diagnostics. Those are not proposed public PHP fields. The service must reject missing, ambiguous, or target/future history rather than manufacture features. A target-term snapshot uses start-of-term values; prior outcomes must have been finalized before the target.

### University Term Policy choice

| Option | Assessment |
| --- | --- |
| A. PHP sends policy on every request | Easy to prototype, but different callers or requests could silently use different rules. Audit/replay would require storing the full supplied policy for each call. |
| B. Python loads a versioned term-policy snapshot by `target_part` | **Recommended.** An approved snapshot can be frozen for the semester, validated at startup/use, and recorded by version and source in every response. PHP supplies only the target term. |

Future snapshot fields: `part_id`, `conditional_retake_allowed`, `conditional_retake_max_credits`, `policy_version`, `policy_source`. These govern eligibility, not the 47-feature ML contract; they require no retraining. The current Official V2 path applies no conditional-retake policy. Introducing an eligibility filter needs its own validation and explicit comparison with this baseline before any production activation. Current additive projected GPA also has **no confirmed retake grade-replacement rule**.

## 3. Candidate source contract

Python must not invent courses. The authoritative candidate set comes from the university system/procedure, including `IS_REQUESTABLE='Y'` where that column is provided. The current `normalize_candidates` in `src/recommendation/inputs.py` filters `is_requestable='Y'` when present, checks student/degree/term, removes identical duplicate course rows, rejects conflicting duplicates, validates credits against the selected degree catalog, and derives attempt numbers from earlier cleaned history. A bare list without a requestability field is currently accepted by the local adapter; the production source integration must prove eligibility at its boundary instead of treating absent evidence as approval. `finish_status='W'` in `data/clean/registration_roster_v2.parquet` is an explicit withdrawal indicator for historical classification; `final_mark` alone is never one.

```text
University candidate source / procedure
    ↓ candidate normalization and catalog validation
Student-course historical context and target-start snapshot
    ↓ versioned University Term Policy (future; currently not applied)
Temporal feature generation + validated Frozen History
    ↓ official Grade and Fail prediction
Exhaustive exact-credit plan generation → ranking → Top 3 response
```

For prior marks, the validated classification is failed `<50`, conditional pass `50 <= final_mark < 60`, normal pass `>=60`; withdrawal uses explicit registration/status data. This classification is available in `src/features/student_course_status.py`, but its `previous_course_status` output is **not an official model feature** or an implemented retake permission rule.

## 4. Recommendation response contract

Proposed service envelope; field names map to current engine values without changing its calculations:

```json
{
  "request_id": "generated-or-caller-id",
  "status": "SUCCESS",
  "reason": null,
  "student_id": "29485.111",
  "degree_id": "42.111",
  "target_part": 20251,
  "target_credits": 18,
  "candidate_count": 15,
  "matching_plan_count": 2503,
  "plans": [
    {
      "rank": 1,
      "plan_id": 797,
      "courses": [
        {
          "course_id": "1032.111",
          "credits": 1,
          "expected_mark": 84.96699990831131,
          "expected_points": 3.0,
          "fail_probability": 0.008131930704151
        }
      ],
      "total_credits": 18,
      "expected_plan_gpa": 3.041666666666667,
      "projected_cumulative_gpa": 3.10360465116279,
      "expected_failed_credits": 0.173434142252117
    }
  ],
  "warnings": [],
  "provenance": {}
}
```

**Schema example from the saved regression result:** the course array is abbreviated to one of plan 797's nine courses; the plan metrics and course values above come from `data/debug/recommendation_trace_29485_111/result.json`. The actual mapping is `expected_mark ← predicted_mark`, `credits ← course_credits`; `expected_points` and `fail_probability` already exist. Course predictions can differ by plan because the official 47-feature model includes plan/peer context. `plan_id` is generated during exact-subset enumeration and is meaningful only with the same normalized candidate snapshot and engine version; it is not a durable university ID. `plans` contains up to three ranked plans for the first service contract. `candidate_count` is after normalization; `matching_plan_count` counts exact-credit combinations scored. `warnings` can surface current `projected_gpa_requires_repeat_policy` without changing the rank. Do not claim repeat replacement has been computed.

Current projected cumulative GPA is `(current_gpa * current_gpa_credits + expected_quality_points) / (current_gpa_credits + total_credits)`, where `expected_quality_points = Σ(course_credits * expected_points)`. Current `current_gpa_credits` defaults to snapshot `prior_total_reg_credits`. Ranking is exactly: `projected_cumulative_gpa` DESC, `expected_failed_credits` ASC, `expected_plan_gpa` DESC, `plan_id` ASC. No GPA improvement threshold removes a matching plan. The engine's current status strings are `ok` and `no_matching_credit_plan`; the service envelope above is a future mapping.

### Status and reason semantics

| `status` | Meaning | Proposed transport treatment |
| --- | --- | --- |
| `SUCCESS` | At least one exact-credit plan; `reason=null`. | Successful response. |
| `NO_RECOMMENDATION` | Valid business request with no recommendation; `plans=[]`, with a business reason such as `NO_CANDIDATES` or `NO_EXACT_CREDIT_PLAN`. | Successful business response, not HTTP 500. |
| `ERROR` | Invalid input, unavailable required context/artifacts, or an internal failure; `plans=[]`, with a stable error reason. | Appropriate client/server error response; the API mapping is future work. |

Example normal business outcome: `{"status":"NO_RECOMMENDATION","reason":"NO_EXACT_CREDIT_PLAN","plans":[]}`. Do not silently lower the credit target. This differs from technical failures, which stop inference and must not return an apparent empty recommendation.

## 5. Provenance contract

Every response and future log record must identify the exact inputs and artifacts needed to reproduce the result. Use immutable release IDs and/or SHA-256 digests, not mutable filenames alone.

| Field | Source / meaning |
| --- | --- |
| `model_version`, `grade_model_version`, `fail_model_version` | Registry release and grade/fail artifact IDs or digests; current loader already records model paths and SHA-256, but no registry release ID exists yet. |
| `feature_contract_version` | Feature engineering version `2` plus ordered 47-feature contract identity/digest. |
| `frozen_history_version`, `frozen_history_cutoff` | V2 bundle identity/digest and `as_of_part`; current bundle metadata and loader record cutoff and hashes. |
| `policy_version`, `policy_source` | Approved term-policy snapshot/version and authority. Until policy exists, record an explicit `policy_applied=false` and null version; do not imply a policy was enforced. |
| `candidate_source_version`, `candidate_source_timestamp`, `candidate_snapshot_hash` | University procedure/version, capture time, and immutable candidate-set identity after normalization. The current local adapter records file SHA-256, but production procedure versioning is unresolved. |
| `recommendation_engine_version` | Deployed service/core release or commit; include the baseline reference used for parity. |
| `request_timestamp`, `runtime_ms`, `request_id` | UTC receipt time, measured runtime, and correlation ID. Current local output has `created_at_utc` and elapsed seconds; service envelope/logging remain future work. |

Also retain `student_id`, `degree_id`, `target_part`, requested credit form/bounds, resolved `target_credits`, and the selected Frozen History cutoff with each audit record. Access and retention controls for student-level logs must be decided before deployment. Do not log full raw records by default.

## 6. Error contract

The codes below are proposed **service** reasons. Current Python exceptions/status strings are not yet a stable API error schema.

| Reason | Outcome | Current representation / future wrapper work |
| --- | --- | --- |
| `INVALID_REQUEST` | `ERROR` | Candidate import and snapshot validation raise `CandidateImportError`/`ValueError`; wrapper must map and redact details. |
| `STUDENT_NOT_FOUND` | `ERROR` | Missing or non-unique target status currently raises `ValueError`; wrapper must distinguish absent student from ambiguity. |
| `NO_CANDIDATES` | `NO_RECOMMENDATION` | Empty normalized list can flow to no plan; wrapper must classify it separately. |
| `NO_EXACT_CREDIT_PLAN` | `NO_RECOMMENDATION` | Already represented by engine status `no_matching_credit_plan` with empty recommendations and a reason string; wrapper maps it. |
| `INVALID_CREDIT_TARGET` | `ERROR` | `resolve_credit_bounds` raises `ValueError`; wrapper maps to a stable reason. |
| `INVALID_TERM_POLICY` | `ERROR` | Future policy loader/validator; no current implementation. |
| `MISSING_REQUIRED_HISTORY` | `ERROR` | Frozen History loader/selection raises on missing, older, target, or future history; wrapper maps without fallback. |
| `MODEL_ARTIFACT_ERROR` | `ERROR` | Official loader raises for missing/incompatible V2 models, categories, metadata, or GradeScale; wrapper maps and prevents experimental fallback. |
| `FEATURE_CONTRACT_ERROR` | `ERROR` | Ordered-feature/metadata checks already raise; wrapper maps. |
| `INTERNAL_ERROR` | `ERROR` | Future top-level unexpected-error handler, with correlation ID and private diagnostic log. |

Business outcomes are `NO_CANDIDATES` and `NO_EXACT_CREDIT_PLAN`; they do not indicate a crashed model/service. Missing required student/history/policy/artifact context is a technical or validation failure and must not be disguised as a no-plan result.

## 7. Production Invariants

1. Productization must not change predictions.
2. Productization must not change plan ranking.
3. Productization must not change exact-credit behavior or silently reduce the target.
4. Productization must not silently switch model artifacts or fall back to V1/experiments.
5. Productization must not import `src/experiments/` or `src/recommendation_experiments/` into serving.
6. Same normalized input + same artifacts + same policy must produce the same recommendation result; operational timestamps/runtime are excluded from result equality.
7. Models and Frozen History should be loaded once where possible, not rebuilt or retrained per request. Validate the term-specific bundle before use.
8. No training occurs in serving runtime or during a recommendation request.
9. Target-semester outcomes must not enter target features or Frozen History; the ordinary cutoff is the previous finalized academic part.
10. Removing experimental modules/artifacts must not prevent the official service from starting and producing recommendations. This becomes an executable service test after the service exists.

Allowed serving components: `src/recommendation/`, `src/features/`, official contracts/utilities (currently `src/paths.py`, `src/grade_scale.py`, and the local adapter's pure `src/data/cleaning_utils.py`), official artifacts, plus future `src/policy/` and `src/service/`. `src/modeling/` may supply shared official contracts but the trainer must never be called online. Forbidden dependencies: `src/experiments/`, `src/recommendation_experiments/`, `reports/`, `data/debug/`, `models/experiments/`, `data/features/experiments/`, and `data/evaluation/experiments/`. Reports and debug captures may be used for offline validation, never as serving inputs.

## 8. Reference regression case

**VERIFIED on 2026-09-29 against the current official `AcademicPlanRecommender` core**, reading `json/exportdata (7).json` through `load_local_inputs` and loading the V2 official artifacts. No training, experiment, policy filter, or file-output CLI run was performed in this check.

| Input / result | Verified value |
| --- | --- |
| Student / degree / target | `29485.111` / `42.111` / `20251` |
| Requested / exact target credits | `12–18` / `18` |
| Candidate input | `json/exportdata (7).json`; SHA-256 `8d8ea78e277191edc22ceed9673068d9eddecd158fa2f5d3fc0f4b17e9399f60` |
| Normalized candidate count | `15` |
| Frozen History | `data/artifacts/history_v2/as_of_20243/` |
| Exact-credit matching/scored plans | `2503` |
| Top 3 plan IDs | `797`, `2173`, `1080` |

The same values are preserved in the earlier local [student trace](../reports/recommendation_student_29485_111_trace.md), but that report and `data/debug/` are evidence only. The candidate JSON is local student data and may not be present in another checkout. Before policy changes eligibility, require parity of normalized inputs and result across **CLI == Service == API**, including counts, course predictions, ordered plan IDs, and plan metrics, with an explicit numeric tolerance if serialization changes precision. Re-verify from the official core when artifacts, candidate snapshot, or code change.

## 9. Offline Build Pipeline vs Online Serving Pipeline

| Offline build | Online serving |
| --- | --- |
| Cleaning; temporal feature dataset build; Frozen History build; training; model selection; evaluation; isolated experiments. `src/main.py` orchestrates V2 build stages; `src/modeling/train_models.py` writes official artifacts only offline. | Load and validate official artifacts; receive request; fetch/normalize university candidates; load target-start student context; resolve/apply approved term policy when implemented; build inference features with frozen history; predict; enumerate exact-credit plans; rank; return Top 3 and log provenance. |

**Training must never happen during a recommendation request.** No build/evaluation/experiment module should be invoked by the service to repair missing runtime artifacts.

## 10. Proposed production structure (not created)

```text
src/
├── recommendation/                 # existing official core: inputs, artifacts, engine, plans, ranking
├── policy/
│   ├── term_policy.py               # load/select immutable policy by target_part
│   └── validation.py                # validate policy schema and effective term
└── service/
    ├── app.py                       # HTTP entry point, transport only
    ├── schemas.py                   # request/response and stable error contracts
    ├── artifact_registry.py         # pin and validate official artifact release/digests
    ├── recommendation_service.py    # coordinate sources, policy, core, provenance
    └── health.py                    # readiness based on required official dependencies
```

The first implementation task is to pin the source/term-policy ownership and create a thin service wrapper with parity tests against the verified reference. Do not redesign scoring, features, model loading semantics, or candidate eligibility during that wrapper work.
