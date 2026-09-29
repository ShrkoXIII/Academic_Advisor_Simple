# Experiment Winner Decision Audit V2

Audit date: 2026-09-26. Dataset: **V2**. Feature-engineering version: **2**. Winner: `degree_history_mark_temporal`, target=`mark`, credit weighting disabled. Reference: `baseline_mark_temporal` / saved official V2 grade regressor.

Scope: analysis of existing predictions, saved models and current source/tests. No fitting, experiment rerun, feature-artifact rebuild, selection change, production change or recommendation change was performed. Specialty features were reconstructed **in memory with the existing function** solely to inspect support and reproduce saved inference. New outputs are this report and files inside `data/evaluation/experiments/degree_points/decision_audit/`.

Notation throughout: Δ = winner − baseline; negative MAE/error Δ is better. Bias = prediction − actual. MAE, bias and tail errors use GPA units on the 0–4 scale; mark errors use the 0–100 scale. Percent columns are percentages, not fractions. Figures are rounded for display; Parquet tables retain full precision.

## 1. Executive Summary

**Recommendation: KEEP EXPERIMENTAL.** The global improvement is reproducible and supported by student-cluster resampling, but the evidence does not justify replacing the general baseline yet.

- All **12,713 plans / 67,536 courses** pair exactly. MAE falls from **0.454199 to 0.449470**, Δ **-0.004730**, or **-1.04%**.
- The improvement reverses by semester: **20251 −2.52%**, **20252 +0.74%**. The same reversal remains among the 5,694 students observed in both semesters and among degrees with history support ≥100.
- The top three improving degrees supply **91.16% of net error savings**; removing the top five leaves MAE Δ **+0.000661**. Unweighted degree-average Δ is **+0.002420**, although the plan-weighted Δ is negative.
- Of 25 degrees with ≥100 plans: **9 improve, 4 worsen, 12 are approximately unchanged**, using |Δ MAE| <0.005 as the descriptive tolerance. This is reasonably favorable, but is not uniform benefit across degrees.
- Global bias, course accuracy and tail metrics improve. **GPA=0 is essentially unchanged**, GPA in (0,1] and (3,4] worsens, and degree `40.111` has a notable bias increase despite almost unchanged MAE.
- Global bootstrap 95% CI is **[−0.006256, −0.003231]**; all 2,000 replicates have negative global Δ. This measures sampling stability conditional on these models and semesters, not future-semester stability or causality.
- Incremental production complexity is **MODERATE**: ten specialty features and a separate finalized, versioned specialty-history state; the existing recommendation loader expects a different target and V1 artifacts.

The evidence supports a useful experimental signal, rather than rejection. The missing evidence is breadth and stability across semesters, underserved histories and production-compatible inference.

## 2. Data Integrity / Paired Comparison Check

Comparison keys are `(student_id, degree_id, part_id)`. Both plan joins and the course join on `student_course_id` are validated as one-to-one.

| Check | Result |
| --- | --- |
| Baseline plans | 12,713 |
| Selected plans | 12,713 |
| Exactly matched plan keys | 12,713 |
| Missing only in baseline (selected-only keys) | 0 |
| Missing only in selected (baseline-only keys) | 0 |
| Duplicate plan keys, baseline / selected | 0 / 0 |
| Null plan-key rows, baseline / selected | 0 / 0 |
| Baseline / selected / matched course rows | 67,536 / 67,536 / 67,536 |
| Duplicate or null student_course_id, either model | 0 |
| Actual GPA, course count, credits and actual quality points disagreement | 0 |
| Plan reconstruction disagreement from constituent course predictions | 0 |
| Fresh inference vs saved marks, baseline / selected maximum difference | 0 / 0 |
| GradeScale recomputation vs saved predicted points disagreement | 0 |
| Saved degree table vs independently grouped raw plans | All counts and MAE/bias/deltas agree within 10⁻¹² |

Both saved models were loaded for prediction only. Winner inference used the existing sequential specialty-history reconstruction. Thus the reported holdout difference is reproduced from the actual saved artifacts, not inferred from an aggregate report.

Inputs used:

- `data/evaluation/plan_gpa_evaluation_2025_v2.parquet`
- `data/evaluation/plan_gpa_course_predictions_2025_v2.parquet`
- `data/evaluation/plan_gpa_metrics_2025_v2.json`
- `data/evaluation/experiments/degree_points/selected_holdout_plan_predictions_v2.parquet`
- `data/evaluation/experiments/degree_points/selected_holdout_course_predictions_v2.parquet`
- `data/evaluation/experiments/degree_points/selected_holdout_by_degree_v2.parquet`
- `validation_results_v2.parquet`, `validation_summary_v2.parquet`, `experiment_metadata_v2.json` in the same experiment directory
- `data/features/temporal_train_features_v2.parquet`, `temporal_test_features_v2.parquet`
- Both V2 grade-model files, their category-level files, `models/model_metadata_v2.json`, and `data/raw/v_acs_grade.parquet`.

**Signature reconciliation:** the stored experiment signature is `b4850b277b4435a3886f84985dfb050c8b94b93876e5274707d452f5e6c6fc53`; the current signature is `06f7270302bc1f611fa699e1fccbce147a5563ef1218edf784f7d22ce059c4e0`. The current trainer contains candidate name `capaciy_63`, while the saved metadata records `capacity_63`. Replacing that one label **in memory only** recreates the stored signature exactly. Trainer mtime is 12:33:16 UTC, later than the experiment metadata's 12:23:07 UTC creation. No other signature input difference is needed to explain the mismatch. The name change affects provenance/cache identity, not the candidate's numeric parameters; no source was edited to reconcile it. Raw validation rows carry the stored signature consistently.

Existing root documentation and AGENTS.md describe an older V1 consumer boundary. Current code and `_v2` artifacts confirm that modeling, evaluation and experiments now use V2. Recommendation remains on its existing unsuffixed artifact paths. These distinct bindings, rather than stale overview text, govern this audit.

Source fingerprints and file sizes are saved in `decision_audit/source_manifest.json`; 681 pre-existing data/model/source/test/document files were verified unchanged by SHA-256.

## 3. Global Baseline vs Winner

| Metric | Baseline | Winner | Winner − baseline |
| --- | --- | --- | --- |
| Plan GPA MAE | 0.454199 | 0.449470 | -0.004730 |
| Plan GPA RMSE | 0.639670 | 0.633992 | -0.005678 |
| Plan GPA bias | 0.213762 | 0.200083 | -0.013679 |
| Within ±0.25, % | 43.955007 | 44.544954 | 0.589947 |
| Within ±0.50, % | 68.378825 | 69.008102 | 0.629277 |
| Within ±1.00, % | 89.514670 | 89.758515 | 0.243845 |
| Credit-weighted plan MAE (diagnostic) | 0.416908 | 0.411111 | -0.005797 |

Relative MAE change = 100 × (winner MAE − baseline MAE) / baseline MAE = **-1.04%**. Credit-weighted evaluation is a diagnostic here; both fitted variants retain their original temporal training weights.

The raw per-plan delta is preserved. For substantive direction counts, values within ±10⁻¹² are treated as unchanged to prevent floating-point subtraction noise from becoming a model win/loss. The exact-sign counts are also shown to implement the literal Δ<0 / Δ=0 / Δ>0 definition.

| Direction | Practical count (10⁻¹² tolerance) | Practical % | Exact-sign count | Exact-sign % |
| --- | --- | --- | --- | --- |
| Improved | 4,207 | 33.092110 | 4,229 | 33.265162 |
| Unchanged | 4,945 | 38.897192 | 4,910 | 38.621883 |
| Worsened | 3,561 | 28.010698 | 3,574 | 28.112955 |

All subsequent improved/worsened percentages use the practical tolerance. Only 35 rows change classification under exact arithmetic; this does not affect the MAE, bootstrap or decision.

| Delta distribution | Δ absolute error |
| --- | --- |
| Mean | -0.004730 |
| Median / P50 | 0.000000 |
| P25 | -0.041667 |
| P75 | 0.029412 |
| P90 | 0.083333 |
| P95 | 0.117647 |

| Magnitude | Value |
| --- | --- |
| Mean improvement, improved plans | 0.082607 |
| Median improvement, improved plans | 0.062500 |
| Mean degradation, worsened plans | 0.080707 |
| Median degradation, worsened plans | 0.062500 |
| Total absolute error saved | 347.527142 |
| Total absolute error added | 287.398982 |
| Net error change, added − saved | -60.128160 |

Total error means the sum of **unweighted per-plan absolute GPA errors**, not credits or quality points. Improvements occur on thousands of plans, but the median plan delta is zero and typical winning/losing magnitudes are very similar. The small net benefit is the difference between sizable opposing changes.

There are no identical predicted marks across the 67,536 courses, but **52,849 courses (78.253% rounded)** have identical converted points. The discrete GradeScale mapping and plan aggregation explain much of the unchanged plan-GPA mass.

