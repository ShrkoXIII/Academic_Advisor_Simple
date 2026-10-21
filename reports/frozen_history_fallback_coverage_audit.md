# Frozen History Fallback Coverage Audit

**Recommendation: CONDITIONAL**

This is a read-only audit of the current source, saved feature/evaluation artifacts, and the archived university payloads for the 30 primary `20251` pilot students. No code, data, model, history bundle, or contract was changed. No training or university request was run. The only new file is this report.

## Executive summary

- The current cascade is key-presence based. It selects the most specific available key among Levels 1–5, then Level 6 (global). `min_support=20` sets `course_history_missing`; it does **not** make the cascade try a less specific level.
- On the saved V2 `20251` prediction records, Levels 1+2 cover **95.44% of records / 95.27% of credit hours**. Levels 3–5 account for **4.30% / 4.30%**, and Level 6 for **0.26% / 0.43%**.
- On the archived Courses API candidate rows, Level 1+2 coverage is estimated at **95.79% of candidate rows / 95.58% of candidate hours**. Across distinct candidate course IDs, **285/303 (94.06%)** have at least one Level 1 or Level 2 key. This estimate uses the archive's `STUDENTS_COUNT` and the existing temporal weights; the archive has no `attempt_sum` or `plan_requirement_type_id` field in Frozen History.
- Coverage is not the same as sufficient support. In the local V2 frozen state applied to those same candidate rows, **204/477 (42.8%)** of the Level 1+2 rows have `effective_support < 20`. The university-archive count estimate gives a similar but not identical **194/478 (40.6%)**. Count definitions have not been confirmed as equivalent, so these figures remain separately labelled.
- Removing Levels 3–5 would route **22/499 (4.41%)** candidate rows and **63/1,401.5 (4.50%)** candidate credit hours to Level 6 under the existing local V2 state. In the V2 saved `20251` evaluation, those levels represent **1,480/34,408 (4.30%)** prediction rows/hours. Aggregate loss is limited, but coverage loss is concentrated in some specialties and in a few pilot students.
- The current official history/model path is not directly compatible with the university archive. `attempt_sum` is required to compute existing average-attempt features and is required by the official Delta contract. It must remain absent rather than be inferred from `RETAKE_COUNT`. A compatible reduced history/model path is required before scoring with that source.

## Scope and denominators

Historical feature rates below count **student-course outcome rows that were actually used as model/prediction records**, not the number of rows in the Frozen History aggregate files. Credit-hour rates sum `course_credits` over those same rows. The `20251` course evaluation is matched one-to-one to its feature row using `(student_course_id, part_id)`.

The university estimate uses 30 archived `student_response.json` / `courses_response.json` pairs, 499 candidate rows, and 303 distinct candidate course IDs. Every archived candidate row had `IS_REQUESTABLE=Y` and `ALLOW_REGISTER=Y`, so the all-available and currently requestable/allowed denominators coincide. The unique-course figure is deduplicated by `COURSE_ID`; row and hour rates retain student-course pairs because different students can have different degrees and candidate sets.

`effective_support` from the local artifacts is the temporal-weighted outcome-row sum (`0.25` before 2022, `1.0` from 2022 onward), not an unweighted row count. The university-archive estimate applies the same weights to `STUDENTS_COUNT` as a proxy. This proxy is conditional on the university count having the same finalized-outcome denominator as the model history; that definition has not been confirmed.

## Current selection, smoothing, and missingness

`src/features/temporal_features.py` builds these lookup keys:

| Level | Lookup key |
| --- | --- |
| 1 | `(degree_id, course_id)` |
| 2 | `course_id` |
| 3 | `(degree_id, plan_requirement_type_id, rounded course_credits)` |
| 4 | `(faculty_id, plan_requirement_type_id, rounded course_credits)` |
| 5 | `(plan_requirement_type_id, rounded course_credits)` |
| 6 | Global aggregate, used if no Level 1–5 key exists |

The implementation initializes each row to Level 6 and iterates levels 5 down to 1, overwriting a row whenever the keyed aggregate exists. The final choice is therefore Level 1 if present, otherwise Level 2, then 3, 4, 5, and global Level 6. A lower level is selected when the more specific key is absent, not when its support is small.

