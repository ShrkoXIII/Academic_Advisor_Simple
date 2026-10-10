# Student progress lineage audit — 2026-10-10

Read-only source, schema, metadata and artifact-header audit. No training, recommendation execution, protected-file writes, graph update, or production changes were performed by this audit. Graph navigation began with `graphify query "start_total_in_credits start_total_in_courses total_reg_credits total_reg_courses temporal history cumulative GPA training inference" --budget 2000`; its broad/truncated result was followed by actual-source verification. No memory-derived claims are used.

## Exact semantics and provenance

| Model feature | Exact local source and transformation | Established local meaning | University business definition |
|---|---|---|---|
| `start_total_in_courses` | `data/raw/v_add_student_degree_status.parquet`; normalized source field retained by `src/data/clean_student_status.py:24`, cast with `to_integer` at lines 141–154; status-to-course join at `src/data/build_student_course_enriched.py:28–34` on `(student_id, degree_id, part_id)` | Source start counter; no sum, shift, subtract-current, or alias to registered courses | **UNVERIFIED**: inclusion, repeats, transfer/exemption, successful completion and GPA inclusion rules are not defined by a DB view/procedure here |
| `start_total_in_credits` | Same status source; retained at cleaner line 25, converted to float at lines 156–173; same status join | Source start credits counter; independently retained from registered credits | **UNVERIFIED**: cannot assert earned credits, passed credits, degree completion, or official AGPA denominator from the name |
| `prior_total_reg_courses` | `src/features/temporal_features.py:add_student_history_features`, line 315: `semester["prior_total_reg_courses"] = semester["total_reg_courses"]` | **Direct alias** of the target status's source `total_reg_courses`. Source is treated as START-of-semester by code comment at lines 313–314; no shift and no subtraction of current registration | **UNVERIFIED** DB definition. Code assumption and observed equality are stronger than an invented business label, but are not an official view definition |
| `prior_total_reg_credits` | Same function, line 316: direct alias of `total_reg_credits` | Exact direct alias with no shift/subtraction. Also the denominator of `prior_fail_credit_ratio` at lines 319–322 | **UNVERIFIED** DB definition and official AGPA inclusion rules |

`src/paths.py:35` names the raw status source; line 40 separately names the raw request export. The four source fields exist in the status raw schema as `double`. Raw status has 189,158 rows, no field metadata for these fields, and only pandas schema metadata. No `.sql` file was found in the repository excluding `.venv` and `graphify-out`; DB view/procedure definitions were unavailable. The raw course schema has `in_credits`, `in_gpa`, and `in_agpa`; presence of these flags does not establish the view's aggregation rules. The raw request schema does not contain the four progress source fields; it has other credits/GPA fields that must not be substituted without a separately verified definition.

Source outlier rules compare `total_pass_* + total_fail_* <= total_reg_*` and `start_total_in_* <= end_total_in_*` (`src/data/clean_outliers.py:201–225`). Those are local consistency checks, not definitions of the source database views.

Existing documentation agrees on direct aliases (`reports/feature_leakage_audit.md:12`). `reports/projected_frozen_history_validation.md:3–7` explicitly marks its later body as historical: its old lines 38 and 54 use/claim `start_total_in_credits` as GPA credits, whereas its correction and actual current code use registered-credit fallback. That historical owner assertion is not fresh DB evidence. `reports/api_request_column_mapping.md:201` also states that SQL/backend definitions were unavailable. Do not report either start or registered credits as the university's official denominator.

## Actual V1/V2 data checks

All checks read existing Parquet columns with the project interpreter; null-safe equality was used. These are current artifact checks, not assumptions about earlier rebuilds.

