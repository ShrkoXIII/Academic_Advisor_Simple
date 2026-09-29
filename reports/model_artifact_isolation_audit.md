# Model Artifact Isolation Audit

Audit date: 2026-09-27. Scope: inventory, dependency audit, characterization tests and policy documentation. Production implementation and all existing artifacts were preserved. No training, pipeline evaluation, experiment rerun or recommendation execution was performed; tests use temporary artifacts and synthetic/mock fitting.

## Inventory

The initial scan covered **264 files** with `.txt`, `.pkl`, `.joblib`, `.bin`, `.model` or `.json` extensions, including ignored project files. Git internals, the virtual environment and interpreter/test caches were excluded. Model headers, JSON roles and source references distinguish runtime artifacts from audit manifests, configuration, student snapshots and metrics. `reports/data_features_v2_20260921/logic_parity.json` mentions a feature contract but records source parity; it is not model metadata.

**14 model-related artifacts:** 4 OFFICIAL_V2, 6 EXPERIMENTAL, 4 LEGACY_V1, 0 TEMPORARY/CACHE trained models, 0 UNKNOWN. Older experiment artifacts retain EXPERIMENTAL classification because they are still research artifacts; they are not baseline V1.

Producer abbreviations: **trainer** = `src/modeling/train_models.py`; **experiment model save** = `src/experiments/modeling.py:evaluate_selected_holdout`; **experiment result save** = `src/experiments/experiment_io.py:save_results`; **baseline evaluation** = `src/evaluation/evaluate_plan_gpa.py` and `src/evaluation/analyze_model_errors.py`; **serving loader** = `src/recommendation/artifacts.py`. Historical producers are identified from preserved metadata and matching persistence contracts, not assumed to have been executed in this task.

| Artifact | Current path | Producer | Consumer(s) | Classification | Action |
| --- | --- | --- | --- | --- | --- |
| V2 grade model | `models/grade_regressor_v2.txt` | trainer | baseline evaluation | OFFICIAL_V2 | Keep |
| V2 fail model | `models/fail_risk_classifier_v2.txt` | trainer | No current standalone V2 serving reader; Recommendation migration pending | OFFICIAL_V2 | Keep |
| V2 baseline metadata | `models/model_metadata_v2.json` | trainer | baseline evaluation; experiment comparison/signature | OFFICIAL_V2 | Keep |
| V2 baseline categories | `data/artifacts/category_levels_v2.json` | trainer | baseline evaluation | OFFICIAL_V2 | Keep |
| V2 selected experiment model | `models/experiments/degree_points/selected_model_v2.txt` | experiment model save | experiment provenance; prior decision audit; no official reader | EXPERIMENTAL | Keep |
| V2 experiment categories | `models/experiments/degree_points/selected_category_levels_v2.json` | experiment model save | experiment provenance; prior decision audit | EXPERIMENTAL | Keep |
| V2 experiment metadata | `data/evaluation/experiments/degree_points/experiment_metadata_v2.json` | experiment result save | experiment reuse/provenance; prior decision audit | EXPERIMENTAL | Keep |
| Older selected experiment model | `models/experiments/degree_points/selected_model.txt` | historical experiment model save | serving loader; project status existence check; artifact-dependent tests | EXPERIMENTAL | Keep; report serving dependency |
| Older experiment categories | `models/experiments/degree_points/selected_category_levels.json` | historical experiment model save | serving loader; artifact-dependent tests | EXPERIMENTAL | Keep; report serving dependency |
| Older experiment metadata | `data/evaluation/experiments/degree_points/experiment_metadata.json` | historical experiment result save | serving loader; project status; debugging trace provenance | EXPERIMENTAL | Keep; report serving dependency |
| V1 grade model | `models/grade_regressor.txt` | historical baseline trainer | project status existence check; rollback/comparison | LEGACY_V1 | Preserve; not official V2 |
| V1 fail model | `models/fail_risk_classifier.txt` | historical baseline trainer | serving loader; project status existence check | LEGACY_V1 | Preserve; not official V2 |
| V1 baseline metadata | `models/model_metadata.json` | historical baseline trainer | serving loader; project status; debugging trace provenance | LEGACY_V1 | Preserve; not official V2 |
| V1 baseline categories | `data/artifacts/category_levels.json` | historical baseline trainer | serving loader; project status existence check | LEGACY_V1 | Preserve; not official V2 |

All four category-level files have identical SHA-256 content (`4fb4f3dff5f1d1bf70972ad9d02384a01f73e4689fb514937f2d70eb966982f6`). They remain separate namespace artifacts: shared bytes do not justify replacing an official path with an experiment dependency. No additional duplicate trained-model, misplaced model, temporary model or cached trained-model file was found.

### Auxiliary state, excluded from trained-model classification

The seven pickle files below are known feature-history state, not trained models. Frozen bundle metadata JSON describes cutoffs/hashes, not model candidates. None is moved or deleted.