For Levels 1–5, each reported historical mean is smoothed toward the global mean:

`(local weighted sum + 20 × global mean) / (local effective_support + 20)`

`smoothing_k=20`; the global Level 6 value is the global mean. `effective_support` is the sum of temporal weights. `course_history_missing=1` when the selected level is 3 or higher **or** the selected support is under 20. Thus support below 20 is a warning flag, not a fallback trigger; Levels 1 and 2 can be selected with low support and flagged missing. Conversely, Level 5 can have enormous support while still being marked missing because its key is broad.

The current feature output includes seven course-history fields: average mark, fail rate, average attempt, retake rate, effective support, fallback level, and missingness. `compute_plan_context_features()` derives plan-wide and leave-one-course-out peer features from these per-course values.

## Historical fallback rates

These are counts on saved feature rows, with hours weighted by each row's `course_credits`. V1 and V2 are kept separate. Training rows describe historical walk-forward feature construction; target-20251 rows are the retrospective held-out course-prediction records.

| Source | Rows | L1 | L2 | L3 | L4 | L5 | L6 | L1+L2 rows / hours | L3–L5 rows / hours | `support < 20` rows / hours |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| V1 train features | 365,585 | 320,238 (87.60%) | 8,592 (2.35%) | 4,247 (1.16%) | 1,710 (0.47%) | 2,967 (0.81%) | 27,831 (7.61%) | 89.95% / 89.86% | 2.44% / 2.53% | 23.82% / 23.22% |
| V2 train features | 356,816 | 312,427 (87.56%) | 8,506 (2.38%) | 4,214 (1.18%) | 1,684 (0.47%) | 2,939 (0.82%) | 27,046 (7.58%) | 89.94% / 89.86% | 2.48% / 2.56% | 24.19% / 23.51% |
| V1 target 20251 | 34,922 | 32,534 (93.16%) | 819 (2.35%) | 108 (0.31%) | 0 (0.00%) | 1,372 (3.93%) | 89 (0.25%) | 95.51% / 95.34% | 4.24% / 4.24% | 9.86% / 9.28% |
| V2 target 20251 | 34,408 | 32,020 (93.06%) | 819 (2.38%) | 108 (0.31%) | 0 (0.00%) | 1,372 (3.99%) | 89 (0.26%) | 95.44% / 95.27% | 4.30% / 4.30% | 10.08% / 9.49% |

The percentages in the individual `L1`–`L6` columns are record shares; the two columns containing a slash give record share / credit-hour share. Level 4 had no rows in either saved 20251 test set. These tables do not combine V1 and V2. The V2 20252 saved test feature file was not used to support the pilot decision because prior repository audit evidence identifies that saved semester as stale relative to the current feature implementation; 20251 is reported on its own.

### V2 semester and specialty variation

Direct Level 1+2 share in the V2 training feature rows varied by semester (record share / hour share):

| Part | L1+L2 records | L1+L2 hours |
| --- | ---: | ---: |
| 20201 | 0.0% | 0.0% |
| 20202 | 94.8% | 93.7% |
| 20203 | 98.6% | 98.6% |
| 20211 | 99.6% | 99.5% |
| 20212 | 99.8% | 99.8% |
| 20213 | 99.9% | 99.9% |
| 20221 | 90.3% | 90.0% |
| 20222 | 97.5% | 97.4% |
| 20223 | 99.1% | 99.0% |
| 20231 | 95.2% | 95.7% |
| 20232 | 97.8% | 97.7% |
| 20233 | 99.3% | 99.2% |
| 20241 | 98.3% | 98.6% |
| 20242 | 99.6% | 99.6% |
| 20243 | 99.2% | 99.1% |

The first semester has no earlier outcome history, so its zero direct coverage is expected from the walk-forward cutoff, not evidence that the global fallback failed.

For target `20251`, V2 has 48 `degree_id` groups. The ten largest groups by outcome-row count all had 100% Level 1+2 coverage. Coverage is uneven outside them: 12 groups (2,245 rows total) had under 90% Level 1+2 coverage. Six groups had only 19.2%–19.7% direct coverage, with 80.3%–80.8% of rows using Level 3–5. This concentration means the aggregate 4.30% loss understates the effect on affected specialties. These are degree IDs, not a claim about program names or a population-wide specialty rate.

