# Student Academic Progress Feature Audit and Ablation


Date: 2026-10-10. Audit status: **PARTIAL**. Experimental matrix: **COMPLETE**. Final recommendation: **KEEP_ALL** for now. Production action: retain the existing four features pending a separately approved simplification decision.


## 1. Executive Summary


Executed 108 outer ablation fits (nine configurations × six model tasks/profiles × two years) and 36 baseline-only inner tuning fits on existing V2 tables. No new 2025 model evaluation occurred. Source/alias/join checks, empirical statistics, Plan GPA, paired uncertainty, subgroup analysis, importance and fixed-candidate sensitivity are recorded. University view definitions, snapshot mutability and official cumulative-GPA denominators are **UNVERIFIED**, so the audit cannot receive an unconditional PASS.


High aggregate correlation does not imply equivalence: on 356,816 training course rows, start versus registration credits correlate 0.898350 (Spearman 0.935258), but are exactly equal on only 27.3968%; course counts correlate 0.901001 and are equal on 28.2173%. No deterministic mapping between any pair was found. Removing explicit inputs leaves `prior_fail_credit_ratio` and other progress/GPA proxies intact.


Variant C (registered credits only), equal-weight mean across the two validation folds:

| model | grade_mae | grade_delta_pct | plan_gpa_mae | plan_delta_pct | log_loss | logloss_delta_pct |
| --- | --- | --- | --- | --- | --- | --- |
| 47_grade | 9.56025 | 0.0880298 | 0.417385 | 0.0319216 | — | — |
| 47_fail | — | — | — | — | 0.228025 | 0.149711 |
| 33_grade | 9.53373 | 0.122052 | 0.417454 | 0.202412 | — | — |
| 33_fail | — | — | — | — | 0.228134 | 0.0861673 |
| 47_points | — | — | 0.418988 | 0.242316 | — | — |
| 57_degree_history_grade | 9.54274 | 0.183034 | 0.416439 | 0.185057 | — | — |


These fold means are descriptive; the actual per-fold results and student-cluster confidence intervals govern interpretation. They do not establish official denominator correctness or counterfactual ranking quality.


## 2. Feature Definitions

| Model input | Raw view column | Transformation | Supported interpretation |
| --- | --- | --- | --- |
| start_total_in_credits | start_total_in_credits | float; direct status join | Source start credit counter; earned/passed/GPA-counted rules UNVERIFIED |
| start_total_in_courses | start_total_in_courses | integer; direct status join | Source start course counter; inclusion/repeats rules UNVERIFIED |
| prior_total_reg_credits | total_reg_credits | float; exact direct alias, no shift | Code treats cumulative registration credits as prior state; official rules UNVERIFIED |
| prior_total_reg_courses | total_reg_courses | integer; exact direct alias, no shift | Code treats cumulative registration course count as prior state; official rules UNVERIFIED |


All four raw fields are doubles in `data/raw/v_add_student_degree_status.parquet` (189,158 physical rows), named by `src/paths.py:35`. The upstream source is the exported view `v_add_student_degree_status`; its underlying tables, SELECT expression, stored procedure and business definitions are absent. Do not relabel any field as earned, passed, attempted or GPA-counted solely from its name.


Source-to-model lineage:


| Raw Source | Cleaning | Feature Engineering | Training Matrix | Model | Recommendation |
|---|---|---|---|---|---|
| `v_add_student_degree_status.start_total_in_credits` | `clean_student_status.py:156–173`, numeric cast, retained | `build_student_course_enriched.py:28–34`, exact `(student,degree,part)` status join | `feature_contract.py:35–38,138–165`, float32 | Official V2 47; shortlist 33; degree-history 57; direct-points research | `inputs.py:133–154,196–199,251–272`; `engine.py:65–82`; `two_stage_engine.py:154–171` |
| `v_add_student_degree_status.start_total_in_courses` | `clean_student_status.py:141–154`, integer cast, retained | Same status join, no cumulative reconstruction | Same ordered numeric contract | Same consumers | Same required snapshot; no substitution from candidate counts |
| `v_add_student_degree_status.total_reg_credits` | `clean_student_status.py:156–173`, numeric cast, retained | `temporal_features.py:316`, direct `prior_total_reg_credits`; ratio at `:319–322` | Same matrix conversion | Same consumers | Snapshot plus local GPA denominator fallback at `engine.py:21–34` |
| `v_add_student_degree_status.total_reg_courses` | `clean_student_status.py:141–154`, integer cast, retained | `temporal_features.py:315`, direct `prior_total_reg_courses`; cold-start counter at `:325–330` | Same matrix conversion | Same consumers | Required current snapshot |


Line references refer to current untouched source. Full evidence: [lineage audit](../scripts/experiments/student_progress_20261010/lineage_audit.md). Outlier checks `clean_outliers.py:201–225` and cleaning initial-GPA fallback `clean_student_status.py:67–84` also depend on these source columns.


## 3. Temporal Availability


| Class | Fields | Finding |
|---|---|---|
| `START_SNAPSHOT` under the implemented contract | `start_agpa_points`, `start_total_in_credits`, `start_total_in_courses`, diploma/catalog properties, explicit `current_gpa_credits` | Exact target-start snapshot; DB immutability, inclusion rules and finalized timing require confirmation |
| `HISTORICAL_STATE` under the implemented contract | `prior_total_reg_*`, `prior_total_fail_*`, `prior_fail_credit_ratio`, earlier GPA, prior registered semesters, course/specialty history | Registration/failure totals are aliases of source start-state totals, not computed shifts; GPA/history apply strict prior-part cutoffs |
| `CURRENT_PLAN` | `plan_*` / `peer_*` context, total candidate credits, course count | Calculated from each proposed combination; no outcome needed |
| `END_OUTCOME` | `final_mark`, `is_fail`, `points`, `gpa_points`, `end_agpa_points`, `end_total_in_*`, semester pass/fail counters, finish fields | Evaluation labels/update inputs only; explicitly excluded from BASE_FEATURES |
| `UNCERTAIN` at DB boundary | Official meaning and mutable/recomputed nature of all four counters; GPA denominator policy | Names and code comments are insufficient to certify the university view |


Empirical timing supports prior registration credits: among 70,054 adjacent clean V2 status transitions, `current total_reg_credits = previous total_reg_credits + previous semester_reg_credits` has one mismatch (0.001427%). Substituting current-semester registration produces 62,302 mismatches (88.9343%). Start credits versus previous end credits differ in 4,158 transitions (5.9354%); course-count registration transitions differ in 1,753 (2.5024%). These discrepancies need business-rule explanations; they are not automatically leakage.


All four training features match clean status on all 356,816 rows. V1/V2 common 2020–2024 status rows (82,300) have zero mismatches for 18 checked fields; V2 adds 5,592 status rows. Definitions/aliases agree on shared rows; cohorts and historical protocols differ. Current training, degree-points experiments and serving actually consume V2, despite stale V1 statements in AGENTS/older pipeline documentation. Source truth: `train_models.py:369–374,416–429`, `degree_points.py:42–48`, `recommendation/artifacts.py:47–51,74–77`.


V2 course history applies then updates each finalized semester: 20251 sees 20243; 20252 sees 20251 (`temporal_features.py:228–270`). Earlier 20251 outcomes may enter 20252 only after finalization. V1 saved metadata uses history frozen after 20243. Student progress snapshots remain separate: publishing a 20251 course-difficulty Delta does not update student GPA/progress for 20252. Existing leakage/version/cutoff guards were preserved. No invalid prediction-time feature was demonstrated; external snapshot semantics remain uncertified.


Exact backend questions: provide the view SQL and base tables for the four columns; list inclusion rules for repeats, failures, withdrawals, transfers, exemptions and flags `in_credits/in_gpa/in_agpa`; confirm whether rows are historical immutable snapshots or recalculated live; state capture/finalization timestamps and degree-transfer rules; explain the transition exceptions; provide the official GPA credit denominator and repeat replacement policy.


## 4. Correlation and Redundancy


Statistical grain matters. Course rows weight semesters by finalized-course count. Unique training status groups number 75,076; their fields are constant within each group. Raw 2020–2024 has 92,741 rows (11 missing per field, 0.011861%); cleaned V2 has 87,892 rows. Training has no missing values for the four fields. Summary statistics below use sample standard deviation.

| dataset | field | rows | missing | missing_pct | unique | mean | median | min | max | std |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| train_v2_course | start_total_in_credits | 356816 | 0 | 0 | 379 | 77.9355 | 73 | 0 | 250 | 55.8228 |
| train_v2_course | start_total_in_courses | 356816 | 0 | 0 | 82 | 28.2012 | 26 | 0 | 81 | 20.2223 |
| train_v2_course | total_reg_credits | 356816 | 0 | 0 | 760 | 95.8677 | 86 | 0 | 495 | 72.052 |
| train_v2_course | total_reg_courses | 356816 | 0 | 0 | 163 | 34.4427 | 31 | 0 | 169 | 25.9649 |


All six training-course pair correlations/equality/difference summaries:

| dataset | a | b | valid | pearson | spearman | exact_equal | equal_tolerance_1e8 | equal_pct | a_minus_b_mean | a_minus_b_median | a_minus_b_min | a_minus_b_max | a_minus_b_std | a_minus_b_unique |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| train_v2_course | start_total_in_credits | start_total_in_courses | 356816 | 0.964593 | 0.984383 | 36071 | 36071 | 10.1091 | 49.7344 | 46 | 0 | 187 | 36.7061 | 278 |
| train_v2_course | start_total_in_credits | total_reg_credits | 356816 | 0.89835 | 0.935258 | 97756 | 97756 | 27.3968 | -17.9322 | -6 | -360 | 103 | 32.8799 | 568 |
| train_v2_course | start_total_in_credits | total_reg_courses | 356816 | 0.866388 | 0.921047 | 35643 | 35643 | 9.98918 | 43.4928 | 39 | -115 | 192 | 35.7606 | 398 |
| train_v2_course | start_total_in_courses | total_reg_credits | 356816 | 0.867078 | 0.922888 | 34287 | 34287 | 9.60915 | -67.6665 | -58 | -433 | 24 | 55.4406 | 712 |
| train_v2_course | start_total_in_courses | total_reg_courses | 356816 | 0.901001 | 0.938036 | 100684 | 100684 | 28.2173 | -6.24151 | -2 | -115 | 35 | 11.7021 | 135 |
| train_v2_course | total_reg_credits | total_reg_courses | 356816 | 0.966697 | 0.984305 | 34091 | 34091 | 9.55422 | 61.425 | 55 | 0 | 367 | 47.4196 | 576 |


