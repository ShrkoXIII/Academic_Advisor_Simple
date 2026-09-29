# Model Artifact Policy

The official V2 baseline consists only of these artifacts:

| Central path constant | Official artifact |
| --- | --- |
| `GRADE_MODEL_PATH_V2` | `models/grade_regressor_v2.txt` |
| `FAIL_MODEL_PATH_V2` | `models/fail_risk_classifier_v2.txt` |
| `MODEL_METADATA_PATH_V2` | `models/model_metadata_v2.json` |
| `CATEGORY_LEVELS_PATH_V2` | `data/artifacts/category_levels_v2.json` |

Official Recommendation also reads the shared `GRADE_SCALE_PATH` for
`predicted_mark -> GradeScale -> expected_points` conversion.

The saved grade candidate is `capacity_63`, target `final_mark`; the fail
candidate is `balanced_31`. Both use the 47 `BASE_FEATURES`. Their feature
inputs are `data/features/temporal_train_features_v2.parquet` and
`data/features/temporal_test_features_v2.parquet`.

## Experiment boundary

- Experiment models and category levels belong in `models/experiments/<name>/`.
- Experiment results, metadata and caches belong in `data/evaluation/experiments/<name>/`.
- Use experiment-specific constants from `src/paths.py`, including
  `DEGREE_POINTS_SELECTED_MODEL_PATH_V2`, `DEGREE_POINTS_CATEGORY_LEVELS_PATH_V2`
  and `DEGREE_POINTS_EXPERIMENT_METADATA_PATH_V2`.
- Experiments may read official artifacts for comparison. Official `data`,
  `features`, `modeling`, `evaluation` and `recommendation` must not import experiment
  implementations or consume their model paths.
- Experiments must never write official V2 artifacts or unsuffixed baseline
  artifacts. Missing official artifacts must raise an error; no experiment fallback.
- **KEEP EXPERIMENTAL** means no automatic promotion. The selected
  `degree_history_mark_temporal` and `degree_history_points_temporal` models
  remain research-only, including their specialty history.
- Official metadata describes the baseline only. Experiment metadata retains
  its dataset version, variant, selection protocol, signature, comparison and
  experiment artifact paths inside its own namespace.
- Do not add unscoped `CURRENT_MODEL_PATH` or `BEST_MODEL_PATH` aliases.

## Preserved history and migration status

Root `models/` also retains `grade_regressor.txt`, `fail_risk_classifier.txt`
and `model_metadata.json` as **LEGACY_V1**, alongside
`data/artifacts/category_levels.json`. These are not official V2. Preserve
them for rollback and audit. V1 experiment artifacts remain **EXPERIMENTAL**,
even though they are older. Feature-history pickle files and immutable
`data/artifacts/history/as_of_<part>/` bundles are state, not trained models;
this policy does not relocate them.

After the Recommendation migration on 2026-09-27, Modeling, Evaluation and
Official Recommendation consume the official V2 baseline. Recommendation
must not consume `src.experiments`, `DEGREE_POINTS_*`, V1 or experimental
models. Missing V2 artifacts fail explicitly. Its base-only frozen histories
live in `data/artifacts/history_v2/`, separately from preserved V1 bundles.
Generic experiment save helpers
accept caller-supplied paths: the tests protect configured routing, not
arbitrary filesystem writes by other callers.

`src/evaluation/evaluate_xml_recommendations.py` loads Official Recommendation
V2 and cleaned V2 inputs; it is no longer an experimental consumer. Official
baseline evaluators `evaluate_plan_gpa.py` and `analyze_model_errors.py` are
independent of experiments. The AST tests explicitly allow only this existing
Recommendation import, and still reject direct experiment imports there.

See [the isolation audit](../reports/model_artifact_isolation_audit.md) for
the historical pre-migration inventory, consumer references, protected hashes
and verification results. See [the Recommendation migration](../reports/recommendation_v2_migration.md)
for the current serving contract and checks.