### Support quality and GPA strata in V2

Among V2 target-20251 prediction rows, mean effective support by fallback was: Level 1 **318.3**, Level 2 **1,115.5**, Level 3 **64.4**, Level 5 **66,955.9**, and Level 6 **258,532.2**. The Level 3–5 combined mean was 62,074.6 (median 69,587.3), driven by Level 5. That large support is count quantity for a broad requirement-type/credit key; it does not establish that the pooled courses share a relevant difficulty distribution.

| `start_agpa_points` band | Rows | L1+L2 | L3–L5 | L6 | Support <20 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0–1 | 10,565 | 86.03% | 13.13% | 0.84% | 1.55% |
| >1–2 | 2,093 | 99.57% | 0.43% | 0.00% | 8.07% |
| >2–3 | 17,024 | 99.55% | 0.45% | 0.00% | 13.90% |
| >3–4 | 4,726 | 99.85% | 0.15% | 0.00% | 16.29% |

The low-GPA band has distinctly less Level 1+2 coverage and more Level 3–5 use. A low count of `support < 20` does not negate that fallback pattern: Level 5 can have very high support and still be semantically broad and flagged `course_history_missing`.

## University 20251 candidate archive estimate

The archive contains 15 per-semester Frozen History JSON files from 20201 through 20243 and 30 student/course payload pairs. Its Frozen History rows have `COURSE_ID`, `PART_ID`, `DEGREE_ID`, `FACULTY_ID`, `COURSE_CREDITS`, and aggregate counts/marks, but do not have a requirement-type field or `attempt_sum`. The 499 available-course rows carry `REQUIREMENT_TYPE_ID` in Courses API; that field can identify the student's current course requirement, but it cannot recover historical requirement grouping without a trusted time-valid crosswalk.

The following coverage is the university-archive estimate, using the Courses API course and degree IDs and weighted `STUDENTS_COUNT` support from the archive. It is not mixed with the local V2 state:

| Estimated selection | Candidate rows | Rows | Candidate hours | Hours | Mean support / median |
| --- | ---: | ---: | ---: | ---: | ---: |
| Level 1, `(degree, course)` | 499 | 418 (83.77%) | 1,401.5 | 1,171.5 (83.59%) | 128.9 / 34.5 |
| Level 2, `course` | 499 | 60 (12.02%) | 1,401.5 | 168.0 (11.99%) | 230.5 / 33.0 |
| No Level 1 or 2 key; use global | 499 | 21 (4.21%) | 1,401.5 | 62.0 (4.42%) | 310,966 global weighted count* |
| **Level 1+2 combined** | **499** | **478 (95.79%)** | **1,401.5** | **1,339.5 (95.58%)** | — |

At the distinct-material grain, 265/303 candidate course IDs (87.46%) have Level 1, and 285/303 (94.06%) have Level 1 or 2. The remaining 18 unique course IDs account for 21 student-course rows. Across the 30 students, mean direct coverage is 95.9% by rows and 95.7% by hours; three students have under 90% row coverage, and the minimum student row/hour coverage is 50.0% / 41.2%. This demonstrates why the candidate-row, distinct-course, and per-student units must be kept separate.

*Global support is the sum of archived `STUDENTS_COUNT × temporal_weight` over all archived aggregate rows. It is only an archive-derived count proxy until the university confirms that `STUDENTS_COUNT` means finalized outcome rows under the same exclusions and denominator as the local feature pipeline. It must not be interpreted as independent student count.