At status grain, credit correlation is 0.900141 and equality 24.1569%; course-count correlation 0.896312 and equality 24.9547%. Within degree groups with ≥100 rows, credit correlations range 0.426–0.956 and course correlations 0.433–0.959. Within progress quartiles, ranges shrink to 0.400–0.680 and 0.518–0.700. Overall high correlation partly reflects the shared progress range. Year, degree, progress-quartile distributions, missing percentages, correlations, target relationships and directed deterministic tests are in the [descriptive audit](../scripts/experiments/student_progress_20261010/data_findings.md) and its [CSV evidence](../scripts/experiments/student_progress_20261010/evidence/stratified_pairwise.csv).


The four concepts cannot be collapsed through simple identities: in cleaned V2, start credits equal total passed credits in only about half the rows; registered credits differ from passed+failed credits in 55.3782%. Target relationships even change sign: course-points Pearson is +0.070779 for start credits versus −0.065524 for registered credits; failure correlations are −0.089245 versus +0.000239. Neither low univariate target correlation nor a high interfeature correlation establishes uselessness.


Representative real source records (student keys are SHA-256 pseudonyms, shortened here; no original student/status identifiers):

| reason | student | degree_id | part_id | start_total_in_credits | total_reg_credits | start_total_in_courses | total_reg_courses |
| --- | --- | --- | --- | --- | --- | --- | --- |
| lag_start_end_mismatch | a3f9bb372310 | 2.111 | 20223 | 222 | 413.5 | 60 | 108 |
| lag_start_end_mismatch | 004a82c35509 | 13.111 | 20202 | 28 | 153 | 11 | 61 |
| lag_start_end_mismatch | 004a82c35509 | 13.111 | 20211 | 30 | 165 | 12 | 66 |
| lag_start_end_mismatch | 004a82c35509 | 13.111 | 20212 | 30 | 177 | 12 | 71 |
| lag_start_end_mismatch | 004a82c35509 | 13.111 | 20222 | 35 | 208 | 14 | 83 |
| lag_reg_increment_mismatch | 2159b3f40503 | 8.111 | 20212 | 72 | 93 | 30 | 38 |
| lag_reg_increment_mismatch | f6e7048d31bd | 29.111 | 20232 | 60 | 85 | 22 | 28 |
| lag_reg_increment_mismatch | d92f4b4167c2 | 29.111 | 20233 | 78 | 57 | 28 | 20 |
| lag_reg_increment_mismatch | bf9b40ceb1a0 | 2.111 | 20232 | 242 | 802.5 | 61 | 194 |
| start_vs_reg_difference | a3f9bb372310 | 2.111 | 20202 | 156.5 | 294 | 45 | 78 |
| start_vs_reg_difference | a3f9bb372310 | 2.111 | 20203 | 176 | 318.5 | 49 | 83 |
| start_vs_reg_difference | a3f9bb372310 | 2.111 | 20211 | 184 | 326.5 | 51 | 85 |


The differences demonstrate distinct values, not a verified explanation such as repeated failures or transfers. Raw high extremes are source examples, not necessarily modeling-eligible records. Full pseudonymized records and differences are in [anonymized_examples.csv](../scripts/experiments/student_progress_20261010/evidence/anonymized_examples.csv); pseudonymization is not a guarantee of irreversible anonymity.


## 5. Experimental Setup


Existing `data/features/temporal_train_features_v2.parquet`: 356,816 rows, 20201–20243; SHA-256 `026faac5933709c0903dac1b0ea2ca88be71d55c1bb6f805eb265d0f4cbe204f`. No pipeline rebuild. Outer 2023 fits through 20223; outer 2024 fits through 20233. Inner selection fits through 20213/20223 and validates 2022/2023 respectively. Categories come only from each training frame; weights are 0.25 before 2022 and 1.0 from 2022; seed 42; deterministic CPU LightGBM, four threads.


| Variant | Model-input change only |
|---|---|
| A | Retain all four |
| B | Retain both credits, drop both counts |
| C | Retain only prior_total_reg_credits |
| D | Retain only start_total_in_credits |
| E | Drop all four explicit inputs |
| F1 | Drop start_total_in_credits |
| F2 | Drop start_total_in_courses |
| F3 | Drop prior_total_reg_credits |
| F4 | Drop prior_total_reg_courses |


Six model specifications: 47 grade/fail, 33 grade/fail, 47 unweighted direct points (points_temporal research variant), and 57 unweighted degree-history grade matching the selected research profile. Direct points is not the selected production predictor; existing selected degree-points artifact predicts marks. Other research catalogs, including credit-weighted/direct-points degree-ID combinations, were audited but not all retrained; those are follow-ups if adopted. All remaining model inputs, raw columns and `prior_fail_credit_ratio` stay unchanged.


Nested baseline-only selection compares the existing `balanced_31`, `capaciy_63`, `regularized_47` grid on the inner year. Grade/points configurations are selected by historical Plan GPA MAE; failure by Log Loss. Early stopping uses the existing l1/binary_logloss metric (maximum 900 rounds, patience 75). The selected configuration and tree count are then frozen for A–F in the outer fit. This is a controlled fixed-configuration ablation, not independently tuned variant optimization. Baseline A is a nested retrained reference, not an exact reproduction of saved full-2024 production models.

| year | model | inner_fit_through | inner_validation | candidate | rounds | leaves | min_leaf | feature_fraction | bagging_fraction | L1 | L2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2023 | 47_grade | 20213 | 20221,20222,20223 | regularized_47 | 348 | 47 | 160 | 0.8 | 0.85 | 0.5 | 4 |
| 2023 | 47_fail | 20213 | 20221,20222,20223 | regularized_47 | 116 | 47 | 160 | 0.8 | 0.85 | 0.5 | 4 |
| 2023 | 33_grade | 20213 | 20221,20222,20223 | regularized_47 | 195 | 47 | 160 | 0.8 | 0.85 | 0.5 | 4 |
| 2023 | 33_fail | 20213 | 20221,20222,20223 | regularized_47 | 148 | 47 | 160 | 0.8 | 0.85 | 0.5 | 4 |
| 2023 | 47_points | 20213 | 20221,20222,20223 | regularized_47 | 89 | 47 | 160 | 0.8 | 0.85 | 0.5 | 4 |
| 2023 | 57_degree_history_grade | 20213 | 20221,20222,20223 | regularized_47 | 208 | 47 | 160 | 0.8 | 0.85 | 0.5 | 4 |
| 2024 | 47_grade | 20223 | 20231,20232,20233 | capaciy_63 | 122 | 63 | 100 | 0.85 | 0.9 | 0.2 | 2 |
| 2024 | 47_fail | 20223 | 20231,20232,20233 | regularized_47 | 88 | 47 | 160 | 0.8 | 0.85 | 0.5 | 4 |
| 2024 | 33_grade | 20223 | 20231,20232,20233 | capaciy_63 | 137 | 63 | 100 | 0.85 | 0.9 | 0.2 | 2 |
| 2024 | 33_fail | 20223 | 20231,20232,20233 | regularized_47 | 95 | 47 | 160 | 0.8 | 0.85 | 0.5 | 4 |
| 2024 | 47_points | 20223 | 20231,20232,20233 | capaciy_63 | 75 | 63 | 100 | 0.85 | 0.9 | 0.2 | 2 |
| 2024 | 57_degree_history_grade | 20223 | 20231,20232,20233 | regularized_47 | 136 | 47 | 160 | 0.8 | 0.85 | 0.5 | 4 |


Common parameters: learning rate .04, bagging frequency 1, max_bin 255, deterministic/force_col_wise true. Bagging fraction is .85 or .90 according to the selected candidate. The full parameter dictionaries, categories, ordered keys, dataset/source hashes and per-model feature/config/signature/SHA records are saved. Cache namespaces are isolated. Existing 2025 research results predate this task, so 2025 cannot be represented as a fresh blind holdout; this study performed no new 2025 model metrics or selection.


Repeat the protocol from the root with `.\.venv\Scripts\python.exe -m scripts.experiments.student_progress_20261010.workflow --output-name student_progress_followup`; a fresh isolated namespace is required. An existing output rejects an accidental overwrite. The 144 numerical fits used [executed_workflow.py](../scripts/experiments/student_progress_20261010/evidence/executed_workflow.py), whose SHA matches the recorded setup. Subsequent reusable-runner hardening pins imported implementation sources, authenticates inner selection with run/year/specification/ordered temporal-row context, publishes COMPLETE only after protection checks, and uses complete-plan permutation sampling. These safeguards were not retroactively used for the original fits. The original run did not resume a cache; all 108 saved outer models were independently verified against the archived protocol, exact features/order, categories, configuration, row fingerprints and SHA. The current runner correctly rejects the old namespace on `--resume`; no signatures were migrated and no fits were repeated after hardening. Models: `models/experiments/student_progress_20261010/`. Numerical evidence: `data/evaluation/experiments/student_progress_20261010/`.


## 6. Model Performance