## 4. Validation Stability: 2023 / 2024

| Variant | 2023 MAE | 2024 MAE | Mean MAE | Δ vs baseline 2023 | Δ vs baseline 2024 | Stability |
| --- | --- | --- | --- | --- | --- | --- |
| degree_history_mark_temporal | 0.406947 | 0.422909 | 0.414928 | -0.000882 | -0.002918 | improves both |
| degree_history_points_credit_weighted | 0.404111 | 0.428324 | 0.416217 | -0.003718 | 0.002497 | 2023 only |
| degree_history_points_temporal | 0.403876 | 0.428778 | 0.416327 | -0.003953 | 0.002951 | 2023 only |
| baseline_mark_temporal | 0.407829 | 0.425827 | 0.416828 | 0.000000 | 0.000000 | baseline |
| mark_credit_weighted | 0.407439 | 0.426231 | 0.416835 | -0.000390 | 0.000404 | 2023 only |
| points_temporal | 0.405133 | 0.430604 | 0.417868 | -0.002696 | 0.004777 | 2023 only |
| degree_id_mark_temporal | 0.408965 | 0.427252 | 0.418108 | 0.001136 | 0.001425 | worsens both |
| points_credit_weighted | 0.405491 | 0.432772 | 0.419131 | -0.002338 | 0.006945 | 2023 only |
| degree_id_points_temporal | 0.406112 | 0.433427 | 0.419769 | -0.001717 | 0.007600 | 2023 only |
| degree_id_points_credit_weighted | 0.406382 | 0.435534 | 0.420958 | -0.001446 | 0.009707 | 2023 only |

Mean is the equally weighted average of the two validation-year metrics, as in the existing selection rule. Each variant has 77,014 courses / 16,500 plans in 2023 and 74,433 courses / 15,413 plans in 2024; saved aggregates show identical fold supports. Raw per-variant validation predictions are not saved, so this audit cannot independently establish validation key-level pairing or subgroup CIs.

- Improves both folds: **degree_history_mark_temporal** only (2023 Δ −0.000882, 2024 Δ −0.002918).
- Improves only 2023: **mark_credit_weighted and all six direct-points variants**.
- Improves only 2024: **none**.
- Worsens both: **degree_id_mark_temporal**.
- Baseline has zero deltas and is not categorized as improving/worsening itself.

The winner's validation mean reduction is 0.001900 GPA / 0.456%. Its course-mark MAE slightly worsens in 2023 (9.267135 → 9.282080) and improves in 2024 (9.777679 → 9.760005). Validation therefore supports a small consistent **plan** benefit, not universally improved course marks.

The existing rule is unchanged: select the lowest mean Plan GPA MAE among variants improving **both** validation years; fall back to baseline if none qualifies. Winner final rounds = round(mean(127,115)) = 121; baseline final rounds = 114. No 2025 subgroup result was used to reselect a variant.

## 5. Holdout Performance: 2025

| Evaluation coverage | Plans | Baseline MAE | Winner MAE | Δ MAE | Relative Δ % | Baseline bias | Winner bias | Improved % | Worsened % |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete evaluated credits | 10022 | 0.390581 | 0.385489 | -0.005092 | -1.303623 | 0.137670 | 0.124551 | 33.955298 | 28.946318 |
| partial evaluated credits | 2691 | 0.691133 | 0.687752 | -0.003381 | -0.489245 | 0.497151 | 0.481385 | 29.877369 | 24.526198 |

The reproduced 2025 MAE reduction is −0.004730 / −1.04%. It also appears in the 10,022 plans with complete evaluated credits (−1.30%), so it is not created solely by partial-credit plans.

**Evaluation denominator:** actual and predicted plan GPA both use the same saved scored-course rows, `sum(credits × points) / sum(credits)`. There are **2,691 partial-credit plans (21.17%)** relative to the full registration roster represented by `plan_total_credits` and `plan_course_count`. No evaluated plan exceeds its registered credits or course count. Their MAE/bias are much higher. Course counts and credits in the main segmentation/extreme tables are **evaluated** values; full-roster values and coverage are retained in the paired table. A lower error on this denominator does not by itself establish full-semester-GPA accuracy or better recommendation outcomes.

The saved metadata records validation-based selection followed by one selected-model holdout evaluation. This audit reuses those saved results and performs prediction-only reproduction; it does not establish every historical interaction with the holdout.

## 6. 20251 vs 20252

| Part | Plans | Baseline MAE | Winner MAE | Δ MAE | Relative Δ % | Baseline bias | Winner bias | Improved % | Worsened % |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20251 | 6469 | 0.487710 | 0.475433 | -0.012276 | -2.517162 | 0.284468 | 0.256973 | 36.821765 | 23.914052 |
| 20252 | 6244 | 0.419482 | 0.422571 | 0.003089 | 0.736402 | 0.140509 | 0.141143 | 29.228059 | 32.254965 |

20251 saves **79.416318** total error units; 20252 adds **19.288158**, offsetting 24.29% of that gain. Its MAE, RMSE and all three within-tolerance rates move in the wrong direction; bias also rises slightly (+0.000634). The winner's advantage is **larger in 20251**, before incorporating finalized 20251 specialty outcomes.

Composition sensitivity: restrict to the 5,694 students appearing in both parts. This keeps the same student identities across semesters (their plans and outcomes still differ):

| Part | Common-student plans | Baseline MAE | Winner MAE | Δ MAE | Relative Δ % |
| --- | --- | --- | --- | --- | --- |
| 20251 | 5694 | 0.480687 | 0.467758 | -0.012928 | -2.689578 |
| 20252 | 5694 | 0.398866 | 0.401629 | 0.002763 | 0.692591 |

The semester reversal persists (−2.69% then +0.69%). This weakens an explanation based purely on students entering/leaving the evaluated sample. It does not isolate why the reversal occurs. Sequential-history support and resampling evidence are examined in sections 10 and 17.

## 7. Degree-Level Analysis

The saved `selected_holdout_by_degree_v2.parquet` was cross-checked against independently aggregated paired raw plans. Every count, MAE, bias and MAE delta agrees within 10⁻¹². Names are retained in the local tables; IDs below distinguish curriculum versions.

Descriptive classification: improved if Δ<−0.005, worsened if Δ>+0.005, approximately unchanged if |Δ|<0.005. No observed degree lies exactly on the threshold. This is a display/triage tolerance, not a significance test or new selection criterion.