The local saved V2 `as_of_20243` state applied read-only to the same candidate rows selects L1 for 415, L2 for 62, L3 for 10, L5 for 12, and Level 6 for none. It therefore estimates 95.59% L1+L2 row coverage and 95.50% hours, close to but not identical to the API aggregate estimate. This is a cross-check against the local state, not a replacement for the archive estimate. Its L3–L5 rows would move to Level 6 if those levels were disabled: **22/499 (4.41%) rows**, **63/1,401.5 (4.50%) hours**, and **19/303 (6.27%) distinct course IDs**; mean support is **24,241.9**. Level 3 accounts for 10 rows / 7 distinct courses at mean support 146.6; Level 5 accounts for 12 rows / 12 distinct courses at mean support 44,321.3. The archive-only L1/L2 coverage estimate instead finds 18 distinct course IDs without either key; that small difference reflects source/count/key differences and should not be hidden by merging the measures.

Support under 20 remains common in direct candidate coverage. In the local-state application, 204/477 Level 1+2 rows (42.8%) have support under 20. By the six fixed sample GPA categories in `students.csv`, direct row/hour coverage and low support among directly covered rows were:

| Fixed sample GPA category | Students | Candidate rows | L1+L2 rows | L1+L2 hours | Covered rows with support <20 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `gpa_0_no_observed_prior_outcomes` | 5 | 110 | 89.09% | 89.62% | 28.57% |
| `gpa_0_with_observed_prior_outcomes` | 5 | 65 | 100.00% | 100.00% | 30.77% |
| `gpa_gt_0_le_1` | 5 | 90 | 100.00% | 100.00% | 28.89% |
| `gpa_gt_1_le_2` | 5 | 78 | 100.00% | 100.00% | 34.62% |
| `gpa_gt_2_le_3` | 5 | 60 | 90.00% | 90.06% | 79.63% |
| `gpa_gt_3_le_4` | 5 | 96 | 95.83% | 95.60% | 63.04% |

Three fixed-sample students in the `gpa_0_no_observed_prior_outcomes` and `gpa_gt_2_le_3` categories account for the below-90% per-student coverage cases. No student IDs are included here. The two GPA sources in the archive disagree: `student_response.json` `START_AGPA_POINTS` differs from the frozen `students.csv` `previous_gpa` for **17/30** students (all five in each of the `0–1` and `1–2` categories, plus seven in the two higher categories). These rates use the selection-stratum GPA in `students.csv`, as it is the source tied to the fixed evaluation sample; the university snapshot's GPA discrepancy needs resolving before per-student performance is treated as representative of that API snapshot.

## Counterfactual: remove Levels 3–5

At lookup time, every row currently selected at Level 3, 4, or 5 would resolve to Level 6 if those tables/keys were removed, assuming global totals remain available and the implementation is changed to skip those tables. It would not automatically be rescued by Level 2 when the current course-only key is absent; it would go directly to global.

| Read-only counterfactual source | Current L3–L5 rows | Share of rows | Hours share | Mean effective support in current L3–L5 rows | Result after removal |
| --- | ---: | ---: | ---: | ---: | --- |
| V1 target 20251 | 1,480 / 34,922 | 4.24% | 4.24% | 63,316.3 | Level 6 |
| V2 target 20251 | 1,480 / 34,408 | 4.30% | 4.30% | 62,074.6 | Level 6 |
| University candidate rows scored by local V2 `as_of_20243` state | 22 / 499 | 4.41% | 4.50% | 24,241.9 | Level 6 |

In the university candidate cross-check, all 22 displaced rows are L3 or L5; there are no L4 rows and no current Level 6 rows. The support mean is highly skewed by L5. The university archive estimate independently shows 21/499 rows and 4.42% of hours with no L1/L2 key; it cannot identify whether those would have matched an old L3, L4, or L5 key because historical requirement grouping is absent.

### Level 2 pooling risk

Level 2 deliberately merges outcomes for a course ID across all degrees. That increases coverage but can mask degree-specific differences in course delivery, grading, cohorts, and curricula. In the local V2 state, the 62 pilot candidate rows selected at Level 2 cover 50 distinct course IDs. For all 50, other-degree Level 1 history existed for the same course; across those degree-specific rates, the candidate-course-weighted mean max-to-min historical fail-rate range was **0.172** (17.2 percentage points), with a row of courses reaching a 100-point range. The pooled Level 2 rate differed from the available degree-specific rates by a median **4.3 points** and a 90th percentile **10.2 points**. Those other-degree rates do not reveal the missing candidate degree's own true rate, so this is evidence of heterogeneity risk, not an estimate of error caused by Level 2.