| Existing artifact | Rows | Parts | Alias mismatches (`prior_total_reg_*` vs `total_reg_*`) | Missing values in all four requested model features |
|---|---:|---|---:|---:|
| `data/features/temporal_train_features.parquet` | 365,585 | 20201–20243 | 0 for both | 0 |
| `data/features/temporal_test_features.parquet` | 68,578 | 20251: 34,922; 20252: 33,656 | 0 for both | 0 |
| `data/features/temporal_train_features_v2.parquet` | 356,816 | 20201–20243 | 0 for both | 0 |
| `data/features/temporal_test_features_v2.parquet` | 67,536 | 20251: 34,408; 20252: 33,128 | 0 for both | 0 |

Both V1/V2 feature pairs declare `feature_engineering_version=2`; this feature-engineering version is distinct from the dataset suffix. V2 train/test joined back to `data/clean/student_status_v2.parquet` on `student_status_id` with `many_to_one` validation: **0 missing joins** and **0 mismatches** for all four source fields in both datasets. The V2 clean status has 107,939 rows; V1 clean status has 95,622 rows. This verifies exact status lineage of V2 model rows. V1 aliases were also checked directly; historical V1 source rebuilding was not performed.

`start_total_in_credits != total_reg_credits` occurs on 259,060 V2 train rows and 42,935 V2 test rows. These are course-row counts, not distinct student/status counts. The two credits columns therefore cannot be treated as interchangeable aliases.

## Temporal integrity and 20251 → 20252

1. `src/data/build_temporal_split.py:10–28` fixes train parts 20201–20243, test parts 20251/20252, and incomplete part 20253. `build_temporal_split` at lines 32–45 selects these sets and stably sorts them. Actual artifact parts match these boundaries.
2. Start fields are carried from the exact target status. Local `build_student_snapshot` (`src/recommendation/inputs.py:133–154`) requires one target `(student, degree, part)` status and combines its start fields with earlier shifted history; it does not roll forward an arbitrary last status's end fields.
3. `add_student_history_features` (`src/features/temporal_features.py:284–335`) reads sorted full cleaned status history. Prior GPA uses earlier registered outcomes (lines 292–305). Direct `total_*` aliases are deliberately different from `prior_registered_semesters`, which shifts `reg_total_semesters` inside `(student_id, degree_id)` at lines 325–330. Its cold-start zero case additionally examines `total_reg_courses`. Removing the model column does not remove this derivation's dependency on the source.
4. Course difficulty history is distinct from student progress. `build_temporal_course_history` applies history **before** adding each semester's outcomes (lines 228–237), clones the training state (line 252), then applies and updates holdout semesters in chronological order (lines 259–270). Thus 20251 sees cutoff 20243, 20252 sees finalized 20251, and the returned training state remains 20243. Roster rows do not add finalized outcomes.
5. The V2 runtime/source metadata states `test_protocol=sequential_roll_forward`, cutoffs `{20251: 20243, 20252: 20251}`, and updates after finalized outcomes (`src/modeling/train_models.py:440–446`; `models/model_metadata_v2.json:117–127`). In contrast, **existing V1 model metadata** declares `course_history.test_state_frozen_after_part=20243` at `models/model_metadata.json:119`. Do not pool V1 and V2 evidence as one protocol or silently retrofit historical V1 artifacts with today's builder.
6. Existing V2 immutable bundles read from `data/artifacts/history_v2/as_of_20243/metadata.json` and `as_of_20251/metadata.json` declare V2, exact matching cutoffs, and source counts 356,816 and 391,224 respectively. The difference is the 34,408 finalized 20251 course rows. No bundle was rebuilt or rewritten.
7. `CourseHistoryState.apply` rejects history overlapping the target (`src/features/temporal_features.py:149–151`). `validate_history_selection` rejects cutoff >= target and by default requires the immediate previous part (`src/features/frozen_history.py:49–61`). `FrozenHistoryManager.capture` intentionally allows older finalized history with explicit provenance (`src/recommendation/history_update.py:277–282`), while continuing to prohibit target/future history. Two-stage runtime additionally rejects a model training cutoff >= target (`src/recommendation/two_stage_engine.py:185–186`).