Positive error/Log Loss/Brier differences mean harm; positive AUC differences mean improvement. PR-AUC here is sklearn average precision, matching the existing evaluator; ROC-AUC is omitted in any single-class subgroup. Bias retains its sign, so a relative bias change is not an improvement measure. Detailed [metric_deltas.csv](../data/evaluation/experiments/student_progress_20261010/metric_deltas.csv) contains every absolute and relative change. Equal-weight fold means below do not replace separate folds.

| model | variant | grade_mae | grade_delta_pct | points_mae | plan_gpa_mae | plan_delta | plan_delta_pct | log_loss | logloss_delta_pct | pr_auc | roc_auc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 47_grade | A | 9.55164 | 0 | 0.550607 | 0.417239 | 0 | 0 | — | — | — | — |
| 47_grade | B | 9.57403 | 0.235304 | 0.551807 | 0.418116 | 0.000877563 | 0.208296 | — | — | — | — |
| 47_grade | C | 9.56025 | 0.0880298 | 0.551292 | 0.417385 | 0.000146145 | 0.0319216 | — | — | — | — |
| 47_grade | D | 9.56773 | 0.172672 | 0.552072 | 0.418197 | 0.000958588 | 0.233378 | — | — | — | — |
| 47_grade | E | 9.55743 | 0.0619343 | 0.551134 | 0.416754 | -0.000484584 | -0.117538 | — | — | — | — |
| 47_grade | F1 | 9.55382 | 0.0237173 | 0.550879 | 0.417389 | 0.000150138 | 0.0369313 | — | — | — | — |
| 47_grade | F2 | 9.55362 | 0.0198486 | 0.551132 | 0.417044 | -0.000195047 | -0.0503152 | — | — | — | — |
| 47_grade | F3 | 9.54125 | -0.107614 | 0.550185 | 0.415861 | -0.00137752 | -0.337019 | — | — | — | — |
| 47_grade | F4 | 9.55122 | -0.00362619 | 0.550693 | 0.416974 | -0.000264324 | -0.0630212 | — | — | — | — |
| 47_fail | A | — | — | — | — | — | — | 0.227719 | 0 | 0.244187 | 0.804031 |
| 47_fail | B | — | — | — | — | — | — | 0.227711 | -0.00824221 | 0.243381 | 0.804269 |
| 47_fail | C | — | — | — | — | — | — | 0.228025 | 0.149711 | 0.240187 | 0.803267 |
| 47_fail | D | — | — | — | — | — | — | 0.228056 | 0.154248 | 0.241192 | 0.803324 |
| 47_fail | E | — | — | — | — | — | — | 0.227999 | 0.128359 | 0.242192 | 0.803137 |
| 47_fail | F1 | — | — | — | — | — | — | 0.227556 | -0.0593985 | 0.243057 | 0.804843 |
| 47_fail | F2 | — | — | — | — | — | — | 0.22751 | -0.0775483 | 0.242994 | 0.804602 |
| 47_fail | F3 | — | — | — | — | — | — | 0.227549 | -0.0626954 | 0.243485 | 0.804731 |
| 47_fail | F4 | — | — | — | — | — | — | 0.227972 | 0.112938 | 0.241046 | 0.8039 |
| 33_grade | A | 9.5224 | 0 | 0.549789 | 0.41664 | 0 | 0 | — | — | — | — |
| 33_grade | B | 9.53401 | 0.126313 | 0.549958 | 0.416078 | -0.000562286 | -0.13479 | — | — | — | — |
| 33_grade | C | 9.53373 | 0.122052 | 0.549968 | 0.417454 | 0.000813315 | 0.202412 | — | — | — | — |
| 33_grade | D | 9.52825 | 0.0630445 | 0.549727 | 0.417073 | 0.000433084 | 0.110032 | — | — | — | — |
| 33_grade | E | 9.53776 | 0.164071 | 0.550412 | 0.417422 | 0.000781484 | 0.196402 | — | — | — | — |
| 33_grade | F1 | 9.52228 | -0.0015627 | 0.549317 | 0.415674 | -0.00096624 | -0.227875 | — | — | — | — |
| 33_grade | F2 | 9.53069 | 0.0883612 | 0.549559 | 0.416242 | -0.000398534 | -0.0971682 | — | — | — | — |
| 33_grade | F3 | 9.51228 | -0.105492 | 0.548757 | 0.415619 | -0.00102151 | -0.244746 | — | — | — | — |
| 33_grade | F4 | 9.54054 | 0.190189 | 0.550261 | 0.416634 | -5.90689e-06 | -0.00231785 | — | — | — | — |
| 33_fail | A | — | — | — | — | — | — | 0.22792 | 0 | 0.242089 | 0.80423 |
| 33_fail | B | — | — | — | — | — | — | 0.227687 | -0.099341 | 0.24381 | 0.804313 |
| 33_fail | C | — | — | — | — | — | — | 0.228134 | 0.0861673 | 0.241018 | 0.803326 |
| 33_fail | D | — | — | — | — | — | — | 0.2281 | 0.0761288 | 0.240745 | 0.803738 |
| 33_fail | E | — | — | — | — | — | — | 0.228185 | 0.115983 | 0.240866 | 0.803036 |
| 33_fail | F1 | — | — | — | — | — | — | 0.228093 | 0.0636414 | 0.240705 | 0.803832 |
| 33_fail | F2 | — | — | — | — | — | — | 0.228224 | 0.121719 | 0.239817 | 0.803611 |
| 33_fail | F3 | — | — | — | — | — | — | 0.22802 | 0.0448813 | 0.240731 | 0.804086 |
| 33_fail | F4 | — | — | — | — | — | — | 0.228241 | 0.132857 | 0.24063 | 0.803525 |
| 47_points | A | — | — | 0.562859 | 0.417966 | 0 | 0 | — | — | — | — |
| 47_points | B | — | — | 0.563298 | 0.418162 | 0.000195326 | 0.047196 | — | — | — | — |
| 47_points | C | — | — | 0.564119 | 0.418988 | 0.00102117 | 0.242316 | — | — | — | — |
| 47_points | D | — | — | 0.563724 | 0.41836 | 0.000393275 | 0.0942267 | — | — | — | — |
| 47_points | E | — | — | 0.563461 | 0.418887 | 0.0009205 | 0.219325 | — | — | — | — |
| 47_points | F1 | — | — | 0.563326 | 0.418184 | 0.000217319 | 0.0510122 | — | — | — | — |
| 47_points | F2 | — | — | 0.562457 | 0.417665 | -0.000301779 | -0.0683418 | — | — | — | — |
| 47_points | F3 | — | — | 0.563626 | 0.418568 | 0.000601181 | 0.144949 | — | — | — | — |
| 47_points | F4 | — | — | 0.563325 | 0.418242 | 0.000275644 | 0.0663671 | — | — | — | — |
| 57_degree_history_grade | A | 9.52573 | 0 | 0.54947 | 0.415682 | 0 | 0 | — | — | — | — |
| 57_degree_history_grade | B | 9.54415 | 0.198767 | 0.550178 | 0.415771 | 8.81997e-05 | 0.0224653 | — | — | — | — |
| 57_degree_history_grade | C | 9.54274 | 0.183034 | 0.550216 | 0.416439 | 0.000756793 | 0.185057 | — | — | — | — |
| 57_degree_history_grade | D | 9.52173 | -0.0383339 | 0.549101 | 0.415323 | -0.000359759 | -0.085588 | — | — | — | — |
| 57_degree_history_grade | E | 9.55234 | 0.281727 | 0.551242 | 0.41675 | 0.00106755 | 0.256187 | — | — | — | — |
| 57_degree_history_grade | F1 | 9.54341 | 0.187858 | 0.550962 | 0.416787 | 0.0011042 | 0.266351 | — | — | — | — |
| 57_degree_history_grade | F2 | 9.53843 | 0.139088 | 0.550562 | 0.415769 | 8.69459e-05 | 0.0231088 | — | — | — | — |
| 57_degree_history_grade | F3 | 9.53206 | 0.0727229 | 0.549673 | 0.415715 | 3.2626e-05 | 0.0144305 | — | — | — | — |
| 57_degree_history_grade | F4 | 9.53487 | 0.101179 | 0.550246 | 0.415516 | -0.000166537 | -0.0384116 | — | — | — | — |


### 47_grade