| Degree | Plans | Baseline MAE | Winner MAE | Δ MAE | Relative Δ % | Baseline bias | Winner bias | Improved % | Classification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 41.111 | 1895 | 0.486198 | 0.469916 | -0.016282 | -3.348885 | 0.272977 | 0.213526 | 43.799472 | improved |
| 2.111 | 1469 | 0.464879 | 0.465693 | 0.000814 | 0.175077 | 0.211718 | 0.193334 | 26.684820 | approximately unchanged |
| 42.111 | 1353 | 0.401772 | 0.397049 | -0.004723 | -1.175503 | 0.096745 | 0.044171 | 38.802661 | approximately unchanged |
| 44.111 | 986 | 0.414791 | 0.400884 | -0.013907 | -3.352772 | 0.114135 | 0.090984 | 41.582150 | improved |
| 1.111 | 866 | 0.299514 | 0.287684 | -0.011830 | -3.949567 | 0.184904 | 0.156134 | 39.838337 | improved |
| 13.111 | 769 | 0.411834 | 0.412364 | 0.000531 | 0.128832 | 0.252440 | 0.262380 | 33.029909 | approximately unchanged |
| 40.111 | 670 | 0.537825 | 0.538897 | 0.001072 | 0.199320 | 0.072678 | 0.184424 | 36.417910 | approximately unchanged |
| 24.111 | 423 | 0.540740 | 0.549467 | 0.008727 | 1.613882 | 0.425345 | 0.439903 | 24.586288 | worsened |
| 50.111 | 378 | 0.600156 | 0.602780 | 0.002624 | 0.437292 | 0.340775 | 0.352610 | 22.751323 | approximately unchanged |
| 26.111 | 353 | 0.352622 | 0.350631 | -0.001990 | -0.564442 | 0.210144 | 0.197028 | 25.779037 | approximately unchanged |
| 3.111 | 247 | 0.375202 | 0.374878 | -0.000325 | -0.086539 | 0.156438 | 0.153919 | 26.720648 | approximately unchanged |
| 47.111 | 221 | 0.393397 | 0.387007 | -0.006390 | -1.624340 | 0.283504 | 0.279059 | 28.959276 | improved |
| 29.111 | 215 | 0.419129 | 0.406187 | -0.012942 | -3.087841 | 0.287038 | 0.271450 | 32.558140 | improved |
| 46.111 | 201 | 0.470680 | 0.451631 | -0.019049 | -4.047107 | 0.383859 | 0.343475 | 45.273632 | improved |
| 27.111 | 189 | 0.343190 | 0.337408 | -0.005782 | -1.684848 | 0.182958 | 0.152510 | 34.920635 | improved |
| 48.111 | 187 | 0.422668 | 0.422622 | -0.000046 | -0.010986 | 0.287950 | 0.292088 | 25.133690 | approximately unchanged |
| 65.111 | 178 | 0.594052 | 0.601887 | 0.007835 | 1.318955 | 0.294843 | 0.337380 | 18.539326 | worsened |
| 45.111 | 161 | 0.435712 | 0.453828 | 0.018116 | 4.157699 | 0.244249 | 0.289390 | 22.360248 | worsened |
| 11.111 | 159 | 0.650874 | 0.641872 | -0.009001 | -1.382978 | 0.543246 | 0.533696 | 33.962264 | improved |
| 59.111 | 129 | 0.599459 | 0.604859 | 0.005401 | 0.900912 | 0.061982 | 0.075148 | 13.178295 | worsened |
| 58.111 | 125 | 0.586739 | 0.591655 | 0.004916 | 0.837927 | 0.219437 | 0.221661 | 18.400000 | approximately unchanged |
| 57.111 | 124 | 0.630358 | 0.633914 | 0.003556 | 0.564091 | 0.218277 | 0.233258 | 14.516129 | approximately unchanged |
| 8.111 | 118 | 0.430577 | 0.426041 | -0.004536 | -1.053447 | 0.246867 | 0.243436 | 25.423729 | approximately unchanged |
| 36.111 | 103 | 0.560812 | 0.558518 | -0.002293 | -0.408937 | 0.437547 | 0.424771 | 27.184466 | approximately unchanged |
| 55.111 | 101 | 0.534630 | 0.512807 | -0.021823 | -4.081865 | 0.395527 | 0.358441 | 45.544554 | improved |
| 64.111 | 96 | 0.617566 | 0.617974 | 0.000408 | 0.066069 | 0.154985 | 0.156927 | 17.708333 | approximately unchanged |
| 7.111 | 95 | 0.395792 | 0.395841 | 0.000048 | 0.012187 | -0.109938 | -0.103689 | 27.368421 | approximately unchanged |
| 60.111 | 94 | 0.653629 | 0.657166 | 0.003538 | 0.541265 | 0.245686 | 0.268967 | 17.021277 | approximately unchanged |
| 34.111 | 87 | 0.423745 | 0.421711 | -0.002034 | -0.479956 | 0.213902 | 0.215704 | 22.988506 | approximately unchanged |
| 53.111 | 86 | 0.355469 | 0.354978 | -0.000491 | -0.138040 | 0.140306 | 0.085867 | 33.720930 | approximately unchanged |
| 30.111 | 83 | 0.426777 | 0.422368 | -0.004409 | -1.033082 | 0.124058 | 0.104334 | 28.915663 | approximately unchanged |
| 61.111 | 82 | 0.641654 | 0.652920 | 0.011266 | 1.755729 | 0.317419 | 0.337037 | 14.634146 | worsened |
| 49.111 | 81 | 0.486576 | 0.506822 | 0.020246 | 4.160819 | 0.357820 | 0.393252 | 19.753086 | worsened |
| 31.111 | 67 | 0.442439 | 0.451708 | 0.009269 | 2.094969 | 0.242185 | 0.260066 | 10.447761 | worsened |
| 10.111 | 62 | 0.458537 | 0.429991 | -0.028545 | -6.225342 | 0.012526 | 0.033183 | 35.483871 | improved |
| 6.111 | 36 | 0.411360 | 0.393317 | -0.018043 | -4.386106 | 0.067480 | 0.116475 | 30.555556 | improved |
| 35.111 | 34 | 0.360311 | 0.359496 | -0.000814 | -0.225976 | 0.146714 | 0.152197 | 20.588235 | approximately unchanged |
| 54.111 | 31 | 0.416768 | 0.420367 | 0.003598 | 0.863402 | 0.011720 | -0.029326 | 22.580645 | approximately unchanged |
| 33.111 | 31 | 0.383667 | 0.405280 | 0.021614 | 5.633411 | 0.107931 | 0.133453 | 9.677419 | worsened |
| 56.111 | 29 | 0.380182 | 0.389451 | 0.009269 | 2.437992 | 0.207061 | 0.206570 | 20.689655 | worsened |
| 37.111 | 27 | 0.398476 | 0.428251 | 0.029776 | 7.472351 | -0.086195 | -0.115971 | 0.000000 | worsened |
| 52.111 | 22 | 0.279017 | 0.288034 | 0.009017 | 3.231699 | 0.128773 | 0.112731 | 22.727273 | worsened |
| 39.111 | 20 | 0.772207 | 0.694666 | -0.077541 | -10.041485 | 0.592247 | 0.474825 | 30.000000 | improved |
| 4.111 | 13 | 0.649729 | 0.667357 | 0.017628 | 2.713164 | 0.225271 | 0.242899 | 0.000000 | worsened |
| 16.111 | 7 | 0.400917 | 0.510310 | 0.109394 | 27.285905 | 0.215202 | 0.348406 | 28.571429 | worsened |
| 22.111 | 6 | 0.463542 | 0.496776 | 0.033234 | 7.169609 | 0.380208 | 0.330109 | 16.666667 | worsened |
| 20.111 | 2 | 0.072479 | 0.094538 | 0.022059 | 30.434783 | -0.072479 | -0.094538 | 0.000000 | worsened |
| 5.111 | 2 | 0.591667 | 0.616667 | 0.025000 | 4.225352 | -0.008333 | -0.033333 | 0.000000 | worsened |

Sample-support bands:

| Plans per degree | Degrees | Plans | Improved | Worsened | Approx. unchanged | Unweighted Δ | Plan-weighted Δ |
| --- | --- | --- | --- | --- | --- | --- | --- |
| <30 | 9 | 128 | 1 | 8 | 0 | 0.019759 | 0.007881 |
| 30-99 | 14 | 965 | 2 | 4 | 8 | 0.001118 | 0.001358 |
| 100-299 | 15 | 2458 | 6 | 3 | 6 | -0.002824 | -0.003071 |
| 300+ | 10 | 9162 | 3 | 1 | 6 | -0.003496 | -0.005992 |

For **plans ≥100**, 9 of 25 degrees improve materially, 4 worsen, and 12 are approximately unchanged. With no materiality tolerance, 15 have negative and 10 positive deltas. Thus **21/25 do not materially regress**, a positive result; the improvement does not span a majority of degrees materially.

Well-supported regressions are `24.111` (423 plans, +0.008727), `45.111` (161, +0.018116), `65.111` (178, +0.007835) and `59.111` (129, +0.005401). Degree `16.111` has the largest relative deterioration (+27.29%) but only seven plans; it warrants sparse-history caution rather than the same weight as a 1,000-plan degree.

| Degree weighting view | Δ MAE |
| --- | --- |
| Unweighted mean of 48 degree MAE deltas | 0.002420 |
| Unweighted median degree MAE delta | 0.000469 |
| Plan-count-weighted degree MAE delta | -0.004730 |

Plan weighting reproduces the global delta. Giving every degree one vote yields a small **positive** mean and almost-zero median. Low-support degrees explain part of that disparity; even so, the overall gain is disproportionately carried by larger degrees.

Top 10 degrees by total error reduction (`sum(selected AE − baseline AE)`; this equals plans × Δ MAE):

| Degree | Plans | Baseline MAE | Winner MAE | Δ MAE | Total error Δ |
| --- | --- | --- | --- | --- | --- |
| 41.111 | 1895 | 0.486198 | 0.469916 | -0.016282 | -30.854826 |
| 44.111 | 986 | 0.414791 | 0.400884 | -0.013907 | -13.712304 |
| 1.111 | 866 | 0.299514 | 0.287684 | -0.011830 | -10.244350 |
| 42.111 | 1353 | 0.401772 | 0.397049 | -0.004723 | -6.390000 |
| 46.111 | 201 | 0.470680 | 0.451631 | -0.019049 | -3.828836 |
| 29.111 | 215 | 0.419129 | 0.406187 | -0.012942 | -2.782537 |
| 55.111 | 101 | 0.534630 | 0.512807 | -0.021823 | -2.204110 |
| 10.111 | 62 | 0.458537 | 0.429991 | -0.028545 | -1.769820 |
| 39.111 | 20 | 0.772207 | 0.694666 | -0.077541 | -1.550821 |
| 11.111 | 159 | 0.650874 | 0.641872 | -0.009001 | -1.431229 |

Top 10 degrees by total error increase:

| Degree | Plans | Baseline MAE | Winner MAE | Δ MAE | Total error Δ |
| --- | --- | --- | --- | --- | --- |
| 24.111 | 423 | 0.540740 | 0.549467 | 0.008727 | 3.691482 |
| 45.111 | 161 | 0.435712 | 0.453828 | 0.018116 | 2.916611 |
| 49.111 | 81 | 0.486576 | 0.506822 | 0.020246 | 1.639890 |
| 65.111 | 178 | 0.594052 | 0.601887 | 0.007835 | 1.394678 |
| 2.111 | 1469 | 0.464879 | 0.465693 | 0.000814 | 1.195617 |
| 50.111 | 378 | 0.600156 | 0.602780 | 0.002624 | 0.992037 |
| 61.111 | 82 | 0.641654 | 0.652920 | 0.011266 | 0.923788 |
| 37.111 | 27 | 0.398476 | 0.428251 | 0.029776 | 0.803939 |
| 16.111 | 7 | 0.400917 | 0.510310 | 0.109394 | 0.765756 |
| 40.111 | 670 | 0.537825 | 0.538897 | 0.001072 | 0.718236 |

Across degrees with negative net deltas, gross degree-level savings are **80.099115**; degrees with positive deltas add **19.970955**. These sums differ from plan-direction gross savings/additions because wins and losses within a degree cancel first.

Degree `41.111` alone provides 30.854826 saved units, **51.32% of net savings**. Degrees `41.111`, `44.111`, `1.111` provide 54.811480, **91.16% of net savings / 68.43% of gross degree savings**, on 3,747 plans (29.48% of the sample).

Descriptive concentration sensitivity, not a revised target population or selection rule:

| Excluded degrees | Removed plans | Share of gross degree savings % | Remaining plans | Baseline MAE | Winner MAE | Δ MAE | Relative Δ % |
| --- | --- | --- | --- | --- | --- | --- | --- |
| top 1 improving degrees | 1895 | 38.520807 | 10818 | 0.448594 | 0.445888 | -0.002706 | -0.603214 |
| top 3 improving degrees | 3747 | 68.429570 | 8966 | 0.466711 | 0.466118 | -0.000593 | -0.127056 |
| top 5 improving degrees | 5301 | 81.187309 | 7412 | 0.478457 | 0.479118 | 0.000661 | 0.138232 |
| top 10 improving degrees | 5858 | 93.345392 | 6855 | 0.474814 | 0.476950 | 0.002136 | 0.449811 |

Excluding the best three reduces the gain to −0.000593; excluding the best five reverses it to +0.000661. This is the clearest evidence that the ~1% global gain lacks broad degree-level support. These post hoc exclusions are diagnostics only; they do not justify degree-specific routing.

## 8. GPA Segment Analysis

Bins match current Error Analysis: `pd.cut(actual_plan_gpa, [-0.01, 0.001, 1, 2, 3, 4.01])`, right-closed. The zero-labeled bin contains **only exact zeros in these artifacts**. Remaining intervals are (0.001,1], (1,2], (2,3], (3,4.01]; observed maximum GPA is within 4.

| Actual GPA band | Plans | Baseline MAE | Winner MAE | Δ MAE | Relative Δ % | Baseline bias | Winner bias | Improved % | Worsened % |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 272 | 1.990080 | 1.991097 | 0.001017 | 0.051099 | 1.990080 | 1.991097 | 16.911765 | 17.279412 |
| 0-1 | 823 | 1.269115 | 1.275758 | 0.006643 | 0.523443 | 1.259182 | 1.270229 | 29.161604 | 30.498177 |
| 1-2 | 3189 | 0.565715 | 0.554276 | -0.011439 | -2.022069 | 0.542173 | 0.534268 | 37.597993 | 26.026968 |
| 2-3 | 6254 | 0.257247 | 0.248599 | -0.008648 | -3.361586 | 0.019247 | -0.001094 | 35.976975 | 27.822194 |
| 3-4 | 2175 | 0.356583 | 0.367934 | 0.011351 | 3.183386 | -0.326166 | -0.340349 | 21.701149 | 31.862069 |

**GPA=0:** 272 plans retain extreme overprediction: MAE/bias **1.990080 → 1.991097**, Δ +0.001017. 46 improve, 47 worsen, 179 are unchanged. The model does not solve this failure mode. By part: 20251 zero-GPA MAE 2.067331 → 2.052772; 20252 1.917244 → 1.932946.

**Very low GPA (0,1]:** 823 plans worsen by +0.006643 / +0.52%, with overprediction bias rising from +1.259182 to +1.270229. **High GPA (3,4]:** 2,175 plans worsen by +0.011351 / +3.18%, with stronger underprediction (−0.326166 → −0.340349).

The 1–2 and 2–3 segments save 36.479460 and 54.081873 error units respectively; the zero/very-low/high bands add 30.433173. The improvement comes from the middle of the GPA distribution, rather than repair of zero-GPA extremes.

## 9. Course Load Analysis

Course-count bins match Error Analysis: 1; 2–3; 4–5; 6–7; 8+. Credits: low <12, normal 12–18 inclusive, high >18. These credit cutoffs separate the existing 12–18 planning range from smaller/larger evaluated loads; data quantiles support inspecting both tails: min 1, P5 7, P25 14, median 17, P75 18, P95 24, max 39. They are descriptive boundaries, not eligibility rules.

| Load variable | Band | Plans | Baseline MAE | Winner MAE | Δ MAE | Relative Δ % | Baseline bias | Winner bias | Improved % | Worsened % |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| course_count | 1 | 549 | 0.836066 | 0.838342 | 0.002277 | 0.272331 | 0.384335 | 0.356557 | 13.661202 | 13.479053 |
| course_count | 2-3 | 849 | 0.670584 | 0.672284 | 0.001700 | 0.253468 | 0.460060 | 0.455846 | 22.261484 | 22.850412 |
| course_count | 4-5 | 4759 | 0.509067 | 0.504487 | -0.004580 | -0.899618 | 0.283631 | 0.276401 | 31.435175 | 27.757932 |
| course_count | 6-7 | 5896 | 0.366668 | 0.360607 | -0.006061 | -1.652931 | 0.116200 | 0.098964 | 36.736771 | 29.799864 |
| course_count | 8+ | 660 | 0.244526 | 0.236508 | -0.008019 | -3.279273 | 0.122807 | 0.093948 | 42.575758 | 32.575758 |
| total_credits | high (>18) | 2209 | 0.321366 | 0.311002 | -0.010364 | -3.224998 | 0.160707 | 0.126303 | 37.120869 | 29.017655 |
| total_credits | low (<12) | 1425 | 0.763177 | 0.765397 | 0.002220 | 0.290832 | 0.486883 | 0.478275 | 22.175439 | 20.561404 |
| total_credits | normal (12-18) | 9079 | 0.438023 | 0.433574 | -0.004449 | -1.015810 | 0.183803 | 0.174370 | 33.825311 | 28.934905 |

Very small course-count plans (1 and 2–3) and low-credit plans deteriorate slightly. Normal plans improve, and high-credit / 8+ course plans improve more. Therefore the winner does **not** spoil large loads globally, but does not improve small-load plans. Count and credits refer to scored rows; partial evaluation can move a normally registered load into a small evaluated-load band. Full-roster counts, credits and coverage are available in `paired_plan_comparison.parquet`.

## 10. Specialty-History Support Analysis

Support is a **weighted historical course-outcome count**, not students or evaluated plans: pre-2022 rows weight 0.25; later rows weight 1. Bins are support=0 (missing), 0<support<20, 20≤support<100, support≥100. Fractional positive supports are allowed.

Each plan has one degree support. Degree×requirement support varies by its courses, so the primary plan-level view uses the **minimum** support across scored courses and marks missing if **any** requirement history is missing. The mean-support view is saved separately to reveal aggregation sensitivity; it is not credit weighted. Course-level support metrics avoid plan-level attribution entirely.

Plan-level degree support:

| Degree support | Plans | Baseline MAE | Winner MAE | Δ MAE | Relative Δ % | Baseline bias | Winner bias | Improved % | Worsened % |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| missing (0) | 396 | 0.721132 | 0.725845 | 0.004713 | 0.653584 | 0.312071 | 0.325842 | 7.575758 | 10.606061 |
| positive <20 | 0 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| 20-<100 | 7 | 0.400917 | 0.510310 | 0.109394 | 27.285905 | 0.215202 | 0.348406 | 28.571429 | 71.428571 |
| 100+ | 12310 | 0.445643 | 0.440544 | -0.005098 | -1.144038 | 0.210599 | 0.195953 | 33.915516 | 28.545898 |

Plan-level minimum requirement support:

| Minimum requirement support | Plans | Baseline MAE | Winner MAE | Δ MAE | Relative Δ % | Baseline bias | Winner bias | Improved % | Worsened % |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| missing (0) | 557 | 0.627516 | 0.630878 | 0.003362 | 0.535770 | 0.230703 | 0.241260 | 13.464991 | 15.260323 |
| positive <20 | 310 | 0.423331 | 0.413828 | -0.009503 | -2.244784 | 0.235575 | 0.213872 | 35.806452 | 21.290323 |
| 20-<100 | 1061 | 0.425874 | 0.423905 | -0.001969 | -0.462229 | 0.227038 | 0.220632 | 32.045240 | 26.767201 |
| 100+ | 10785 | 0.448922 | 0.443640 | -0.005282 | -1.176595 | 0.210954 | 0.195538 | 34.130737 | 28.984701 |