Tests already define the decisive behavior: `tests/test_temporal_features.py:103–120` verifies changed 20251 outcomes affect 20252 course history while leaving 20251/training state intact; lines 289–299 verify prior GPA for 20252 uses 20251 and earlier outcomes. These tests were inspected, not executed in this read-only audit.

**Temporal decision:** No temporal blocker was discovered for an isolated, fixed-V2, four-column model-matrix ablation that retains existing rows, features, splits, and GPA inputs. University definitions remain UNVERIFIED and prevent claiming these fields' official business meaning or deriving replacements for production. V1 frozen-history evidence is a separate historical protocol and cannot justify a V2 holdout claim.

## Current training, models and inference

`src/features/feature_contract.py:35–38` places all four columns in the numeric section of ordered `BASE_FEATURES` (47 total). `prepare_model_matrix` at lines 138–165 accepts an ordered subset for isolated experiments, validates it against BASE_FEATURES, converts numeric fields to float32, and returns exactly the supplied order.

Current `src/modeling/train_models.py:369–374` actually reads **V2** feature paths and verifies feature version; lines 416–429 save V2 models and their 47-column contract. This is current-source evidence even though the supplied repository guideline still describes modeling as V1. `src/features/build_temporal_features.py:92–104` also explicitly reads/writes V2 and uses cleaned V2 full status history.

Existing model text headers were inspected without making predictions:

- `models/grade_regressor.txt`, `models/fail_risk_classifier.txt`: 47 features; all four present (preserved historical V1).
- `models/grade_regressor_v2.txt`, `models/fail_risk_classifier_v2.txt`: 47 features; all four present.
- `models/shortlist_v2/grade_model.txt`, `models/shortlist_v2/fail_model.txt`: 33 features; all four present.

`src/experiments/course_only_core.py:26–28` derives the 33-feature family by dropping 14 plan-context fields, so the progress fields remain. `stage_feature_contract` (`src/recommendation/two_stage_artifacts.py:43–62`) independently enforces the same 47-minus-14 arrangement. Stage metadata and model feature names are validated (`two_stage_artifacts.py:106–115,164–166`); the official V2 loader also requires the exact ordered 47 (`src/recommendation/artifacts.py:47–51,74–77`). An isolated 43/29-feature result cannot be loaded as production by just replacing existing model files.

In local runtime, snapshot fields are copied into candidate rows (`src/recommendation/engine.py:65–82`). In two-stage runtime, normalized snapshot fields are copied into candidates (`src/recommendation/two_stage_engine.py:154–160`), Stage 1 explicitly supplies the 33 contract (lines 194–198), and Stage 2 supplies plan context then uses the default 47 (lines 163–171).

The **current dirty manifest** was read but not modified. It presently declares all three ranking approvals `APPROVED` (`models/shortlist_v2/manifest.json:27–30`); both model-stage cutoffs are 20243. This observation is not fresh user authorization to edit, retrain, or activate anything. Older documentation asserting no integrated two-stage engine is stale (`docs/architecture/04_model_training.md:71` versus actual `two_stage_engine.py`).

## Model vs API vs GPA removal

| Proposed operation | Result and dependency |
|---|---|
| Remove four columns from **isolated model matrix** | Valid ordered subset: official-family 47→43, course-only 33→29. Retrain isolated models under fixed settings; preserve frames, labels, category mapping, history and production. This measures the four explicit column inputs; it does **not** erase every student-progress proxy. |
| Remove source/raw fields | Out of scope and breaks cleaning/outlier/enrollment/history calculations. `prior_fail_credit_ratio` still needs raw registered credits and the cold-start semester derivation uses registered courses. |
| Remove fields from existing snapshot/API adapter | Current local validator requires them (`src/recommendation/inputs.py:157–173`); Backend required key list includes them (`:196–199,251–272`). Model benefit alone does not establish that they can be removed from the public/backend schema. Model-matrix removal preserves existing API compatibility. |
| Remove `prior_total_reg_credits` from local snapshot | Without explicit `current_gpa_credits`, breaks local denominator fallback; fallback and model-feature selection are independent. |
| Remove `start_total_in_credits` from model matrix | Does not change current additive GPA denominator, which uses separate `current_gpa_credits` / registered fallback. It is not safe to replace that denominator with another progress column as part of this experiment. |