| State path | Role / producer | Consumer / action |
| --- | --- | --- |
| `data/artifacts/course_history_state.pkl` | Legacy course state / historical temporal feature builder | history verification, rollback; preserve |
| `data/artifacts/course_history_state_v2.pkl` | V2 course state / temporal feature builder | history verification; preserve |
| `data/artifacts/history/as_of_20243/course_history_state.pkl` | Immutable frozen course state / frozen-history writer | serving history loader; preserve |
| `data/artifacts/history/as_of_20243/specialty_history_state.pkl` | Immutable optional specialty state / frozen-history writer with injected specialty implementation | Recommendation; preserve |
| `data/artifacts/history/as_of_20251/course_history_state.pkl` | Immutable frozen course state / frozen-history writer | serving history loader; preserve |
| `data/artifacts/history/as_of_20251/specialty_history_state.pkl` | Immutable optional specialty state / frozen-history writer with injected specialty implementation | Recommendation; preserve |
| `data/backup_v2_before_rebuild/artifacts/course_history_state_v2.pkl` | Auxiliary backup/cache state; historical rebuild backup | rollback; preserve |

These state files are outside the model-artifact classification universe. In particular, optional specialty state in existing immutable bundles must not be relocated as though it were a trained experiment model.

### Experiment results and cache

All **45** existing degree-points result files are already under `data/evaluation/experiments/degree_points/`: 12 top-level files and 33 `decision_audit/` outputs.

The top-level names are `validation_results`, `validation_summary`, `selected_holdout_course_predictions`, `selected_holdout_plan_predictions`, `selected_holdout_by_degree` (Parquet) and `experiment_metadata` (JSON), each with unsuffixed and `_v2` versions. Validation Parquet is also the signature-filtered experiment cache. All are EXPERIMENTAL and preserved. The decision-audit outputs are EXPERIMENTAL analysis, not official evaluation. Their established report is `reports/experiment_winner_decision_v2.md`; reports may remain in `reports/`, while model/result artifacts stay in their experiment namespace.

## Static dependency and writer audit

| Source consumer / producer | Finding | Disposition |
| --- | --- | --- |
| `src/experiments/degree_points.py` | V2 selected paths passed to experiment save; official metadata and saved baseline results read for comparison | Allowed Experiment → Official direction |
| `src/experiments/experiment_io.py` | V2 experiment metadata/model references; result writes only to experiment-specific constants | Allowed |
| `src/experiments/modeling.py` | Selected model/category saves take caller-supplied paths; configured caller passes experiment-specific V2 constants | Allowed configured routing; helper is not a filesystem access guard |
| `src/modeling/` | No experiment imports/artifact references; official writes use V2 paths | Isolated |
| `src/data/`, `src/features/` | No experiment imports/artifact references; specialty-history implementation is explicitly injected into generic frozen-state code | Isolated |
| `src/evaluation/evaluate_plan_gpa.py`, `analyze_model_errors.py` | Official V2 grade/category/metadata reads; no experiment fallback | Isolated official baseline evaluation |
| `src/evaluation/evaluate_xml_recommendations.py` | `AcademicPlanRecommender.load()` creates an indirect Evaluation → Recommendation → Experiments dependency | Intentional existing serving-evaluation exception; report only, migrate with Recommendation |
| `src/recommendation/artifacts.py` | Loads unsuffixed experiment model, categories, metadata and V1 failure artifacts | Known dependency; report only |
| `src/recommendation/engine.py` | Imports `prepare_matrix` from experiment modeling | Known dependency; report only |
| `src/project_status.py` | Reads/displays V1 metadata and experiment metadata; outdated V1 boundary banner | Diagnostic consumer, not official modeling/evaluation; report only |
| `src/paths.py` | Explicit official V2 and degree-points-specific constants; no unscoped current/best model alias | Existing naming retained |
| `src/main.py`, `src/experiment_degree_points.py` | Explicit experiment registry entry / CLI dispatch | Orchestration, not a baseline model consumer |
| `debugging/trace_student_29485_20251.py` | Older experiment and V1 metadata provenance | Diagnostic Recommendation trace; preserved |

Evaluation only loads the models needed by its task: GPA/error evaluators read the grade model, official categories and metadata. They do not currently load the standalone fail model; no experiment model fills that role.

No direct experiment import or artifact reference was found in any of the four official packages. The XML evaluator exception is **transitive** and must not be hidden behind that direct-import result. AST tests explicitly allow Recommendation imports only in that file, while rejecting direct experiment imports there and new Recommendation imports elsewhere in the official packages.

`load_or_train_holdout()` can reuse **experimental** cached predictions; this is not an official-model fallback. Missing V2 inputs in baseline evaluators raise an error. Existing V2 I/O tests verify missing-input behavior without V1 fallback.

### Recommendation report only

```text
CURRENT RECOMMENDATION DEPENDENCY ON EXPERIMENT: YES
Recommendation currently consumes experimental model: YES

Files:
- src/recommendation/artifacts.py
- src/recommendation/engine.py

Paths:
- DEGREE_POINTS_SELECTED_MODEL_PATH
  models/experiments/degree_points/selected_model.txt
- DEGREE_POINTS_CATEGORY_LEVELS_PATH
  models/experiments/degree_points/selected_category_levels.json
- DEGREE_POINTS_EXPERIMENT_METADATA_PATH
  data/evaluation/experiments/degree_points/experiment_metadata.json
```