Large degree support accounts for all aggregate benefit: 12,310 plans at ≥100 save 62.760343 units; missing degree history adds 1.866426 units, and the seven plans at 20–99 add 0.765756. There are **no positive degree supports below 20 in this holdout**; no empirical conclusion can be drawn for that empty group.

Missing degree histories occur in **396 plans / 1,935 courses**, all in 20251, spanning seven new IDs (`57.111`, `58.111`, `59.111`, `60.111`, `61.111`, `64.111`, `65.111`). Their plan MAE worsens by +0.004713, bias rises by +0.013771, and 81.82% of plans are unchanged. The seven 20–99-support plans are degree `16.111`; their +0.109394 deterioration is too sparse to extrapolate broadly.

The benefit is not confined to large **requirement** support: 310 plans with minimum requirement support below 20 improve by −0.009503, while 557 with any missing requirement history worsen by +0.003362. Using mean requirement support instead yields +0.012595 for the 140 plans at 20–99 and −0.005221 for the 12,175 at ≥100; mixed-support plans make aggregation choice matter.

Course-level support evidence:

| History level | Support | Courses | Baseline mark MAE | Winner mark MAE | Baseline points MAE | Winner points MAE |
| --- | --- | --- | --- | --- | --- | --- |
| degree | missing (0) | 1935 | 14.151980 | 14.226591 | 0.842506 | 0.844315 |
| degree | positive <20 | 0 | N/A | N/A | N/A | N/A |
| degree | 20-<100 | 44 | 9.577376 | 10.054315 | 0.659091 | 0.676136 |
| degree | 100+ | 65557 | 9.576606 | 9.501299 | 0.568101 | 0.565386 |
| degree x requirement | missing (0) | 2114 | 13.895173 | 13.950011 | 0.824267 | 0.824740 |
| degree x requirement | positive <20 | 462 | 10.024450 | 9.776391 | 0.574675 | 0.565476 |
| degree x requirement | 20-<100 | 2409 | 9.831278 | 9.805139 | 0.552408 | 0.548568 |
| degree x requirement | 100+ | 62551 | 9.559077 | 9.483780 | 0.568552 | 0.565974 |

**Smoothing:** K=20. Degree means shrink toward prior global means; degree×requirement means shrink toward the already smoothed degree mean. With missing degree history, both use the global fallback. At support 1, the prior contributes 20/21 (95.24%); at 20 it contributes 50%; at 100 it contributes 16.67%. This gives a coherent fallback and prevents an unshrunk single outcome from defining a mean. It **does not guarantee** baseline-equivalent predictions: the winner is a different fitted model with additional inputs. Missing-history bias worsens, so smoothing's statistical protection is not sufficient evidence of production reliability for new degrees.

The winner's ten specialty inputs together account for 6.169484% of LightGBM gain. `degree_history_missing` has no splits; `degree_requirement_history_missing` has one. These are descriptive fitted-model statistics, not causal feature contributions or a reason to remove features.

**Sequential-history effect / association:** course-row-weighted support distributions:

| Part | Support feature | Course rows | Mean | Min | P25 | Median | P75 | P95 | Max | Missing rows |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20251 | degree_history_effective_support | 34408 | 15634.292163 | 0.000000 | 2969.000000 | 8779.000000 | 15546.000000 | 50301.250000 | 50301.250000 | 1935 |
| 20251 | degree_requirement_history_effective_support | 34408 | 10640.595995 | 0.000000 | 1331.000000 | 2790.000000 | 12565.500000 | 47042.250000 | 47042.250000 | 1937 |
| 20252 | degree_history_effective_support | 33128 | 17402.075623 | 73.000000 | 4663.000000 | 12935.000000 | 15599.000000 | 53468.250000 | 53468.250000 | 0 |
| 20252 | degree_requirement_history_effective_support | 33128 | 11498.318507 | 0.000000 | 1806.750000 | 4462.000000 | 10255.000000 | 50181.250000 | 50181.250000 | 177 |

| History missing coverage | 20251 | 20252 |
| --- | --- | --- |
| Degree missing courses | 1,935 / 34,408 (5.624%) | 0 / 33,128 (0%) |
| Requirement missing courses | 1,937 / 34,408 (5.629%) | 177 / 33,128 (0.534%) |
| Degree missing plans | 396 / 6,469 (6.122%) | 0 / 6,244 (0%) |
| Any requirement missing plans | 398 / 6,469 (6.152%) | 159 / 6,244 (2.546%) |

The degree median support increases 8,779 → 12,935; the requirement median increases 2,790 → 4,462. Every matched degree/requirement key has nonnegative support growth. Distribution means/quantiles also reflect different course mixes, so they should not be read as a pure update effect.

Among the **high degree-support** plans, 20251 improves by −0.013430 (6,069 plans), while 20252 worsens by +0.003004 (6,241). Thus the semester regression is not explained solely by the seven sparse-degree plans or missing histories. More support is associated with the later semester, **but not with greater global benefit**. Across 48 shared degree IDs, correlation between support growth and (20252 Δ −20251 Δ) is Pearson +0.154193 / Spearman +0.201216; weak positive association here means larger growth tends toward a less favorable delta change. This descriptive correlation does not establish causality, control for curriculum/student shifts, or estimate a frozen-versus-updated counterfactual.

Validation-history coverage can be reconstructed, but validation subgroup predictions cannot: in 2023 there are 5,648 missing-degree rows and 442 positive degree supports <20; in 2024 there are no missing-degree rows or positive degree supports <20. The saved validation aggregate metrics cannot establish smoothing performance on those subgroups.

## 11. Course-Level Accuracy

| Metric | Baseline | Winner | Δ |
| --- | --- | --- | --- |
| Mark MAE | 9.707698 | 9.637045 | -0.070652 |
| Mark RMSE | 13.045276 | 12.936378 | -0.108898 |
| Mark bias | 2.265171 | 1.971955 | -0.293216 |
| Mark within ±5, % | 34.997631 | 35.145700 | 0.148069 |
| Mark within ±10, % | 62.588842 | 62.716181 | 0.127339 |
| Course points MAE | 0.576022 | 0.573450 | -0.002573 |
| Course points RMSE | 0.839027 | 0.834521 | -0.004506 |
| Course points bias | 0.173282 | 0.158575 | -0.014707 |

All measures use the same 67,536 course IDs and actual marks/points. Global mark MAE improves by 0.070652 (0.73%) and course-points MAE by 0.002573 (0.45%); both RMSEs and mark bias improve. There is no global course-quality deterioration hidden by plan aggregation.

The semester reversal also exists at course level:

| Part | Courses | Baseline mark MAE | Winner mark MAE | Baseline points MAE | Winner points MAE |
| --- | --- | --- | --- | --- | --- |
| 20251 | 34408 | 10.287690 | 10.116281 | 0.603581 | 0.595813 |
| 20252 | 33128 | 9.105295 | 9.139293 | 0.547399 | 0.550222 |

20252 mark MAE increases +0.033998 (0.37%) and points MAE +0.002823 (0.52%). The regression is small, but supports the plan-level semester finding rather than an aggregation-only explanation.

## 12. Bias Analysis

Overall plan bias falls **+0.213762 → +0.200083**, reduction **0.013679 / 6.40%**. Overprediction remains substantial. In 20251 it falls **+0.284468 → +0.256973** (−0.027495); in 20252 it rises **+0.140509 → +0.141143** (+0.000634).

Degree and GPA-band bias values are shown completely in sections 7 and 8 and saved in their tables. The winner does not uniformly correct calibration:

- Degree `40.111`, **670 plans**, bias **+0.072678 → +0.184424** (+0.111745), even though MAE Δ +0.001072 is descriptively approximately unchanged.
- Degree `45.111`, 161 plans, bias **+0.244249 → +0.289390**; degree `65.111`, 178 plans, **+0.294843 → +0.337380**.
- GPA=0 and GPA (0,1] overprediction are unchanged/slightly worse; high-GPA underprediction becomes more negative.
- GPA (2,3] bias moves **+0.019247 → −0.001094**, near zero, alongside improved MAE.

Therefore the global MAE gain is accompanied by an overall bias reduction, but it is not a broad calibration repair. Degree `40.111` is a material local warning that a small MAE delta can conceal systematic drift.

## 13. Tail / Extreme Error Analysis

| Model | P90 AE | P95 AE | P99 AE | Max AE | AE >1 | AE >1.5 | AE >2 | AE >2.5 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 1.038462 | 1.375000 | 2.067500 | 3.250000 | 1333 | 478 | 145 | 46 |
| selected | 1.025000 | 1.362121 | 2.035429 | 3.250000 | 1302 | 465 | 132 | 34 |