`resolve_current_gpa_credits` (`src/recommendation/engine.py:21–34`) selects **explicit override → snapshot.current_gpa_credits → snapshot.prior_total_reg_credits**, rejects unknown/nonfinite/negative values, and reports its source. The Backend adapter requires explicit known `current_gpa_credits` and bypasses local fallback (`src/recommendation/inputs.py:251–279`). Two-stage shortlist/final projection both use explicit snapshot `current_gpa_credits` (`two_stage_engine.py:202,212`).

`project_cumulative_gpa` (`src/recommendation/plan_scoring.py:54–67`) uses `(current_gpa * current_gpa_credits + expected_quality_points) / (current_gpa_credits + plan_total_credits)`. It is additive, with no repeat grade replacement. This is a code formula, not verified official university policy. `summarize_scored_plans` (`:70–87`) flags repeated courses for policy needs.

**Indirect inputs retained:** `prior_fail_credit_ratio` explicitly depends on registered credits; prior failure totals, registered semesters, GPA history and degree/course features also retain related signals. All should remain unchanged for the requested four-feature ablation and be disclosed in interpretation. A gain or SHAP rank is not causal proof that the explicit columns are redundant, and course metrics cannot establish recommendation Top-K effects.

## Backend A / B / C / D contracts

| Boundary | Actual current responsibilities | Four-field relevance |
|---|---|---|
| **A: recommendation request** | In-process `student_payload={snapshot,candidates}` plus `request_payload`; normalized identity, exact credits, repeat allowances and requirement policies. `src/recommendation/inputs.py:332–370` states this is not a published Backend transport contract. Ready Backend snapshot/candidates are validated with no catalog/history reconstruction. | The four fields currently arrive as required snapshot keys; they are absent from the raw request export and should not be derived from request GPA/end/credits-to-graduate fields. Backend supplies target-start values consistent with training. |
| **B: finalized stored history** | Immutable V2 course difficulty state from finalized outcomes, explicit cutoff/provenance/hashes. `HISTORY_SOURCE_COLUMNS` (`src/features/frozen_history.py:29–33`) contains IDs, part, requirement type, course credits, attempt and final mark; no student progress fields. | Neither these bundles nor model-only removal reconstruct student start totals; Backend target snapshot remains separate. |
| **C: finalized history update** | `history_payload={delta_part,finalized:True,aggregates:[...]}` with degree/course/faculty/requirement IDs, course credits, counts, failure/retake counts, mark/attempt sums (`src/recommendation/history_update.py:1–8,34–36,81–114`). Validates, clones, applies, stages, reloads, verifies, publishes new immutable bundle, swaps one reference (`:284–321`); hash duplicate is idempotent, conflicting same-semester hash fails. No inference/training. | No four-field student-progress updates exist in this Delta envelope. Advancing difficulty history to 20251 does not update a student's snapshot progress or AGPA totals for 20252; Backend must provide the next correct target-start snapshot independently. |
| **D: internal derived features** | From validated target snapshot derive part semester and GPA trend (`src/recommendation/inputs.py:275–278`); apply finalized course difficulty; compute plan/peer context for Stage 2 (`two_stage_engine.py:154–171`). | Backend-ready prior totals and ratio are accepted, not recomputed from course history. Offline feature builder's direct aliases/ratio remain documented training semantics. Four-column model removal changes D matrix selection only in isolated experiment. |

Only this report was written by the audit agent. Current production code, metadata/manifest, raw/feature Parquet, saved models and immutable history are **NOT CHANGED** by this audit.