| year | variant | grade_mae | grade_mae_delta | grade_rmse | grade_bias | course_points_mae | course_points_rmse | plan_gpa_mae | plan_gpa_mae_delta | plan_gpa_mae_relative_pct | plan_gpa_rmse | plan_gpa_bias |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2023 | A | 9.32067 | 0 | 12.488 | 0.416453 | 0.549556 | 0.79275 | 0.408445 | 0 | 0 | 0.582273 | 0.0969759 |
| 2023 | B | 9.34601 | 0.025337 | 12.5248 | 0.45406 | 0.550137 | 0.79386 | 0.408902 | 0.00045727 | 0.111954 | 0.583543 | 0.0998112 |
| 2023 | C | 9.32075 | 7.9553e-05 | 12.4801 | 0.23279 | 0.549455 | 0.791588 | 0.407973 | -0.000471354 | -0.115402 | 0.580745 | 0.0887365 |
| 2023 | D | 9.35271 | 0.0320399 | 12.5249 | 0.331802 | 0.551987 | 0.795602 | 0.410102 | 0.00165716 | 0.405725 | 0.584461 | 0.0924326 |
| 2023 | E | 9.33137 | 0.0107035 | 12.4935 | 0.350335 | 0.549864 | 0.791469 | 0.407694 | -0.000750856 | -0.183833 | 0.579242 | 0.0948883 |
| 2023 | F1 | 9.32615 | 0.00547723 | 12.4798 | 0.354788 | 0.549351 | 0.79015 | 0.408779 | 0.000334499 | 0.0818958 | 0.581728 | 0.0974847 |
| 2023 | F2 | 9.31917 | -0.00149834 | 12.4821 | 0.393768 | 0.549459 | 0.791542 | 0.407548 | -0.000896974 | -0.219607 | 0.580786 | 0.0954013 |
| 2023 | F3 | 9.31483 | -0.00584478 | 12.476 | 0.353219 | 0.548576 | 0.789916 | 0.405737 | -0.00270721 | -0.66281 | 0.577635 | 0.0937218 |
| 2023 | F4 | 9.32308 | 0.00241518 | 12.5005 | 0.459144 | 0.548826 | 0.791876 | 0.408251 | -0.000193526 | -0.0473812 | 0.582298 | 0.100204 |
| 2024 | A | 9.7826 | 0 | 13.1116 | -1.21303 | 0.551657 | 0.775019 | 0.426033 | 0 | 0 | 0.603886 | 0.0161444 |
| 2024 | B | 9.80205 | 0.019445 | 13.1284 | -1.23335 | 0.553478 | 0.776504 | 0.42733 | 0.00129786 | 0.304638 | 0.605053 | 0.0150975 |
| 2024 | C | 9.79974 | 0.0171397 | 13.121 | -1.22002 | 0.553128 | 0.776508 | 0.426796 | 0.000763644 | 0.179245 | 0.604743 | 0.0171015 |
| 2024 | D | 9.78276 | 0.000155874 | 13.1025 | -1.21744 | 0.552158 | 0.775355 | 0.426293 | 0.000260013 | 0.0610313 | 0.603881 | 0.0167164 |
| 2024 | E | 9.78349 | 0.000883587 | 13.1121 | -1.18095 | 0.552403 | 0.775571 | 0.425814 | -0.000218312 | -0.0512431 | 0.60408 | 0.0184958 |
| 2024 | F1 | 9.78149 | -0.00110834 | 13.1086 | -1.20253 | 0.552406 | 0.775606 | 0.425998 | -3.42236e-05 | -0.0080331 | 0.604563 | 0.0172002 |
| 2024 | F2 | 9.78806 | 0.00545603 | 13.1043 | -1.246 | 0.552806 | 0.775735 | 0.426539 | 0.00050688 | 0.118977 | 0.603935 | 0.0147299 |
| 2024 | F3 | 9.76768 | -0.0149205 | 13.0931 | -1.14504 | 0.551795 | 0.77522 | 0.425985 | -4.78352e-05 | -0.0112281 | 0.603969 | 0.0193934 |
| 2024 | F4 | 9.77936 | -0.00324435 | 13.1077 | -1.21195 | 0.552561 | 0.77563 | 0.425697 | -0.000335122 | -0.0786611 | 0.603873 | 0.0163942 |


### 47_fail

| year | variant | pr_auc | pr_auc_delta | roc_auc | roc_auc_delta | log_loss | log_loss_delta | log_loss_relative_pct | brier | brier_delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2023 | A | 0.281839 | 0 | 0.811411 | 0 | 0.247204 | 0 | 0 | 0.0719783 | 0 |
| 2023 | B | 0.279596 | -0.0022427 | 0.811542 | 0.00013139 | 0.247317 | 0.000112592 | 0.0455462 | 0.0720519 | 7.36435e-05 |
| 2023 | C | 0.27904 | -0.00279865 | 0.811558 | 0.000146907 | 0.24713 | -7.42018e-05 | -0.0300164 | 0.0720016 | 2.33388e-05 |
| 2023 | D | 0.278783 | -0.00305604 | 0.81105 | -0.000360705 | 0.2474 | 0.000196144 | 0.0793451 | 0.0720587 | 8.04043e-05 |
| 2023 | E | 0.280676 | -0.00116318 | 0.810832 | -0.000578239 | 0.247363 | 0.000159375 | 0.064471 | 0.0720191 | 4.07631e-05 |
| 2023 | F1 | 0.282489 | 0.000649909 | 0.812831 | 0.00142051 | 0.246698 | -0.000506176 | -0.204761 | 0.0719072 | -7.10764e-05 |
| 2023 | F2 | 0.281813 | -2.5812e-05 | 0.812711 | 0.00130063 | 0.246596 | -0.000608285 | -0.246066 | 0.0719147 | -6.3609e-05 |
| 2023 | F3 | 0.282376 | 0.000536922 | 0.812869 | 0.00145869 | 0.246695 | -0.000509144 | -0.205961 | 0.071912 | -6.6298e-05 |
| 2023 | F4 | 0.279032 | -0.00280723 | 0.811347 | -6.41278e-05 | 0.24743 | 0.000226115 | 0.0914689 | 0.0720669 | 8.86501e-05 |
| 2024 | A | 0.206536 | 0 | 0.796652 | 0 | 0.208234 | 0 | 0 | 0.0573067 | 0 |
| 2024 | B | 0.207166 | 0.000630168 | 0.796996 | 0.000344135 | 0.208105 | -0.000129169 | -0.0620306 | 0.0572806 | -2.60511e-05 |
| 2024 | C | 0.201333 | -0.00520317 | 0.794975 | -0.00167625 | 0.20892 | 0.000686002 | 0.329437 | 0.0574956 | 0.000188938 |
| 2024 | D | 0.203602 | -0.00293407 | 0.795598 | -0.00105375 | 0.208712 | 0.00047717 | 0.22915 | 0.0574449 | 0.000138258 |
| 2024 | E | 0.203708 | -0.00282814 | 0.795441 | -0.00121103 | 0.208635 | 0.000400323 | 0.192246 | 0.0574014 | 9.4723e-05 |
| 2024 | F1 | 0.203625 | -0.00291094 | 0.796855 | 0.000203589 | 0.208413 | 0.000179006 | 0.0859635 | 0.0574192 | 0.000112547 |
| 2024 | F2 | 0.204174 | -0.00236197 | 0.796492 | -0.000159629 | 0.208424 | 0.000189429 | 0.0909691 | 0.057388 | 8.13711e-05 |
| 2024 | F3 | 0.204594 | -0.0019415 | 0.796593 | -5.82614e-05 | 0.208402 | 0.000167776 | 0.0805705 | 0.0573828 | 7.61594e-05 |
| 2024 | F4 | 0.20306 | -0.00347567 | 0.796454 | -0.00019764 | 0.208514 | 0.000279881 | 0.134407 | 0.0574371 | 0.000130482 |


### 33_grade

| year | variant | grade_mae | grade_mae_delta | grade_rmse | grade_bias | course_points_mae | course_points_rmse | plan_gpa_mae | plan_gpa_mae_delta | plan_gpa_mae_relative_pct | plan_gpa_rmse | plan_gpa_bias |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2023 | A | 9.27071 | 0 | 12.4244 | 0.421776 | 0.547822 | 0.789588 | 0.407464 | 0 | 0 | 0.581002 | 0.0984491 |
| 2023 | B | 9.29784 | 0.0271305 | 12.4593 | 0.464566 | 0.548433 | 0.790883 | 0.406946 | -0.000518328 | -0.127208 | 0.581404 | 0.0998871 |
| 2023 | C | 9.2929 | 0.0221932 | 12.4392 | 0.434031 | 0.548533 | 0.790452 | 0.409622 | 0.00215766 | 0.529534 | 0.584714 | 0.100858 |
| 2023 | D | 9.28214 | 0.0114352 | 12.4334 | 0.43232 | 0.54818 | 0.791124 | 0.409039 | 0.00157412 | 0.386322 | 0.584433 | 0.0986119 |
| 2023 | E | 9.29577 | 0.0250663 | 12.4494 | 0.442793 | 0.549082 | 0.791723 | 0.409899 | 0.00243466 | 0.597514 | 0.584477 | 0.0986477 |
| 2023 | F1 | 9.26943 | -0.0012791 | 12.4161 | 0.39051 | 0.547611 | 0.790078 | 0.407283 | -0.000181599 | -0.0445682 | 0.580713 | 0.0948873 |
| 2023 | F2 | 9.28345 | 0.0127453 | 12.4391 | 0.430922 | 0.547488 | 0.788968 | 0.406788 | -0.000676035 | -0.165913 | 0.580006 | 0.0981305 |
| 2023 | F3 | 9.26375 | -0.00695769 | 12.4173 | 0.388622 | 0.547092 | 0.78909 | 0.406547 | -0.000917545 | -0.225184 | 0.580598 | 0.0946576 |
| 2023 | F4 | 9.28711 | 0.016405 | 12.4308 | 0.339878 | 0.548095 | 0.789174 | 0.407288 | -0.000175975 | -0.0431878 | 0.580193 | 0.0945177 |
| 2024 | A | 9.77409 | 0 | 13.1103 | -1.08516 | 0.551755 | 0.77568 | 0.425816 | 0 | 0 | 0.604548 | 0.0206728 |
| 2024 | B | 9.77018 | -0.00391178 | 13.096 | -1.10988 | 0.551483 | 0.775104 | 0.42521 | -0.000606244 | -0.142372 | 0.603133 | 0.0192179 |
| 2024 | C | 9.77455 | 0.000460714 | 13.1178 | -1.08216 | 0.551402 | 0.776163 | 0.425285 | -0.000531032 | -0.124709 | 0.604512 | 0.0213213 |
| 2024 | D | 9.77436 | 0.000267942 | 13.1142 | -1.10984 | 0.551274 | 0.775231 | 0.425108 | -0.000707955 | -0.166258 | 0.603708 | 0.0202312 |
| 2024 | E | 9.77974 | 0.0056456 | 13.1114 | -1.13912 | 0.551741 | 0.776061 | 0.424945 | -0.000871689 | -0.20471 | 0.603945 | 0.0197593 |
| 2024 | F1 | 9.77514 | 0.00104307 | 13.1061 | -1.11543 | 0.551022 | 0.774861 | 0.424065 | -0.00175088 | -0.411182 | 0.601779 | 0.0203474 |
| 2024 | F2 | 9.77793 | 0.00383568 | 13.1093 | -1.14348 | 0.55163 | 0.775606 | 0.425695 | -0.000121033 | -0.0284238 | 0.603845 | 0.0187688 |
| 2024 | F3 | 9.76081 | -0.0132863 | 13.0883 | -1.10437 | 0.550421 | 0.773992 | 0.424691 | -0.00112547 | -0.264309 | 0.601919 | 0.0207704 |
| 2024 | F4 | 9.79398 | 0.0198826 | 13.1246 | -1.123 | 0.552426 | 0.776566 | 0.42598 | 0.000164161 | 0.0385521 | 0.604608 | 0.0192134 |