Global tails improve at P90/P95/P99 and all requested thresholds; maximum error remains 3.25. There is **no aggregate increase in tail risk**. Threshold crossings still include individual newly severe cases:

| AE threshold | Baseline-only above (repaired) | Winner-only above (new) | Both above |
| --- | --- | --- | --- |
| 1.000000 | 108 | 77 | 1225 |
| 1.500000 | 36 | 23 | 442 |
| 2.000000 | 19 | 6 | 126 |
| 2.500000 | 13 | 1 | 33 |

Among the top 20 baseline errors: 5 improve, 1 worsens, 14 are unchanged. Among the top 20 selected errors: 4 improve, 2 worsen, 14 are unchanged. **All 40 displayed rows have actual GPA=0**; many are the same cases. The maximum and several worst zero-GPA cases remain untouched.

Case IDs below are local audit row references; their original student/degree/part keys are retained in the local paired/extreme Parquet files. No student identifiers are included in this Markdown table.

Top 20 baseline errors:

| Rank | Case | Degree | Part | Courses | Credits | Actual GPA | Baseline AE | Winner AE | Δ AE | Direction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 | 2.111 | 20252 | 1 | 3.000000 | 0.000000 | 3.250000 | 3.250000 | 0.000000 | unchanged |
| 2 | 2 | 41.111 | 20251 | 3 | 7.000000 | 0.000000 | 3.178571 | 3.178571 | 0.000000 | unchanged |
| 3 | 3 | 41.111 | 20251 | 4 | 10.000000 | 0.000000 | 3.150000 | 3.150000 | 0.000000 | unchanged |
| 4 | 4 | 40.111 | 20252 | 2 | 5.000000 | 0.000000 | 3.100000 | 3.100000 | 0.000000 | unchanged |
| 5 | 5 | 41.111 | 20251 | 3 | 9.000000 | 0.000000 | 3.083333 | 3.166667 | 0.083333 | worsened |
| 6 | 6 | 2.111 | 20251 | 1 | 3.000000 | 0.000000 | 3.000000 | 3.000000 | 0.000000 | unchanged |
| 7 | 7 | 41.111 | 20251 | 1 | 2.000000 | 0.000000 | 3.000000 | 3.000000 | 0.000000 | unchanged |
| 8 | 8 | 41.111 | 20251 | 1 | 2.000000 | 0.000000 | 3.000000 | 3.000000 | 0.000000 | unchanged |
| 9 | 9 | 41.111 | 20251 | 2 | 4.000000 | 0.000000 | 3.000000 | 3.000000 | 0.000000 | unchanged |
| 10 | 10 | 2.111 | 20252 | 1 | 3.000000 | 0.000000 | 3.000000 | 2.750000 | -0.250000 | improved |
| 11 | 11 | 2.111 | 20252 | 1 | 3.000000 | 0.000000 | 3.000000 | 2.750000 | -0.250000 | improved |
| 12 | 12 | 2.111 | 20252 | 1 | 3.000000 | 0.000000 | 3.000000 | 3.000000 | 0.000000 | unchanged |
| 13 | 13 | 2.111 | 20252 | 1 | 3.000000 | 0.000000 | 3.000000 | 3.000000 | 0.000000 | unchanged |
| 14 | 14 | 2.111 | 20252 | 1 | 3.000000 | 0.000000 | 3.000000 | 3.000000 | 0.000000 | unchanged |
| 15 | 15 | 11.111 | 20252 | 4 | 12.000000 | 0.000000 | 3.000000 | 3.000000 | 0.000000 | unchanged |
| 16 | 16 | 34.111 | 20252 | 1 | 4.000000 | 0.000000 | 3.000000 | 3.000000 | 0.000000 | unchanged |
| 17 | 17 | 41.111 | 20251 | 5 | 15.000000 | 0.000000 | 2.866667 | 2.766667 | -0.100000 | improved |
| 18 | 18 | 41.111 | 20251 | 4 | 13.000000 | 0.000000 | 2.846154 | 2.769231 | -0.076923 | improved |
| 19 | 19 | 41.111 | 20251 | 4 | 13.000000 | 0.000000 | 2.826923 | 2.826923 | 0.000000 | unchanged |
| 20 | 20 | 11.111 | 20251 | 1 | 4.000000 | 0.000000 | 2.750000 | 2.500000 | -0.250000 | improved |

Top 20 selected errors:

| Rank | Case | Degree | Part | Courses | Credits | Actual GPA | Baseline AE | Winner AE | Δ AE | Direction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 | 2.111 | 20252 | 1 | 3.000000 | 0.000000 | 3.250000 | 3.250000 | 0.000000 | unchanged |
| 2 | 2 | 41.111 | 20251 | 3 | 7.000000 | 0.000000 | 3.178571 | 3.178571 | 0.000000 | unchanged |
| 3 | 5 | 41.111 | 20251 | 3 | 9.000000 | 0.000000 | 3.083333 | 3.166667 | 0.083333 | worsened |
| 4 | 3 | 41.111 | 20251 | 4 | 10.000000 | 0.000000 | 3.150000 | 3.150000 | 0.000000 | unchanged |
| 5 | 4 | 40.111 | 20252 | 2 | 5.000000 | 0.000000 | 3.100000 | 3.100000 | 0.000000 | unchanged |
| 6 | 6 | 2.111 | 20251 | 1 | 3.000000 | 0.000000 | 3.000000 | 3.000000 | 0.000000 | unchanged |
| 7 | 7 | 41.111 | 20251 | 1 | 2.000000 | 0.000000 | 3.000000 | 3.000000 | 0.000000 | unchanged |
| 8 | 8 | 41.111 | 20251 | 1 | 2.000000 | 0.000000 | 3.000000 | 3.000000 | 0.000000 | unchanged |
| 9 | 9 | 41.111 | 20251 | 2 | 4.000000 | 0.000000 | 3.000000 | 3.000000 | 0.000000 | unchanged |
| 10 | 12 | 2.111 | 20252 | 1 | 3.000000 | 0.000000 | 3.000000 | 3.000000 | 0.000000 | unchanged |
| 11 | 13 | 2.111 | 20252 | 1 | 3.000000 | 0.000000 | 3.000000 | 3.000000 | 0.000000 | unchanged |
| 12 | 14 | 2.111 | 20252 | 1 | 3.000000 | 0.000000 | 3.000000 | 3.000000 | 0.000000 | unchanged |
| 13 | 15 | 11.111 | 20252 | 4 | 12.000000 | 0.000000 | 3.000000 | 3.000000 | 0.000000 | unchanged |
| 14 | 16 | 34.111 | 20252 | 1 | 4.000000 | 0.000000 | 3.000000 | 3.000000 | 0.000000 | unchanged |
| 15 | 24 | 10.111 | 20251 | 1 | 4.000000 | 0.000000 | 2.750000 | 3.000000 | 0.250000 | worsened |
| 16 | 19 | 41.111 | 20251 | 4 | 13.000000 | 0.000000 | 2.826923 | 2.826923 | 0.000000 | unchanged |
| 17 | 18 | 41.111 | 20251 | 4 | 13.000000 | 0.000000 | 2.846154 | 2.769231 | -0.076923 | improved |
| 18 | 17 | 41.111 | 20251 | 5 | 15.000000 | 0.000000 | 2.866667 | 2.766667 | -0.100000 | improved |
| 19 | 10 | 2.111 | 20252 | 1 | 3.000000 | 0.000000 | 3.000000 | 2.750000 | -0.250000 | improved |
| 20 | 11 | 2.111 | 20252 | 1 | 3.000000 | 0.000000 | 3.000000 | 2.750000 | -0.250000 | improved |

Sensitivity to a few extreme plans: excluding the top 20 baseline errors leaves Δ **−0.004671**; excluding the top 100 leaves **−0.004376**. Thus isolated worst-error outliers do not create the global gain.

By baseline-error magnitude:

| Baseline AE band | Plans | Baseline MAE | Winner MAE | Δ MAE | Total error Δ |
| --- | --- | --- | --- | --- | --- |
| (0.25,0.50] | 3105 | 0.378027 | 0.365421 | -0.012606 | -39.141834 |
| (0.50,1.00] | 2687 | 0.717060 | 0.703584 | -0.013476 | -36.209305 |
| <=0.25 | 5588 | 0.124584 | 0.132868 | 0.008284 | 46.291610 |
| >1.00 | 1333 | 1.483531 | 1.460224 | -0.023307 | -31.068631 |

About 31.068631 saved units (51.67% of net savings) occur among 1,333 baseline errors >1, but thousands of moderate-error plans also improve. Already accurate plans (baseline AE≤0.25) collectively worsen by 46.291610 units. This partition is post hoc and selected by baseline error, so it describes error redistribution rather than a deployable routing rule. The stronger concentration issue is **degrees**, not a handful of anomalous plans.