The loaded older variant is `degree_history_points_temporal` (target `points`, 57 features). The V2 winner is `degree_history_mark_temporal` (target `mark`, 57 features), whose decision remains **KEEP EXPERIMENTAL**. The current loader requires a direct-points target; changing its filenames alone would not migrate it to official mark prediction. No Recommendation source, scoring, loader or defaults were changed.

## Official baseline and provenance limitations

Saved official metadata and both LightGBM headers match the ordered 47 `BASE_FEATURES`. Grade candidate: `capacity_63`; grade target: `final_mark`; fail candidate: `balanced_31`. Current trainer inputs are exactly `data/features/temporal_train_features_v2.parquet` and `data/features/temporal_test_features_v2.parquet`.

The saved official metadata has no `dataset_version` or source-file hash fields. Its artifact paths identify V2; no provenance field was added or regenerated. The trainer currently contains a pre-existing label typo `capaciy_63` at `src/modeling/train_models.py:94`, unlike saved metadata and the existing test expectation. This affects future labels/cache signatures, not the saved baseline's identity. It was already documented by the winner-decision audit and is outside this artifact-isolation change.

Some historical overview text, `PIPELINE_README.md`, `AGENTS.md` and the project-status diagnostic retain older boundaries. The current entry-point notice in `START_HERE.md` now links the authoritative [model policy](../docs/MODEL_ARTIFACT_POLICY.md). Existing V1 diagrams below that notice are explicitly historical.

## Verification

New tests pin exact official/experiment namespaces for both versions, check all official packages using AST, exercise synthetic forbidden absolute/relative/aliased imports and literal paths, and cover the XML exception. The real experiment holdout routing and JSON/Parquet save logic run against temporary paths with only fitting mocked. Eight dummy official/V1 baseline files and eight dummy older experiment files retain identical SHA-256 after saving the V2 experiment model, categories, metadata and all result frames.

Commands, run with the project virtual environment:

- Focused isolation and V2 modeling/evaluation/experiment I/O suites: **77 passed**, 0 failed.
- Full `python -m pytest -q`: **481 passed, 1 failed, 6 subtests passed** in 26.16 seconds. No skipped tests were reported.
- The single failure is `tests/test_train_models.py::test_tune_model_evaluates_every_candidate_fold_and_selects_mean_metric[grade-capacity_63-mae]`: `capaciy_63 != capacity_63`. It reproduces alone without the new test module. The trainer has no diff in this task.
- Protected-file verification: **79 existing files**, 0 changed, 0 missing, 0 additional files in the protected set. This covers `models/`, `data/artifacts/` including immutable bundles, `data/features/`, experiment result directories, Recommendation source (excluding bytecode), and the pre-existing untracked winner report.
- `git diff --check` passed; new files also have no trailing whitespace. Git only reported its existing line-ending/config-access warnings.

| Official V2 artifact | SHA-256 before = after |
| --- | --- |
| `models/grade_regressor_v2.txt` | `3794be06899046e15e854129bdd3a16437f791f3e4b72a7b0a99bf656bdebf8a` |
| `models/fail_risk_classifier_v2.txt` | `28bd34fb756c7670157a1748a0469e2b066b711d5decb9064fd433190a96d1e2` |
| `models/model_metadata_v2.json` | `8af46218a697eebc9873349a2a8ae9a2d8488278b56909cd5fc6b4a7ef82c83a` |
| `data/artifacts/category_levels_v2.json` | `4fb4f3dff5f1d1bf70972ad9d02384a01f73e4689fb514937f2d70eb966982f6` |

## Final status

```text
Official artifacts moved: NO
Experimental artifacts moved: NO
Artifacts deleted / regenerated / retrained: NO
Official hashes changed: NO
Experiment can overwrite official model: NO (configured workflow)
Official Modeling depends on Experiments: NO
Official Evaluation V2 baseline depends on Experiments: NO
Entire evaluation package transitively depends on Experiments: YES
  Existing XML Recommendation evaluator exception; report only.
Recommendation currently depends on Experiments: YES
Unknown model artifacts: NONE
Temporary/cache trained models: NONE

Official baseline remains:
grade = capacity_63
fail = balanced_31
grade target = final_mark
feature count = 47

degree_history_mark_temporal status: KEEP EXPERIMENTAL

Tests:
481 passed
1 failed
6 subtests passed

Ready to migrate Recommendation to official V2 baseline: YES
  Artifact isolation is ready; the full suite still has the documented
  pre-existing candidate-label failure. Recommendation migration was not started.
```

The no-overwrite result describes the existing configured experiment workflow, demonstrated by exact path tests and synthetic persistence. It does not claim that arbitrary callers of a generic save helper cannot supply an official path.

## Concise diff

- Added `tests/test_model_artifact_isolation.py` (42 isolation/path/persistence checks).
- Added `docs/MODEL_ARTIFACT_POLICY.md`.
- Added this inventory/audit report and the execution plan.
- Updated only the opening artifact-boundary notice in `START_HERE.md`.
- No production Python, `src/paths.py`, existing artifact or Recommendation change.