### 33_fail

| year | variant | pr_auc | pr_auc_delta | roc_auc | roc_auc_delta | log_loss | log_loss_delta | log_loss_relative_pct | brier | brier_delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2023 | A | 0.281519 | 0 | 0.812295 | 0 | 0.247286 | 0 | 0 | 0.0720152 | 0 |
| 2023 | B | 0.281554 | 3.55498e-05 | 0.812548 | 0.000252887 | 0.246955 | -0.00033091 | -0.133817 | 0.0719929 | -2.22874e-05 |
| 2023 | C | 0.277677 | -0.00384181 | 0.810819 | -0.00147529 | 0.247716 | 0.000429643 | 0.173743 | 0.0721752 | 0.000159924 |
| 2023 | D | 0.278573 | -0.00294579 | 0.81119 | -0.00110485 | 0.247557 | 0.000270884 | 0.109543 | 0.072162 | 0.000146753 |
| 2023 | E | 0.279205 | -0.00231323 | 0.810732 | -0.00156301 | 0.24758 | 0.000294281 | 0.119004 | 0.0721019 | 8.66318e-05 |
| 2023 | F1 | 0.27715 | -0.00436868 | 0.810964 | -0.00133073 | 0.247794 | 0.000507757 | 0.205332 | 0.0722207 | 0.000205431 |
| 2023 | F2 | 0.275493 | -0.00602583 | 0.810859 | -0.00143534 | 0.24793 | 0.000644047 | 0.260446 | 0.0722912 | 0.000276018 |
| 2023 | F3 | 0.278526 | -0.00299242 | 0.811844 | -0.000450685 | 0.24736 | 7.36327e-05 | 0.0297763 | 0.0721202 | 0.000104991 |
| 2023 | F4 | 0.27812 | -0.0033987 | 0.810721 | -0.00157327 | 0.247844 | 0.000557695 | 0.225526 | 0.0722155 | 0.000200287 |
| 2024 | A | 0.202658 | 0 | 0.796166 | 0 | 0.208554 | 0 | 0 | 0.0574455 | 0 |
| 2024 | B | 0.206066 | 0.00340789 | 0.796079 | -8.72148e-05 | 0.208419 | -0.000135279 | -0.0648652 | 0.0573493 | -9.62178e-05 |
| 2024 | C | 0.204359 | 0.00170055 | 0.795833 | -0.000332889 | 0.208551 | -2.93818e-06 | -0.00140883 | 0.0574097 | -3.58396e-05 |
| 2024 | D | 0.202917 | 0.000258254 | 0.796287 | 0.000120717 | 0.208643 | 8.90831e-05 | 0.0427146 | 0.0574922 | 4.67357e-05 |
| 2024 | E | 0.202526 | -0.000131893 | 0.795339 | -0.000826549 | 0.20879 | 0.000235585 | 0.112961 | 0.0574826 | 3.70803e-05 |
| 2024 | F1 | 0.204261 | 0.00160223 | 0.7967 | 0.00053426 | 0.208392 | -0.000162774 | -0.0780489 | 0.0574045 | -4.09842e-05 |
| 2024 | F2 | 0.204141 | 0.00148263 | 0.796363 | 0.000197006 | 0.208519 | -3.54726e-05 | -0.0170088 | 0.0574219 | -2.36438e-05 |
| 2024 | F3 | 0.202935 | 0.000276683 | 0.796328 | 0.000162211 | 0.208679 | 0.000125104 | 0.0599862 | 0.0574995 | 5.39867e-05 |
| 2024 | F4 | 0.20314 | 0.000481578 | 0.796329 | 0.000162795 | 0.208638 | 8.38135e-05 | 0.0401879 | 0.0574798 | 3.42465e-05 |


### 47_points

| year | variant | course_points_mae | course_points_rmse | plan_gpa_mae | plan_gpa_mae_delta | plan_gpa_mae_relative_pct | plan_gpa_rmse | plan_gpa_bias |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2023 | A | 0.559077 | 0.776284 | 0.405317 | 0 | 0 | 0.565881 | 0.0638172 |
| 2023 | B | 0.560023 | 0.776061 | 0.405571 | 0.000253361 | 0.0625094 | 0.565384 | 0.0597388 |
| 2023 | C | 0.560601 | 0.776084 | 0.406031 | 0.000713909 | 0.176136 | 0.565113 | 0.0566285 |
| 2023 | D | 0.560751 | 0.776486 | 0.405717 | 0.000399896 | 0.0986626 | 0.564863 | 0.0568429 |
| 2023 | E | 0.559853 | 0.775933 | 0.406084 | 0.000767286 | 0.189305 | 0.566061 | 0.0587229 |
| 2023 | F1 | 0.560227 | 0.77607 | 0.405392 | 7.52064e-05 | 0.0185549 | 0.564914 | 0.0567383 |
| 2023 | F2 | 0.559666 | 0.775631 | 0.405557 | 0.000239948 | 0.0592001 | 0.56549 | 0.0603266 |
| 2023 | F3 | 0.560693 | 0.776119 | 0.406054 | 0.000736709 | 0.181761 | 0.565398 | 0.056718 |
| 2023 | F4 | 0.560212 | 0.775996 | 0.405642 | 0.000324999 | 0.080184 | 0.565475 | 0.059235 |
| 2024 | A | 0.566641 | 0.775037 | 0.430616 | 0 | 0 | 0.600599 | -0.0216176 |
| 2024 | B | 0.566573 | 0.774749 | 0.430753 | 0.000137291 | 0.0318825 | 0.600348 | -0.021841 |
| 2024 | C | 0.567637 | 0.775936 | 0.431944 | 0.00132843 | 0.308495 | 0.60206 | -0.0218706 |
| 2024 | D | 0.566696 | 0.774878 | 0.431002 | 0.000386654 | 0.0897909 | 0.600771 | -0.0228301 |
| 2024 | E | 0.567069 | 0.775503 | 0.431689 | 0.00107371 | 0.249344 | 0.60162 | -0.0217348 |
| 2024 | F1 | 0.566425 | 0.774696 | 0.430975 | 0.000359432 | 0.0834694 | 0.601286 | -0.0210865 |
| 2024 | F2 | 0.565248 | 0.773703 | 0.429772 | -0.000843506 | -0.195884 | 0.600018 | -0.0194563 |
| 2024 | F3 | 0.566558 | 0.774945 | 0.431081 | 0.000465652 | 0.108136 | 0.601313 | -0.020946 |
| 2024 | F4 | 0.566438 | 0.774721 | 0.430842 | 0.00022629 | 0.0525502 | 0.601282 | -0.0204787 |


### 57_degree_history_grade

| year | variant | grade_mae | grade_mae_delta | grade_rmse | grade_bias | course_points_mae | course_points_rmse | plan_gpa_mae | plan_gpa_mae_delta | plan_gpa_mae_relative_pct | plan_gpa_rmse | plan_gpa_bias |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2023 | A | 9.28225 | 0 | 12.4629 | 0.5711 | 0.546943 | 0.789266 | 0.407411 | 0 | 0 | 0.580075 | 0.106564 |
| 2023 | B | 9.32051 | 0.0382546 | 12.4916 | 0.549247 | 0.548507 | 0.790486 | 0.407758 | 0.00034688 | 0.0851426 | 0.580881 | 0.106623 |
| 2023 | C | 9.31532 | 0.0330617 | 12.5012 | 0.688018 | 0.548033 | 0.791684 | 0.408778 | 0.0013674 | 0.335632 | 0.582958 | 0.111236 |
| 2023 | D | 9.29216 | 0.00990342 | 12.4654 | 0.55412 | 0.546962 | 0.789129 | 0.407258 | -0.000152428 | -0.0374139 | 0.580883 | 0.10326 |
| 2023 | E | 9.31695 | 0.0346918 | 12.481 | 0.52778 | 0.549312 | 0.790941 | 0.408325 | 0.000914441 | 0.224452 | 0.581166 | 0.105587 |
| 2023 | F1 | 9.30778 | 0.0255244 | 12.4793 | 0.538472 | 0.548819 | 0.791099 | 0.408642 | 0.00123174 | 0.302333 | 0.581175 | 0.102632 |
| 2023 | F2 | 9.3161 | 0.0338496 | 12.4754 | 0.498006 | 0.549105 | 0.790205 | 0.407954 | 0.000543011 | 0.133283 | 0.57898 | 0.100842 |
| 2023 | F3 | 9.31187 | 0.0296139 | 12.4932 | 0.662104 | 0.548102 | 0.791113 | 0.408817 | 0.00140632 | 0.345184 | 0.582364 | 0.109164 |
| 2023 | F4 | 9.31064 | 0.0283825 | 12.481 | 0.46124 | 0.548754 | 0.790753 | 0.407592 | 0.00018172 | 0.0446036 | 0.579815 | 0.0982437 |
| 2024 | A | 9.76921 | 0 | 13.0883 | -1.48073 | 0.551996 | 0.773909 | 0.423954 | 0 | 0 | 0.600658 | 0.00324364 |
| 2024 | B | 9.76778 | -0.00142545 | 13.0688 | -1.47447 | 0.551849 | 0.772316 | 0.423784 | -0.000170481 | -0.0402121 | 0.598796 | 0.00256623 |
| 2024 | C | 9.77017 | 0.000965776 | 13.0809 | -1.48148 | 0.552399 | 0.773469 | 0.4241 | 0.000146185 | 0.0344812 | 0.599847 | 0.00207165 |
| 2024 | D | 9.75129 | -0.0179128 | 13.0704 | -1.44385 | 0.551241 | 0.772839 | 0.423387 | -0.00056709 | -0.133762 | 0.599346 | 0.00307805 |
| 2024 | E | 9.78774 | 0.0185333 | 13.1066 | -1.53909 | 0.553172 | 0.774871 | 0.425175 | 0.00122065 | 0.287921 | 0.601869 | -0.00137955 |
| 2024 | F1 | 9.77905 | 0.00984097 | 13.0874 | -1.51619 | 0.553105 | 0.774127 | 0.424931 | 0.000976658 | 0.230369 | 0.600206 | -0.000132477 |
| 2024 | F2 | 9.76076 | -0.00844981 | 13.0724 | -1.45924 | 0.55202 | 0.7737 | 0.423585 | -0.000369119 | -0.0870658 | 0.599356 | 0.00294112 |
| 2024 | F3 | 9.75225 | -0.0169586 | 13.0609 | -1.47252 | 0.551244 | 0.772729 | 0.422613 | -0.00134107 | -0.316323 | 0.598797 | 0.00262228 |
| 2024 | F4 | 9.7591 | -0.0101027 | 13.0701 | -1.40668 | 0.551738 | 0.773705 | 0.423439 | -0.000514794 | -0.121427 | 0.599964 | 0.00627279 |