## 14. Direct-Points Experiments

| Variant | 2023 MAE | 2024 MAE | Mean MAE | Δ vs baseline 2023 | Δ vs baseline 2024 |
| --- | --- | --- | --- | --- | --- |
| degree_history_points_credit_weighted | 0.404111 | 0.428324 | 0.416217 | -0.003718 | 0.002497 |
| degree_history_points_temporal | 0.403876 | 0.428778 | 0.416327 | -0.003953 | 0.002951 |
| points_temporal | 0.405133 | 0.430604 | 0.417868 | -0.002696 | 0.004777 |
| points_credit_weighted | 0.405491 | 0.432772 | 0.419131 | -0.002338 | 0.006945 |
| degree_id_points_temporal | 0.406112 | 0.433427 | 0.419769 | -0.001717 | 0.007600 |
| degree_id_points_credit_weighted | 0.406382 | 0.435534 | 0.420958 | -0.001446 | 0.009707 |

All six direct-points variants improve Plan GPA MAE in 2023 and worsen it in 2024. Degree-history points variants have favorable two-year means (−0.000501 unweighted, −0.000611 credit-weighted), but each fails the established improve-both-folds requirement. Degree-ID points and plain points have unfavorable two-year means.

Direct points also show a different metric tradeoff: every direct-points variant has lower 2023 plan RMSE (roughly 0.561–0.566 vs baseline 0.579250), and several have lower mean RMSE, while their 2024 MAE and within-±0.50 rates deteriorate. Lower RMSE/bias alone does not satisfy the existing objective.

**Assessment:** a year-dependent signal exists, especially for degree-history points, but **no consistent MAE signal across years** supports promotion now. Retain as optional research; current evidence does not require a new experiment, and none was run. Only the selected winner has 2025 experimental predictions; no nonselected direct-points model was evaluated on 2025 here.

## 15. Credit-Weighting Experiments

Δ below means credit-weighted variant − its corresponding unweighted variant (not −baseline):

| Unweighted variant | Credit-weighted variant | Δ 2023 | Δ 2024 | Mean Δ |
| --- | --- | --- | --- | --- |
| baseline_mark_temporal | mark_credit_weighted | -0.000390 | 0.000404 | 0.000007 |
| points_temporal | points_credit_weighted | 0.000358 | 0.002167 | 0.001263 |
| degree_history_points_temporal | degree_history_points_credit_weighted | 0.000235 | -0.000455 | -0.000110 |
| degree_id_points_temporal | degree_id_points_credit_weighted | 0.000271 | 0.002108 | 0.001189 |

Mark credit weighting has opposite signs by fold and virtually zero mean gain (+0.000007). Plain-points and degree-ID-points weighting worsen both folds. Degree-history-points weighting slightly worsens 2023 and slightly improves 2024, with a tiny mean reduction (−0.000110). There is **no consistently beneficial credit-weighting pattern** in the current catalog. A degree-history-mark credit-weighted counterpart does not exist in the saved catalog, so that specific pair cannot be assessed.

These are training-weight comparisons. They must not be confused with credit-weighted plan aggregation, which all variants already use, or the diagnostic credit-weighted evaluation MAE.

## 16. Degree ID vs Degree History

| Variant | 2023 MAE | 2024 MAE | Mean MAE | Δ 2023 | Δ 2024 |
| --- | --- | --- | --- | --- | --- |
| degree_history_mark_temporal | 0.406947 | 0.422909 | 0.414928 | -0.000882 | -0.002918 |
| baseline_mark_temporal | 0.407829 | 0.425827 | 0.416828 | 0.000000 | 0.000000 |
| degree_id_mark_temporal | 0.408965 | 0.427252 | 0.418108 | 0.001136 | 0.001425 |

Adding degree identity alone worsens both folds (+0.001136, +0.001425); adding the ten smoothed historical-behavior features improves both (−0.000882, −0.002918). Within the existing candidates, **historical behavior is the more useful signal**. This does not prove degree identity is inherently useless or isolate a causal mechanism; fitting/early-stopping choices and different feature profiles are part of each variant. There is no saved 2025 degree-ID prediction artifact for a fresh paired holdout comparison.

## 17. Robustness / Bootstrap

Paired student-cluster bootstrap: 2,000 replicates, `numpy.random.default_rng(42)`. There are **7,019 student clusters**: 1,325 with one evaluated plan and 5,694 with two. Each student has one degree ID in this holdout. Sample 7,019 student IDs with replacement; include every sampled student's full set of plans, including both semesters, and retain multiplicity. For replicate b, compute `sum(cluster absolute-error deltas) / sum(cluster plan counts)`. This preserves plan-weighted MAE while respecting within-student repetition; it is not course-row resampling or an equally weighted average of student MAEs.

The same method is also applied within each semester (one plan per student there):

| Segment | Student clusters | Plans | Observed Δ | Bootstrap mean Δ | 95% CI low | 95% CI high | Bootstrap fraction Δ<0 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| overall | 7019 | 12713 | -0.004730 | -0.004724 | -0.006256 | -0.003231 | 1.000000 |
| 20251 | 6469 | 6469 | -0.012276 | -0.012277 | -0.014079 | -0.010423 | 1.000000 |
| 20252 | 6244 | 6244 | 0.003089 | 0.003098 | 0.000740 | 0.005467 | 0.005000 |

The global empirical share is **2,000/2,000 = 100%**. For 20252 it is **10/2,000 = 0.5%**, and its CI is positive. Both the global improvement and the later-semester regression are stable under this resampling scheme. This is **not formal causal significance**, a calibrated probability that the winner is better, or proof of future performance. It is conditional sampling robustness for fixed predictions. Two calendar semesters, degree-wide shocks, model-training uncertainty, selection among variants and future distribution shift are not fully represented by student-only resampling.

Minimal reproduction from the paired output:

```python
clusters = paired.groupby("student_id", sort=True).delta_absolute_error.agg(["sum", "count"])
sums = clusters["sum"].to_numpy(float)
counts = clusters["count"].to_numpy(float)
rng = np.random.default_rng(42)
draws = []
for _ in range(2000):
    idx = rng.integers(0, len(clusters), size=len(clusters))
    draws.append(sums[idx].sum() / counts[idx].sum())
ci = np.quantile(draws, [0.025, 0.975])
share = np.mean(np.asarray(draws) < 0)
```

Full draws are saved in `bootstrap_samples.parquet`; summary and methodology are in `bootstrap_summary.parquet` and `audit_summary.json`.

## 18. Production Complexity

**Incremental complexity: MODERATE.** Saved model sizes and feature counts:

| Model | Model features | Trees | Model bytes | Category-level bytes |
| --- | --- | --- | --- | --- |
| baseline | 47 | 114 | 697965 | 568 |
| selected | 57 | 121 | 742299 | 568 |

The winner adds **10 numeric features** (47 →57, +21.28% feature count), **7 trees** (114 →121), and **44,334 bytes** (+6.35% model-file size). Both model files are under 1 MB and category-level files are the same size. No latency, memory or large benchmark was run; file size/tree counts are not a measured runtime cost.

Extra inputs, all required in the winner's saved feature order:

| Degree history | Degree × requirement history |
| --- | --- |
| degree_history_avg_mark | degree_requirement_history_avg_mark |
| degree_history_fail_rate | degree_requirement_history_fail_rate |
| degree_history_avg_points | degree_requirement_history_avg_points |
| degree_history_effective_support | degree_requirement_history_effective_support |
| degree_history_missing | degree_requirement_history_missing |

Serving needs `degree_id` and `plan_requirement_type_id` for lookups, the same temporal weighting/smoothing as training, explicit finalized cutoffs and valid unknown-history fallback. A mark-target winner still requires `predicted_mark` clipping and the existing GradeScale mark-to-points conversion before GPA aggregation.

What must be stored for production, if adopted:

1. Versioned V2 winner grade model, its **57-feature ordered regressor contract**, category levels, training cutoff, target=`mark`, dataset/version/signature provenance and grade-scale provenance.
2. A **FrozenSpecialtyHistory** snapshot with `as_of_part`, **global**, **degree**, and **(degree, requirement)** totals. Each aggregate stores `history_count`, `history_mark_sum`, `history_fail_sum`, `history_points_sum`; retain K=20 and pre-2022=0.25 / later=1 weighting in versioned metadata so inference reproduces the same means.
3. The paired base course-history state at the **same cutoff**, along with source hashes, exact finalized source row IDs/counts, source-semester coverage, `finalized_through_part`, format/feature versions and artifact SHA-256 hashes. Use immutable `data/artifacts/history/as_of_<part>/` bundles and never overwrite an old version.
4. After each newly finalized semester, build a new snapshot from a deduplicated finalized outcome prefix, validate and save it, then use it for the next target semester. This updates the **history**, not necessarily model weights. Never use outcomes from the target/future semester.