## Observed prediction quality by fallback and GPA

The saved V2 course prediction file matches all 34,408 V2 target-20251 feature rows. Bias below is `predicted_mark - actual_mark`; failure is the **observed** actual failure share (`final_mark < 50`), not the classifier's predicted failure rate. These are retrospective, selected fallback strata; they are descriptive and do not estimate the causal effect of changing fallback policy.

| V2 target 20251 fallback | Rows | MAE (marks) | Bias (marks) | Observed failure rate | Mean support |
| --- | ---: | ---: | ---: | ---: | ---: |
| Level 1 | 32,020 | 10.048 | +3.789 | 10.0% | 318.3 |
| Level 2 | 819 | 12.105 | +1.908 | 7.3% | 1,115.5 |
| Level 3 | 108 | 11.810 | +2.504 | 6.5% |
| Level 4 | 0 | — | — | — | — |
| Level 5 | 1,372 | 14.901 | +3.599 | 21.5% | 66,955.9 |
| Level 6 | 89 | 6.812 | +0.921 | 6.7% | 258,532.3 |

The Level 3 support mean is 64.4. Level 5's large support is not comparable to the course-specific support at Levels 1–2. In the `start_agpa_points` 0–1 band, Levels 1–2 have 9,089 rows (MAE about 11.82); Levels 3–5 have 1,387 rows (MAE about 14.85, bias +3.62, observed failure 21.3%). Almost all of that group is Level 5: 1,372 rows with MAE 14.901 and observed failure rate 21.5%. This supports extra caution for low-GPA students, but it does **not** prove that changing those rows to global Level 6 will improve predictions; Level 6 has only 89 selected observations and is a different population.

The V2 grade regressor's saved gain importance assigns 21.55% to `course_history_avg_mark`, 2.23% to `course_history_fail_rate`, 2.16% to `course_history_effective_support`, and 1.29% to `course_history_avg_attempt`. The fail-risk model assigns 15.78% to `course_history_fail_rate`, 3.59% to `course_history_avg_mark`, 2.82% to support, 1.33% to average attempt, and 0.29% to `course_history_fallback_level`. `plan_requirement_type_id` also appears in both model contracts/importance lists. Gain importance is not a causal measure, but it confirms that these history and context fields are active model inputs.

An existing separate `attempt_sum` removal experiment reports small, mixed model-level changes for its reduced feature/model variant. That experiment is not a fallback-level ablation and cannot validate removal of Levels 3–5. In particular, it does not make an archive without `attempt_sum` compatible with the current official state or model contract.

## Dependencies to resolve before a university-backed run

### `plan_requirement_type_id`

- **Inside Frozen History:** it is one component of Levels 3–5, is listed in `HISTORY_SOURCE_COLUMNS`, and is part of the official Delta key. If the new source supports only Levels 1, 2, and global, it need not be present in each incoming history aggregate for those lookup keys. The current builder and updater still expect it and build all five tables, so a reduced history schema/state/load path must be explicitly made compatible before the current loader can consume the archive.
- **Outside Frozen History:** keep the field in candidate/catalog data unless a separate contract change is approved. `feature_contract.py` includes `plan_requirement_type_id` as a categorical model input; `recommendation/inputs.py` and `api/adapters/courses.py` map the Courses API `REQUIREMENT_TYPE_ID` into it; requirement constraints group candidate courses by this field. The user-provided Courses API archive contains this field. Removing it from all inputs would break model, shortlist/plan, and academic requirement constraints even if history no longer uses it.
- **Specialty experiment:** `experiments/specialty_history.py` calculates degree and degree-plus-requirement histories and requires this field on its training source. It is an optional experiment, separate from the base V2 Frozen History, but it cannot use historical aggregate payloads without a reliable time-valid requirement crosswalk.
- **Training-serving parity:** if Levels 3–5 are disabled at serving, feature generation/evaluation and model metadata must represent the same reduced contract. Otherwise the model sees a changed fallback-level distribution, support, historical means, and missingness than it saw during training.

### `attempt_sum`