Paired uncertainty resamples students with all corresponding course rows/observed plans, 1,000 draws, seed 42, percentile 95% intervals. This captures evaluation-case uncertainty conditional on one fitted model/configuration; it does not capture seed or hyperparameter uncertainty. Multiple exploratory comparisons were not multiplicity-adjusted. No product noninferiority margin was supplied; zero-overlap alone is not an approval policy. All cells in [paired_intervals.csv](../data/evaluation/experiments/student_progress_20261010/paired_intervals.csv).


Variant C paired intervals:

| year | model | metric | delta | low | high | students |
| --- | --- | --- | --- | --- | --- | --- |
| 2023 | 47_grade | grade_mae | 7.9553e-05 | -0.00988529 | 0.00987471 | 6564 |
| 2023 | 47_grade | plan_gpa_mae | -0.000471354 | -0.00175985 | 0.000905637 | 6564 |
| 2023 | 47_fail | log_loss | -7.42018e-05 | -0.000414018 | 0.000279386 | 6564 |
| 2023 | 33_grade | grade_mae | 0.0221932 | 0.0146056 | 0.0298619 | 6564 |
| 2023 | 33_grade | plan_gpa_mae | 0.00215766 | 0.000917206 | 0.00322075 | 6564 |
| 2023 | 33_fail | log_loss | 0.000429643 | 4.51834e-05 | 0.000855541 | 6564 |
| 2023 | 47_points | course_points_mae | 0.0015235 | 0.00113923 | 0.00196463 | 6564 |
| 2023 | 47_points | plan_gpa_mae | 0.000713909 | 0.000146585 | 0.00128729 | 6564 |
| 2023 | 57_degree_history_grade | grade_mae | 0.0330617 | 0.0245889 | 0.041705 | 6564 |
| 2023 | 57_degree_history_grade | plan_gpa_mae | 0.0013674 | 0.000170658 | 0.0026254 | 6564 |
| 2024 | 47_grade | grade_mae | 0.0171397 | 0.0102893 | 0.0238652 | 6681 |
| 2024 | 47_grade | plan_gpa_mae | 0.000763644 | -0.000186689 | 0.00160053 | 6681 |
| 2024 | 47_fail | log_loss | 0.000686002 | 0.000439399 | 0.000950956 | 6681 |
| 2024 | 33_grade | grade_mae | 0.000460714 | -0.00604752 | 0.00678738 | 6681 |
| 2024 | 33_grade | plan_gpa_mae | -0.000531032 | -0.0015259 | 0.00034977 | 6681 |
| 2024 | 33_fail | log_loss | -2.93818e-06 | -0.000268461 | 0.000248953 | 6681 |
| 2024 | 47_points | course_points_mae | 0.00099536 | 0.000651942 | 0.00130496 | 6681 |
| 2024 | 47_points | plan_gpa_mae | 0.00132843 | 0.000877596 | 0.00180265 | 6681 |
| 2024 | 57_degree_history_grade | grade_mae | 0.000965776 | -0.00574849 | 0.00791307 | 6681 |
| 2024 | 57_degree_history_grade | plan_gpa_mae | 0.000146185 | -0.000898155 | 0.00120029 | 6681 |


Degree and progress slices use ≥100 rows and fixed start-credit intervals `[0,30)`, `[30,60)`, `[60,90)`, `[90,∞)`. These bands describe the supplied counter, not certified earned hours. Full paired subgroup deltas: [group_deltas.csv](../data/evaluation/experiments/student_progress_20261010/group_deltas.csv). Descriptive quartiles and modeling bands deliberately use different summaries; neither is selected using performance.


Variant C consistency by slice (positive loss changes mean worse; degree/progress summaries overlap the same evaluation students and are not independent replications). Minimum/maximum are observed point-estimate deltas, not uncertainty bounds; small cohorts cannot establish subgroup safety:

| year | model | slice | metric | evaluated_slices | worse_slices | better_slices | minimum_delta | maximum_delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2023 | 47_grade | degree | plan_gpa_mae | 38 | 19 | 19 | -0.0181624 | 0.0196716 |
| 2023 | 47_grade | progress | plan_gpa_mae | 4 | 2 | 2 | -0.00358063 | 0.000566142 |
| 2023 | 47_fail | degree | log_loss | 38 | 24 | 14 | -0.00670219 | 0.00741413 |
| 2023 | 47_fail | progress | log_loss | 4 | 1 | 3 | -0.000712288 | 0.00126163 |
| 2023 | 33_grade | degree | plan_gpa_mae | 38 | 13 | 25 | -0.0105796 | 0.0381787 |
| 2023 | 33_grade | progress | plan_gpa_mae | 4 | 2 | 2 | -0.000479162 | 0.00398907 |
| 2023 | 33_fail | degree | log_loss | 38 | 28 | 10 | -0.00309126 | 0.00969335 |
| 2023 | 33_fail | progress | log_loss | 4 | 3 | 1 | -0.000662164 | 0.00190344 |
| 2023 | 47_points | degree | plan_gpa_mae | 38 | 20 | 18 | -0.00871433 | 0.00995626 |
| 2023 | 47_points | progress | plan_gpa_mae | 4 | 2 | 2 | -0.000772263 | 0.00163868 |
| 2023 | 57_degree_history_grade | degree | plan_gpa_mae | 38 | 21 | 17 | -0.0144174 | 0.0176102 |
| 2023 | 57_degree_history_grade | progress | plan_gpa_mae | 4 | 4 | 0 | 0.00108389 | 0.00160215 |
| 2024 | 47_grade | degree | plan_gpa_mae | 37 | 20 | 17 | -0.0115574 | 0.0252658 |
| 2024 | 47_grade | progress | plan_gpa_mae | 4 | 3 | 1 | -0.0031401 | 0.00286891 |
| 2024 | 47_fail | degree | log_loss | 37 | 24 | 13 | -0.00214459 | 0.0071644 |
| 2024 | 47_fail | progress | log_loss | 4 | 4 | 0 | 0.000483143 | 0.000948741 |
| 2024 | 33_grade | degree | plan_gpa_mae | 37 | 17 | 20 | -0.00941817 | 0.0139996 |
| 2024 | 33_grade | progress | plan_gpa_mae | 4 | 1 | 3 | -0.0017098 | 0.000926487 |
| 2024 | 33_fail | degree | log_loss | 37 | 15 | 22 | -0.00360785 | 0.00725434 |
| 2024 | 33_fail | progress | log_loss | 4 | 1 | 3 | -0.000155271 | 0.000111231 |
| 2024 | 47_points | degree | plan_gpa_mae | 37 | 23 | 14 | -0.00616219 | 0.0115223 |
| 2024 | 47_points | progress | plan_gpa_mae | 4 | 3 | 1 | -0.00130795 | 0.00274518 |
| 2024 | 57_degree_history_grade | degree | plan_gpa_mae | 37 | 17 | 20 | -0.0257183 | 0.0184103 |
| 2024 | 57_degree_history_grade | progress | plan_gpa_mae | 4 | 2 | 2 | -0.00215757 | 0.00144978 |


Currently selected relevant models: LightGBM gain importance (all four fields):

| model | feature | gain_share_percent | rank |
| --- | --- | --- | --- |
| official_grade | start_total_in_courses | 0.371892 | 20 |
| official_grade | start_total_in_credits | 0.481505 | 18 |
| official_grade | prior_total_reg_courses | 0.206323 | 24 |
| official_grade | prior_total_reg_credits | 0.186135 | 26 |
| official_fail | start_total_in_courses | 1.29678 | 10 |
| official_fail | start_total_in_credits | 0.652699 | 19 |
| official_fail | prior_total_reg_courses | 0.185367 | 33 |
| official_fail | prior_total_reg_credits | 0.252075 | 26 |
| stage1_grade | start_total_in_courses | 0.443384 | 21 |
| stage1_grade | start_total_in_credits | 0.465441 | 20 |
| stage1_grade | prior_total_reg_courses | 0.186222 | 24 |
| stage1_grade | prior_total_reg_credits | 0.148719 | 26 |
| stage1_fail | start_total_in_courses | 1.2251 | 13 |
| stage1_fail | start_total_in_credits | 1.00212 | 15 |
| stage1_fail | prior_total_reg_courses | 0.292564 | 25 |
| stage1_fail | prior_total_reg_credits | 0.301956 | 24 |
| selected_degree_history_mark | start_total_in_courses | 0.371187 | 28 |
| selected_degree_history_mark | start_total_in_credits | 0.461296 | 23 |
| selected_degree_history_mark | prior_total_reg_courses | 0.0944105 | 39 |
| selected_degree_history_mark | prior_total_reg_credits | 0.106413 | 36 |