Much of the base course-history machinery already exists for the baseline; the incremental burden is specialty outcome labels/totals, hierarchy joins, provenance and lifecycle parity. The existing bundle builder supports specialty history only through the **explicit** `specialty_history_type=FrozenSpecialtyHistory` hook in `build_frozen_history()` / `load_frozen_history()`. The current standalone build-frozen-history CLI supplies no specialty type and reads no `points`/`is_fail`; its default output is a base bundle, insufficient for this winner.

**Available bundles are not V2-ready evidence:** the existing `as_of_20243` / `as_of_20251` metadata references unsuffixed **V1 feature sources** with 365,585 /400,507 prefix outcomes. This audit's V2 prefixes contain **356,816 /391,224** rows. Their cutoff names and feature-engineering-version=2 do not establish the same dataset cohort. Reusing them for this winner without source-equivalence verification would break the evaluated history contract. No bundle was rebuilt or modified here.

**Recommendation boundary:** `src/recommendation/artifacts.py` loads unsuffixed experiment/model paths, explicitly rejects a selected target other than `points`, and `engine.py` clips its model output directly to 0–4. Plugging this **mark** model into that loader would either be rejected or, if guards were bypassed, misinterpret marks as points. Promotion of a grade-regression baseline therefore does not automatically authorize or implement a recommendation switch.

Because lookup/serialization infrastructure already exists, model size is not the main barrier. Operational parity and the current evidence gaps are harder to justify for a gain limited mainly to one semester and a few degrees.

## 19. Risks and Limitations

**Brief history-leakage audit:**

| Required rule | Current evidence |
| --- | --- |
| Training rows exclude their own part | `_prior_aggregates()` computes ordered cumulative totals minus the whole current-part aggregate; all rows of the part see the same prior prefix. Poisoning tests cover own/future labels. |
| 20251 specialty history excludes 20251/20252 outcomes | Sequential merge filters `source.part_id < current_part` and applies history before appending current finalized rows. Initial train maximum =20243. |
| 20252 includes finalized 20251 | The 20251 rows are appended only after applying 20251 history; metadata records 20252 cutoff=20251. |
| 20252 excludes 20252 outcomes | Strict prior-part filtering; poisoning 20252 labels leaves all held-out specialty features unchanged. |
| Finalization and serving cutoff contract | Frozen builder requires explicit finalization attestation; frozen apply rejects target≤as_of; paired base/specialty cutoff validation is enforced. |

Real-artifact prefix check: independently build in-memory `FrozenSpecialtyHistory` from the explicit finalized prefix and compare **all ten specialty features** with sequential reconstruction:

| Target part | History max part | Prior outcome rows | Target course rows | Maximum feature difference |
| --- | --- | --- | --- | --- |
| 20251 | 20243 | 356816 | 34408 | 0.000000 |
| 20252 | 20251 | 391224 | 33128 | 0.000000 |

Both comparisons are exact (max difference zero). This supports the stated 20251←20243 and 20252←20251 timing. Recorded labels are treated as finalized outcomes according to the existing pipeline contract; this audit cannot independently certify external registrar finalization.

Fresh focused verification, run without pytest cache and without Python bytecode writes:

```powershell
.\.venv\Scripts\python.exe -B -m pytest tests/test_feature_pipeline.py tests/test_specialty_history_sequential.py tests/test_degree_points_experiment.py tests/test_frozen_history.py -q -p no:cacheprovider
```

**Result: 29 passed, 6 subtests passed, no failures or skips (7.49s).** The suites exercise the public feature-building flow, specialty prior/current/future poisoning, sequential application, new-degree fallbacks, frozen cutoff/source/immutability contracts and cache boundaries. They do not train production models. No full-suite run was needed for this report/table-only task; these results are not a claim that every unrelated test passed.

Remaining limitations affecting the decision:

- Only two 2025 semesters are available, and their effect signs differ. Student bootstrap cannot establish future-semester stability.
- Degree concentration and improving mid-GPA bands mean the global average is not a general per-degree or per-student guarantee.
- Zero/very-low/high GPA and missing-history subgroup findings remain descriptive. Sparse groups, especially the seven 20–99-degree-support plans, cannot support reliable generalization. No performance data exists for holdout degree support 1–19.
- Global bias and tails improve, but some degrees' bias worsens materially; new >2.5-error cases still occur. No calibration or fail-risk behavior was changed or separately claimed improved.
- Plans represent observed scored registrations, including partial-credit coverage; prediction accuracy does not show that alternative recommended plans improve realized student GPA.
- The winner has a different final boosting-round count; this is the actual selected-model comparison, not a controlled causal ablation of ten features alone.
- Validation raw predictions are unavailable for paired subgroup/resampling analysis. The aggregate improve-both-folds signal is small, and student-cluster CI is conditional on saved fixed models.
- This was a focused specialty-history timing check, not certification of every upstream cohort-selection, raw-label or administrative-data process.
- Future validation should remain prospectively defined. These 2025 observations should not be recycled as untouched evidence for newly tuned variants or routing thresholds.

Analysis outputs: **30 Parquet tables**, `audit_summary.json` and `source_manifest.json` under the new `decision_audit/` directory. The primary paired tables retain local identifiers to make joins auditable; no commit or external sharing was performed. All existing inputs/outputs were protected by content hashes.

## 20. Decision

```text
DECISION: KEEP EXPERIMENTAL
```

Why:

1. **The benefit is real within these artifacts, but not semester-stable.** Exact paired/inference reproduction gives −0.004730 /−1.04% global MAE with negative bootstrap CI; 20252 instead has +0.003089 MAE with a positive semester CI. More available history does not produce greater benefit.
2. **The gain is concentrated rather than broad.** Three degrees contribute 91.16% of net savings; the unweighted degree mean is positive; removing five favored degrees reverses the mean comparison. A majority of well-supported degrees avoids material regression, but only 9/25 improves materially.
3. **Important unresolved segments remain.** GPA=0 overprediction persists, very-low/high-GPA and small-load groups regress, missing-history performance does not improve, and degree `40.111` has sizable positive-bias growth. Sparse/new-degree protection is not established.
4. **The engineering burden is manageable but premature.** Course accuracy, global bias and tails favor retaining the experiment; however V2 specialty-history snapshots and target-aware serving integration remain necessary. These costs are hard to justify as a general baseline change before broader evidence exists.

If promoted later — exactly what must change in the main pipeline (not executed):

1. Add explicit versioned specialty-history enrichment for the **grade regressor** using the already evaluated prior-part / sequential protocol, K=20, current temporal weights, identical target and credit-weighting setting. Keep base `features/` and `modeling/` independent of `experiments/` by using an explicit injected/shared history provider with a documented stable contract; do not add an implicit experiment import to the base layers.
2. In `src/features/feature_contract.py` and `src/modeling/train_models.py`, give the grade regressor its own **57-feature contract and matrix**; preserve the current **47-feature fail-classifier** contract/matrix. Blindly expanding the shared `BASE_FEATURES` would change a second model outside the evidence from this experiment. Preserve the existing validation/final-round selection procedures and record per-model target, feature order, categories and provenance in official V2 metadata. Do not hard-code 121 as the rule for future fits.
3. In `src/evaluation/evaluate_plan_gpa.py`, `src/evaluation/analyze_model_errors.py` and the artifact bindings in `src/paths.py`, bind official V2 grade-model evaluation to that regressor contract and explicit specialty history. Keep target=`mark`, mark clipping, GradeScale conversion and plan formulas intact; preserve the present baseline artifact/evaluation for traceable paired comparisons and rollback.
4. Build and verify new immutable **V2-cohort** base/specialty bundles at the required cutoffs from finalized outcomes, and update history after each finalized semester. Existing V1-derived bundles must not be assumed interchangeable. Store the artifacts/metadata listed in section 18.
5. Treat any recommendation migration as a separate explicit change: its current loader/predictor expects V1 direct points. A mark-target adapter must perform the existing grade-scale conversion and preserve ranking/risk behavior; merely substituting the model file is invalid. This audit authorizes none of those changes.

If not promoted — evidence still missing:

- A prospectively evaluated later finalized semester demonstrating benefit beyond 20251, using the same frozen model/selection contract and an appropriately updated history snapshot.
- A broader degree-level benefit that survives concentration checks, and acceptable paired bias for the well-supported regressing degrees, especially `40.111` calibration and `45.111` MAE/bias.
- Adequate new/sparse-degree and missing-requirement evidence, with student-level paired uncertainty on those groups rather than seven-plan relative percentages.
- Stability for zero/very-low/high GPA and small-load cases, plus validation subgroup predictions sufficient to determine whether these patterns were present before 2025.
- Demonstrated V2 serving-history/model/target compatibility and a small operational parity check. No large benchmark is required by the current evidence.

No modeling or recommendation adoption was made. Preserve `degree_history_mark_temporal` as the selected experimental candidate and retain the official baseline until these evidence gaps are addressed.