- `temporal_features.py` stores `attempt_sum` in each history sum table/global total, uses it to generate `course_history_avg_attempt`, and uses that feature to derive `plan_credit_weighted_avg_attempt` and `peer_credit_weighted_avg_attempt`.
- All three fields are in the official base model feature contract. Current model artifacts and plan-context features therefore cannot be paired with university history by inventing a mean attempt.
- `recommendation/history_update.py` requires `attempt_sum` in its official Delta columns and validates its arithmetic relationship to count/retake counts. The university Frozen History archive does not provide it.
- `RETAKE_COUNT` is not a substitute for `attempt_sum`: a count of repeat events does not provide the sum of attempt numbers. Do not derive or impute it.
- Before a reduced-history run, use the already documented reduced feature contract/model path or otherwise establish a compatible model and history updater. The previously recorded `attempt_sum` experiment identifies the removed fields as the course-history average attempt and its plan/peer weighted derivatives, while retaining candidate `attempt_number` and the distinct retake-rate feature. This is separate from deleting fallback levels.

## Recommendation and conditions

**CONDITIONAL — adequate coverage to test a reduced history source on the archived 30-student candidate set, but not ready to plug into the current official Frozen History/model path.**

Reasons:

1. Both the retrospective V2 target-20251 records and the direct 30-student candidate archive put Level 1+2 coverage near 95% by rows and hours.
2. The 4–4.5% displaced by removing Levels 3–5 is not evenly distributed: some V2 specialties had only about 20% direct coverage; Level 3–5 candidate rows have broad/heterogeneous support; and the fixed pilot's no-prior-outcome and higher-GPA groups include rows that would lose direct fallback coverage.
3. Direct coverage often has low support: about 41–43% of covered pilot rows have effective support below 20. `min_support` flags those cases but does not find them more data. The historical pilot set's high-GPA categories have the largest low-support shares.
4. The archived university counts are sufficient to estimate Level 1/2 key presence, but the university has not confirmed that `STUDENTS_COUNT`, failure counts, marks, and repeat counts share the local finalized-outcome definitions. Frozen History also lacks `attempt_sum` and historical requirement type. The archived student snapshot's GPA differs from the fixed sample source for 17 students.
5. Current official model and history-update contracts still consume `attempt_sum`; candidate `plan_requirement_type_id` remains necessary outside Frozen History. A Level 1/2/global history alone is not a drop-in replacement.

For the stated order of work, run the original-feature baseline with the existing compatible V2 inputs first. Before testing the university history, define a separate reduced history/model contract that explicitly carries Levels 1, 2, and global, preserves support/missingness semantics, does not synthesize `attempt_sum`, and keeps candidate-side requirement IDs for modeling and academic constraints. Resolve the aggregate count definitions, 20201–20243 completeness, and GPA snapshot mismatch; then compare per-student outcomes with particular attention to the five fixed low-GPA strata and cases whose direct-history coverage is lowest.

## Evidence paths

- Logic and feature contract: `src/features/temporal_features.py`, `src/features/frozen_history.py`, `src/features/feature_contract.py`, `src/features/build_temporal_features.py`.
- Candidate API mapping and academic requirements: `src/api/adapters/courses.py`, `src/recommendation/inputs.py`, `src/recommendation/constraints.py`.
- Optional specialty aggregates: `src/experiments/specialty_history.py`.
- Official update contract: `src/recommendation/history_update.py`.
- Historical V1/V2 features: `data/features/temporal_train_features.parquet`, `data/features/temporal_train_features_v2.parquet`, and corresponding test files.
- V1/V2 retrospective course predictions: `data/evaluation/plan_gpa_course_predictions_2025.parquet`, `data/evaluation/plan_gpa_course_predictions_2025_v2.parquet`.
- V2 metadata/importances: `models/model_metadata_v2.json`.
- Pilot sample and archived university payloads: `data/evaluation/recommendation_pilot_20251/students.csv`, `data/evaluation/recommendation_pilot_20251/api_data/frozen_history/`, and `data/evaluation/recommendation_pilot_20251/api_data/students/`.
- Existing attempt-sum dependency experiment: `reports/attempt_sum_removal_experiment.md`.