Nested baseline gain for all inputs: [baseline_gain.csv](../data/evaluation/experiments/student_progress_20261010/baseline_gain.csv). Reported validation permutation uses 1,000 complete observed student-semester plans per year, three repeats, changing each field or all four together at status level. Whole-plan group sampling preserves its Plan GPA interpretation. The original diagnostic partial-course sample is saved but is not the reported Plan GPA importance evidence. Dependent ratio stays unchanged; permutation breaks correlations and can create implausible feature combinations. The joint diagnostic tests four explicit columns only, not all progress information. Results: [permutation_summary.csv](../data/evaluation/experiments/student_progress_20261010/permutation_summary.csv). Low individual gain can reflect correlated competitors; gain/permutation alone cannot authorize removal.


Joint four-field permutation increases the primary loss in every model/fold below, supporting joint predictive information conditional on the retained inputs. This does not establish that each individual feature is necessary or provide causal evidence:

| year | model | metric | mean_delta | min_delta | max_delta |
| --- | --- | --- | --- | --- | --- |
| 2023 | 47_grade | plan_gpa_mae | 0.00555221 | 0.00333579 | 0.00670584 |
| 2023 | 47_fail | log_loss | 0.0013082 | -4.43246e-05 | 0.00227144 |
| 2023 | 33_grade | plan_gpa_mae | 0.00383227 | 0.00239379 | 0.00552267 |
| 2023 | 33_fail | log_loss | 0.00191877 | 0.000553386 | 0.0027757 |
| 2023 | 47_points | plan_gpa_mae | 0.00156992 | 0.00096661 | 0.00208771 |
| 2023 | 57_degree_history_grade | plan_gpa_mae | 0.00630548 | 0.00404523 | 0.00865073 |
| 2024 | 47_grade | plan_gpa_mae | 0.00554171 | 0.00298996 | 0.00698256 |
| 2024 | 47_fail | log_loss | 0.000559429 | 0.00046549 | 0.00063676 |
| 2024 | 33_grade | plan_gpa_mae | 0.010378 | 0.00643424 | 0.0124013 |
| 2024 | 33_fail | log_loss | 0.000764248 | 0.000564396 | 0.00106162 |
| 2024 | 47_points | plan_gpa_mae | 0.00326208 | 0.00221961 | 0.00525529 |
| 2024 | 57_degree_history_grade | plan_gpa_mae | 0.00737 | 0.00505779 | 0.0104291 |


## 7. Downstream Recommendation Impact


Historical Plan GPA is credit-weighted predicted points over exactly the same modeled finalized-course records; zero-total-credit groups are excluded consistently. It is not necessarily the complete registration roster or official semester GPA. Plan-context training uses the fuller registration roster, whereas evaluation targets exist only for modeled finalized courses. This distinction applies identically to every variant.


Measured registration-context coverage:

| year | plans | exact_credits_plans | exact_course_count_plans | complete_registration_context_plans | coverage_pct | mean_roster_minus_modeled_credits |
| --- | --- | --- | --- | --- | --- | --- |
| 2023 | 16500 | 13454 | 13454 | 13454 | 81.5394 | 0.802727 |
| 2024 | 15413 | 12870 | 12870 | 12870 | 83.5009 | 0.816843 |


Supplementary complete-registration comparison (course count and credits both match the existing roster context):

| year | model | variant | grade_mae | plan_gpa_mae | plan_gpa_mae_delta | log_loss | log_loss_delta |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2023 | 47_grade | A | 9.02389 | 0.376803 | 0 | — | — |
| 2023 | 47_grade | C | 9.02757 | 0.376143 | -0.000660041 | — | — |
| 2023 | 47_fail | A | — | — | — | 0.215662 | 0 |
| 2023 | 47_fail | C | — | — | — | 0.215561 | -0.000100947 |
| 2023 | 33_grade | A | 8.97368 | 0.375045 | 0 | — | — |
| 2023 | 33_grade | C | 8.99134 | 0.376521 | 0.0014753 | — | — |
| 2023 | 33_fail | A | — | — | — | 0.215648 | 0 |
| 2023 | 33_fail | C | — | — | — | 0.215927 | 0.000279523 |
| 2023 | 47_points | A | — | 0.375086 | 0 | — | — |
| 2023 | 47_points | C | — | 0.376056 | 0.000969656 | — | — |
| 2023 | 57_degree_history_grade | A | 8.98466 | 0.375304 | 0 | — | — |
| 2023 | 57_degree_history_grade | C | 9.01419 | 0.375955 | 0.000651523 | — | — |
| 2024 | 47_grade | A | 9.40702 | 0.38636 | 0 | — | — |
| 2024 | 47_grade | C | 9.42536 | 0.387565 | 0.0012052 | — | — |
| 2024 | 47_fail | A | — | — | — | 0.178646 | 0 |
| 2024 | 47_fail | C | — | — | — | 0.17927 | 0.000624714 |
| 2024 | 33_grade | A | 9.39116 | 0.385448 | 0 | — | — |
| 2024 | 33_grade | C | 9.39898 | 0.38566 | 0.000211297 | — | — |
| 2024 | 33_fail | A | — | — | — | 0.178706 | 0 |
| 2024 | 33_fail | C | — | — | — | 0.178786 | 7.92179e-05 |
| 2024 | 47_points | A | — | 0.394145 | 0 | — | — |
| 2024 | 47_points | C | — | 0.395387 | 0.00124224 | — | — |
| 2024 | 57_degree_history_grade | A | 9.40284 | 0.385235 | 0 | — | — |
| 2024 | 57_degree_history_grade | C | 9.4021 | 0.385365 | 0.000130258 | — | — |


All nine configurations on this matched subset, and paired student intervals, are retained in [complete_registration_metrics.csv](../data/evaluation/experiments/student_progress_20261010/complete_registration_metrics.csv) and [complete_registration_intervals.csv](../data/evaluation/experiments/student_progress_20261010/complete_registration_intervals.csv). Matching roster context reduces coverage confounding but still does not certify official GPA counting rules.


Projected cumulative GPA error against matched source end_agpa_points:

| year | model | variant | projected_cumulative_gpa_mae_vs_end | projected_cumulative_gpa_mae_vs_end_delta | additive_observed_gpa_mae_vs_end | projected_comparable_plans |
| --- | --- | --- | --- | --- | --- | --- |
| 2023 | 47_grade | A | 0.368913 | 0 | 0.284884 | 16500 |
| 2023 | 47_grade | C | 0.368841 | -7.2486e-05 | 0.284884 | 16500 |
| 2023 | 47_grade | E | 0.368582 | -0.000331768 | 0.284884 | 16500 |
| 2023 | 33_grade | A | 0.369382 | 0 | 0.284884 | 16500 |
| 2023 | 33_grade | C | 0.369567 | 0.000185158 | 0.284884 | 16500 |
| 2023 | 33_grade | E | 0.37029 | 0.00090787 | 0.284884 | 16500 |
| 2023 | 47_points | A | 0.371005 | 0 | 0.284884 | 16500 |
| 2023 | 47_points | C | 0.371005 | -3.47861e-07 | 0.284884 | 16500 |
| 2023 | 47_points | E | 0.370997 | -7.9539e-06 | 0.284884 | 16500 |
| 2023 | 57_degree_history_grade | A | 0.368642 | 0 | 0.284884 | 16500 |
| 2023 | 57_degree_history_grade | C | 0.368808 | 0.000165345 | 0.284884 | 16500 |
| 2023 | 57_degree_history_grade | E | 0.368154 | -0.000488361 | 0.284884 | 16500 |
| 2024 | 47_grade | A | 0.353206 | 0 | 0.258417 | 15413 |
| 2024 | 47_grade | C | 0.353518 | 0.000311285 | 0.258417 | 15413 |
| 2024 | 47_grade | E | 0.353361 | 0.000154457 | 0.258417 | 15413 |
| 2024 | 33_grade | A | 0.352659 | 0 | 0.258417 | 15413 |
| 2024 | 33_grade | C | 0.352587 | -7.194e-05 | 0.258417 | 15413 |
| 2024 | 33_grade | E | 0.352249 | -0.000410411 | 0.258417 | 15413 |
| 2024 | 47_points | A | 0.357237 | 0 | 0.258417 | 15413 |
| 2024 | 47_points | C | 0.35739 | 0.000153652 | 0.258417 | 15413 |
| 2024 | 47_points | E | 0.357563 | 0.000326313 | 0.258417 | 15413 |
| 2024 | 57_degree_history_grade | A | 0.354407 | 0 | 0.258417 | 15413 |
| 2024 | 57_degree_history_grade | C | 0.354436 | 2.97664e-05 | 0.258417 | 15413 |
| 2024 | 57_degree_history_grade | E | 0.355184 | 0.000777074 | 0.258417 | 15413 |


The observed-points additive control is nonzero even without model error. This is a separate policy/coverage/denominator reconciliation issue: registered credits need not equal official GPA credits; incomplete modeled rosters, repeats/replacement, exemptions and source semantics can also explain discrepancies. It does not identify the denominator alone as the cause, and improved projection under this policy does not establish official AGPA accuracy.


Executed fixed-candidate sensitivity: 12 eligible finalized-course pools per outer year, at most eight courses per pool, exact same credit target selected by most available alternatives before scoring; plan/peer context recomputed for each subset. Grade/fail 47 and 33 models rank standalone proposals by additive projected GPA, then failed credits, plan GPA, plan ID. No production engine, production two-stage shortlist, Balance strategy or active request was executed. This tests sensitivity under an explicitly fixed policy:

| family | variant | cases | top1_changes | top3_set_changes | maximum_plan_gpa_delta |
| --- | --- | --- | --- | --- | --- |
| 47 | A | 24 | 0 | 0 | 0 |
| 47 | B | 24 | 6 | 14 | 0.25 |
| 47 | C | 24 | 10 | 15 | 0.25 |
| 47 | D | 24 | 8 | 16 | 0.2 |
| 47 | E | 24 | 9 | 16 | 0.25 |
| 47 | F1 | 24 | 8 | 14 | 0.25 |
| 47 | F2 | 24 | 8 | 12 | 0.194444 |
| 47 | F3 | 24 | 7 | 13 | 0.25 |
| 47 | F4 | 24 | 7 | 14 | 0.2 |
| 33 | A | 24 | 0 | 0 | 0 |
| 33 | B | 24 | 7 | 9 | 0.25 |
| 33 | C | 24 | 5 | 8 | 0.21875 |
| 33 | D | 24 | 4 | 9 | 0.166667 |
| 33 | E | 24 | 5 | 8 | 0.217742 |
| 33 | F1 | 24 | 6 | 9 | 0.166667 |
| 33 | F2 | 24 | 5 | 10 | 0.166667 |
| 33 | F3 | 24 | 6 | 9 | 0.166667 |
| 33 | F4 | 24 | 7 | 11 | 0.1875 |


Pools are selected in deterministic key order and are not a representative live requestable universe. No observed outcomes exist for each alternative plan; Top-1/Top-3 changes demonstrate sensitivity, not superiority or harm in counterfactual recommendation quality. Exact pools/model SHA/signatures/caveats are saved in [downstream_provenance.json](../data/evaluation/experiments/student_progress_20261010/downstream_provenance.json).


## 8. Backend Contract Implications


This is a recommended ownership contract, not an HTTP/PHP implementation. Current in-process ready payloads require all four snapshot fields; isolated matrix exclusion does not relax that validator.


| Boundary | Field / information | Owner and timing |
|---|---|---|
| A: beginning request | student_id, degree_id, part_id, grade_version_id | Backend supplies exact target identity/version; Python validates |
| A: beginning request | start_agpa_points and explicit current_gpa_credits | Backend supplies official start GPA and certified denominator; do not equate progress columns without university confirmation |
| A: beginning request | start_total_in_credits, start_total_in_courses | Backend supplies verified target-start snapshot; currently required even for a proposed model removal |
| A/B | prior_total_reg_credits/courses, prior_total_fail_credits/courses, prior_registered_semesters | Backend supplies ready finalized prior-state values, or a separately approved Python history adapter derives from finalized status records; existing course bundles cannot reconstruct these |
| A/B | gpa_prev_1/2, observed_gap_semesters, diploma_gpa/type | Backend ready snapshot currently supplies; Python local adapter can derive GPA/gap only with correctly ordered finalized status history |
| A: beginning request | degree_credits_count, course IDs/credits, plan course/requirement type, year/semester, plan_credits_count, attempt_number, previous_course_status | Backend supplies eligible catalog/candidate records; attempts/status have their own history contracts |
| A: beginning request | exact credit target, requirement counts, repeat allowances and other supported policy inputs | Backend/request supplies; Python validates against existing constraints |
| B: finalized history | Course and specialty difficulty states, category levels, model/scaler/version provenance, explicit as_of_part | Existing immutable V2 artifacts available to Python; select strictly before target |
| C: semester update | finalized marks/status/points, student semester GPA, end cumulative GPA/counters and official GPA credits | Backend/university persists finalized student records for the next snapshot and offline training; not beginning request features |
| C: existing history Delta | finalized flag, delta_part, aggregates with IDs/credits/count/fail/retake/mark/attempt sums | Backend supplies finalized aggregates; Python validates/idempotently publishes difficulty history; no student progress snapshot update here |
| D: internally derived | prior_* aliases, prior_fail_credit_ratio, GPA trend/missing, part_semester | Offline Python derives from verified source; ready API currently accepts ratio/GPA history and derives trend/part, not the whole history |
| D: internally derived | course/specialty history features, plan/peer context, expected quality points, Plan GPA, additive projected GPA | Python derives from artifacts/candidate combination; do not request per-plan context directly from PHP |


`current_gpa_credits` precedence locally is explicit override → snapshot value → prior registration credits (`engine.py:21–34`). Backend ready adapter requires explicit `current_gpa_credits` (`inputs.py:251–279`), and both two-stage projections use it. Keep this separate from feature removal. Start credits participate in cleaning/outlier checks and isolated graduation-hour diagnostics (`scripts/scan_under_12_after_status_change.py:100–101`, `scripts/scan_student_over_polict.py:84–85`). Actual recommendation requirement-credit caps use explicit `requirement_policies` in `src/recommendation/constraints.py`, not those diagnostics. Model-only removal changes none of these paths.


## 9. Final Recommendation


**KEEP_ALL** for now. This is a conservative retention decision, not proof that every column is individually indispensable. The proposed registered-credits-only variant C has mixed grade/Plan GPA effects across years and the 47/33 families. Direct-points Plan GPA MAE worsens by +0.000714 (+0.176%) in 2023 and +0.001328 (+0.309%) in 2024; student-cluster 95% intervals are [+0.000147,+0.001287] and [+0.000878,+0.001803]. These are small detectable changes, not established substantial practical harm. No accepted noninferiority tolerance was supplied, and no tested reduced configuration establishes harmlessness across all affected profiles/folds. The broader best-subset question remains inconclusive; individual leave-one-out signals can motivate a separately specified follow-up.


Keep the present inputs while agreeing a Plan GPA tolerance/subgroup risk policy and resolving university source semantics. Comparisons are conditional on retained ratios/GPA/history and fixed configurations. Historical-plan results and candidate sensitivity do not validate recommendation quality. API-field removal and GPA-denominator replacement remain independently unapproved regardless of model metrics.


Three independent decisions: (1) a model matrix/contract change requires retraining and artifact validation; (2) API/source field removal needs independent dependency and data-availability review; (3) GPA denominator/policy change needs official university confirmation and separate academic-calculation validation. No approval for any of them is inferred from this report.


## 10. Required Follow-up Actions


Obtain view SQL, historical snapshot/finalization guarantees, official GPA inclusion/repeat rules and explanations for transition exceptions. Agree a meaningful product tolerance and subgroup risk policy before final selection; extend temporal years/repeated seeds or a prospective term if needed. Freeze any selected feature subset and protocol before a separately authorized final evaluation; existing 2025 prior exposure must be disclosed.


If a subset is approved later, change/revalidate `src/features/feature_contract.py` ordered model lists; `src/experiments/course_only_core.py` and `src/recommendation/two_stage_artifacts.py` stage contracts; modeling and relevant research matrix builders; `src/recommendation/artifacts.py`, `engine.py`, `two_stage_engine.py` loaders/scoring and any payload validator intentionally relaxed; contract/temporal/recommendation tests and documentation. Source cleaning/status and GPA columns stay unless separately approved.


Retrain/promote under new provenance: `models/grade_regressor_v2.txt`, `fail_risk_classifier_v2.txt`, `model_metadata_v2.json`, `data/artifacts/category_levels_v2.json`; course-only reference metadata/categories/models; `models/shortlist_v2/{grade_model.txt,fail_model.txt,category_levels.json,manifest.json}`; selected degree-points research artifacts only if its profile is adopted. Re-run stage compatibility, ranking/benchmark approval and policy checks. Feature-order changes invalidate current strict loaders/manifests; replacing model text alone is insufficient. Rebuild feature tables/history only if definitions change, under new approved versions; not needed for matrix-only removal.


### Verification and changes


Protected inventory: 1159 files; changed=[], added=[], removed=[]. Existing production Python/data/V1/V2/model manifests/selected models/history are **NOT CHANGED**. Experimental scripts/tests/audit notes, isolated numerical/model outputs and this report were added. Graphify AST outputs are generated navigation updates. No commit, API implementation or feature promotion.


Validation: related production suites **110 passed** ([related_suite.log](../scripts/experiments/student_progress_20261010/related_suite.log)); combined existing/experimental suite **1,185 passed, 1 failed, 6 subtests passed** ([final_full_suite.log](../scripts/experiments/student_progress_20261010/final_full_suite.log)). Its only failure is the pre-existing `test_tune_model_evaluates_every_candidate_fold_and_selects_mean_metric[grade-capacity_63-mae]`: source spells `capaciy_63`, test expects `capacity_63`. It was also present in the initial full run (1,169 passed, 1 failed, 6 subtests). This is a BASELINE FAILURE, not an ablation regression; the suite is not green and the mismatch was not repaired.


After the final cache-context guard change, all **22 experimental tests passed** ([final_focused.log](../scripts/experiments/student_progress_20261010/final_focused.log)); the earlier combined suite contained 16 experimental tests. Six new tests failed before implementation and passed afterward, covering acceptance plus signed cross-run/year/specification/fit-row/validation-row transplant rejection ([context_red.log](../scripts/experiments/student_progress_20261010/context_red.log)). Checks also cover feature-order isolation, holdout partitioning, zero-credit GPA, hash/config changes, safe output namespaces, truthful completion and fixed-plan context. No later production code change occurred. Windows TEMP/TMP and pytest basetemp were rooted under isolated report validation directories.


Artifact verification: **PASS, 108 models** ([artifact_integrity.json](../data/evaluation/experiments/student_progress_20261010/artifact_integrity.json)); archived executed source and categories/config/rows checked ([artifact_verification.log](../scripts/experiments/student_progress_20261010/artifact_verification.log)). Old-cache rejection was executed before any fit ([old_cache_rejection.log](../scripts/experiments/student_progress_20261010/old_cache_rejection.log)). Three independent audit/review tasks completed; the final review found no remaining material issue. Graphify AST update is recorded in [graphify_update.log](../scripts/experiments/student_progress_20261010/graphify_update.log). Training log: [training.log](../scripts/experiments/student_progress_20261010/training.log); final byte protection: [isolation_verification.json](../data/evaluation/experiments/student_progress_20261010/isolation_verification.json).
