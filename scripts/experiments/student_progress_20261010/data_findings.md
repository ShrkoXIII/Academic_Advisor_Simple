# Student progress: empirical data audit

Analysis window: target parts 20201–20243 (2020–2024). No 2025 feature table was opened. Separate 2025 raw/clean status summaries are source diagnostics only. No model was trained or evaluated.

These are empirical relations in the provided extract. The SQL/view definition and database business semantics were not supplied, so field names and source comments do not independently verify semantics.

## Main findings

- The four fields have no missing values in clean V1/V2 or training V2. Raw 2020–2024 has 11 missing values per field. Training has 356,816 course rows and 75,076 status groups; all four fields and both aliases are constant inside each status group.
- Start and registration totals are correlated but differ: credits Pearson 0.898350, equal 27.3968%; courses Pearson 0.901001, equal 28.2173%. No directed pair is globally deterministic in any of the five grains/datasets. This does not establish whether a field helps a trained model.
- On 70,054 adjacent clean V2 status transitions, registration credits follow previous cumulative total plus previous semester registration with 1 mismatch (0.001427%). Start credits equal previous end credits with 4,158 mismatches (5.9354%). The timing evidence supports a prior-semester interpretation of total registration credits; it is not a verified SQL/view contract.
- V1/V2 share 82,300 status keys with zero mismatches across 18 progress/semester columns; V2 adds 5,592 rows. Matched raw/clean and clean/training checks preserve the four fields exactly. Both prior aliases equal original total registration fields on all training rows.
- Simple passed/failed decompositions are not exact identities: roughly half the clean status rows fail total registration = total passed + total failed, and roughly half fail start in = total passed. Do not substitute these fields using those formulas.

## Grain and reproducibility

`train_v2_course` weights a semester by its finalized course rows. `train_v2_status` uses one student/degree/part and means of its course labels (`points`, `final_mark`, `is_fail`); these are not GPA labels. Clean/raw windows use status rows. All six unordered field pairs and twelve directed mappings are tested. Statistics use sample standard deviation; equality is exact, identities additionally use absolute tolerance 1e-8. Missing pairs are excluded. Progress quartiles use `start_total_in_credits` separately per dataset; tied cut points can reduce bins. Stratified groups need at least 100 rows; excluded counts are in `group_inventory.csv`.

| dataset | path | physical_rows | window_rows | duplicate_status_keys_window |
| --- | --- | --- | --- | --- |
| raw | data/raw/v_add_student_degree_status.parquet | 189158 | 92741 | 0 |
| clean_v1 | data/clean/student_status.parquet | 95622 | 82300 | 0 |
| clean_v2 | data/clean/student_status_v2.parquet | 107939 | 87892 | 0 |
| train_v2 | data/features/temporal_train_features_v2.parquet | 356816 | 356816 | 281740 |

## Distributions

| dataset | field | rows | missing | missing_pct | unique | mean | median | min | max | std |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| raw | start_total_in_credits | 92741 | 11 | 0.011861 | 394 | 79.2849 | 70 | 0 | 253 | 62.0967 |
| raw | start_total_in_courses | 92741 | 11 | 0.011861 | 82 | 27.8064 | 25 | 0 | 81 | 21.0214 |
| raw | total_reg_credits | 92741 | 11 | 0.011861 | 1003 | 105.794 | 90 | 0 | 996 | 88.1389 |
| raw | total_reg_courses | 92741 | 11 | 0.011861 | 235 | 36.8811 | 32 | 0 | 278 | 29.7427 |
| clean_v1 | start_total_in_credits | 82300 | 0 | 0 | 392 | 83.321 | 76 | 0 | 251 | 60.3407 |
| clean_v1 | start_total_in_courses | 82300 | 0 | 0 | 82 | 29.2899 | 27 | 0 | 81 | 20.5257 |
| clean_v1 | total_reg_credits | 82300 | 0 | 0 | 980 | 109.231 | 96 | 0 | 996 | 85.6642 |
| clean_v1 | total_reg_courses | 82300 | 0 | 0 | 228 | 38.1276 | 34 | 0 | 278 | 28.9115 |
| clean_v2 | start_total_in_credits | 87892 | 0 | 0 | 393 | 83.2835 | 75 | 0 | 253 | 61.1825 |
| clean_v2 | start_total_in_courses | 87892 | 0 | 0 | 82 | 29.2017 | 27 | 0 | 81 | 20.6503 |
| clean_v2 | total_reg_credits | 87892 | 0 | 0 | 1003 | 110.77 | 96 | 0 | 996 | 87.324 |
| clean_v2 | total_reg_courses | 87892 | 0 | 0 | 235 | 38.5979 | 34 | 0 | 278 | 29.3881 |
| train_v2_course | start_total_in_credits | 356816 | 0 | 0 | 379 | 77.9355 | 73 | 0 | 250 | 55.8228 |
| train_v2_course | start_total_in_courses | 356816 | 0 | 0 | 82 | 28.2012 | 26 | 0 | 81 | 20.2223 |
| train_v2_course | total_reg_credits | 356816 | 0 | 0 | 760 | 95.8677 | 86 | 0 | 495 | 72.052 |
| train_v2_course | total_reg_courses | 356816 | 0 | 0 | 163 | 34.4427 | 31 | 0 | 169 | 25.9649 |
| train_v2_status | start_total_in_credits | 75076 | 0 | 0 | 379 | 81.8158 | 74 | 0 | 250 | 59.5576 |
| train_v2_status | start_total_in_courses | 75076 | 0 | 0 | 82 | 28.8156 | 27 | 0 | 81 | 20.3799 |
| train_v2_status | total_reg_credits | 75076 | 0 | 0 | 760 | 102.196 | 90 | 0 | 495 | 77.0704 |
| train_v2_status | total_reg_courses | 75076 | 0 | 0 | 163 | 35.7694 | 32 | 0 | 169 | 26.4477 |

## All pair relationships

| dataset | a | b | pearson | spearman | equal_pct | a_minus_b_mean | a_minus_b_min | a_minus_b_max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| raw | start_total_in_credits | start_total_in_courses | 0.960681 | 0.985638 | 11.9066 | 51.4785 | 0 | 189 |
| raw | start_total_in_credits | total_reg_credits | 0.861423 | 0.922293 | 24.3287 | -26.5093 | -769 | 103 |
| raw | start_total_in_credits | total_reg_courses | 0.821872 | 0.903294 | 11.4073 | 42.4037 | -136 | 192 |
| raw | start_total_in_courses | total_reg_credits | 0.828802 | 0.912694 | 10.8293 | -77.9878 | -934 | 24 |
| raw | start_total_in_courses | total_reg_courses | 0.860781 | 0.920302 | 24.993 | -9.07475 | -216 | 35 |
| raw | total_reg_credits | total_reg_courses | 0.962343 | 0.985578 | 10.784 | 68.913 | 0 | 718 |
| clean_v1 | start_total_in_credits | start_total_in_courses | 0.957151 | 0.98262 | 8.36452 | 54.0311 | 0 | 188 |
| clean_v1 | start_total_in_credits | total_reg_credits | 0.859762 | 0.91864 | 22.4326 | -25.9101 | -769 | 103 |
| clean_v1 | start_total_in_credits | total_reg_courses | 0.820185 | 0.897302 | 8.34629 | 45.1934 | -115 | 192 |
| clean_v1 | start_total_in_courses | total_reg_credits | 0.822045 | 0.90659 | 7.80559 | -79.9412 | -934 | 24 |
| clean_v1 | start_total_in_courses | total_reg_courses | 0.860181 | 0.917033 | 23.164 | -8.83774 | -216 | 35 |
| clean_v1 | total_reg_credits | total_reg_courses | 0.959511 | 0.983133 | 7.76063 | 71.1035 | 0 | 718 |
| clean_v2 | start_total_in_credits | start_total_in_courses | 0.95724 | 0.983292 | 8.25104 | 54.0818 | 0 | 189 |
| clean_v2 | start_total_in_credits | total_reg_credits | 0.852962 | 0.913566 | 21.4832 | -27.4864 | -769 | 103 |
| clean_v2 | start_total_in_credits | total_reg_courses | 0.810292 | 0.89193 | 7.99276 | 44.6856 | -136 | 192 |
| clean_v2 | start_total_in_courses | total_reg_credits | 0.817386 | 0.902271 | 7.41478 | -81.5682 | -934 | 24 |
| clean_v2 | start_total_in_courses | total_reg_courses | 0.85203 | 0.911447 | 22.1852 | -9.39625 | -216 | 35 |
| clean_v2 | total_reg_credits | total_reg_courses | 0.959587 | 0.983407 | 7.367 | 72.172 | 0 | 718 |
| train_v2_course | start_total_in_credits | start_total_in_courses | 0.964593 | 0.984383 | 10.1091 | 49.7344 | 0 | 187 |
| train_v2_course | start_total_in_credits | total_reg_credits | 0.89835 | 0.935258 | 27.3968 | -17.9322 | -360 | 103 |
| train_v2_course | start_total_in_credits | total_reg_courses | 0.866388 | 0.921047 | 9.98918 | 43.4928 | -115 | 192 |
| train_v2_course | start_total_in_courses | total_reg_credits | 0.867078 | 0.922888 | 9.60915 | -67.6665 | -433 | 24 |
| train_v2_course | start_total_in_courses | total_reg_courses | 0.901001 | 0.938036 | 28.2173 | -6.24151 | -115 | 35 |
| train_v2_course | total_reg_credits | total_reg_courses | 0.966697 | 0.984305 | 9.55422 | 61.425 | 0 | 367 |
| train_v2_status | start_total_in_credits | start_total_in_courses | 0.959266 | 0.983917 | 8.84304 | 53.0002 | 0 | 187 |
| train_v2_status | start_total_in_credits | total_reg_credits | 0.900141 | 0.932882 | 24.1569 | -20.3802 | -360 | 103 |
| train_v2_status | start_total_in_credits | total_reg_courses | 0.855574 | 0.91398 | 8.76312 | 46.0464 | -115 | 192 |
| train_v2_status | start_total_in_courses | total_reg_credits | 0.865203 | 0.920485 | 8.28893 | -73.3804 | -433 | 24 |
| train_v2_status | start_total_in_courses | total_reg_courses | 0.896312 | 0.932199 | 24.9547 | -6.95381 | -115 | 35 |
| train_v2_status | total_reg_credits | total_reg_courses | 0.961849 | 0.983476 | 8.23965 | 66.4266 | 0 | 367 |

Pairwise difference distributions (every observed value and its row frequency) are in `pair_difference_frequencies.csv`.

## Status group counts and stratified credit relationships

Training status groups use one student/degree/part. Every included stratum has at least 100 such groups; the same threshold is applied separately at course grain. Observed counts and exclusions:

| dataset | group_by | observed_groups | included_groups | excluded_below_100 | smallest_observed_group | smallest_included_group | largest_included_group |
| --- | --- | --- | --- | --- | --- | --- | --- |
| train_v2_status | degree_id | 43 | 38 | 5 | 7 | 117 | 15172 |
| train_v2_status | progress_quartile | 4 | 4 | 0 | 18466 | 18466 | 19133 |
| train_v2_status | year | 5 | 5 | 0 | 12772 | 12772 | 16500 |

Start-credit versus total-registration-credit correlations by training target year:

| group_value | group_rows | pearson | spearman | equal_pct | a_minus_b_mean |
| --- | --- | --- | --- | --- | --- |
| 2020 | 12772 | 0.896639 | 0.925018 | 23.6455 | -22.7158 |
| 2021 | 14706 | 0.903143 | 0.935949 | 24.9966 | -20.8339 |
| 2022 | 15685 | 0.897889 | 0.928751 | 21.9955 | -20.9968 |
| 2023 | 16500 | 0.902413 | 0.937001 | 23.8485 | -19.367 |
| 2024 | 15413 | 0.901386 | 0.937321 | 26.309 | -18.4689 |

Ranges over qualifying training-status degree and progress strata:

| group_by | groups | pearson_min | pearson_median | pearson_max | equality_pct_min | equality_pct_median | equality_pct_max |
| --- | --- | --- | --- | --- | --- | --- | --- |
| degree_id | 38 | 0.426167 | 0.883604 | 0.956398 | 0.651466 | 25.7734 | 66.7274 |
| progress_quartile | 4 | 0.400474 | 0.536785 | 0.679736 | 10.074 | 18.0691 | 49.804 |
| year | 5 | 0.896639 | 0.901386 | 0.903143 | 21.9955 | 23.8485 | 26.309 |

## Training target correlations

| dataset | feature | target | valid | pearson | spearman |
| --- | --- | --- | --- | --- | --- |
| train_v2_course | start_total_in_credits | points | 356816 | 0.0707788 | 0.044132 |
| train_v2_course | start_total_in_credits | final_mark | 356816 | 0.0610284 | 0.0441934 |
| train_v2_course | start_total_in_credits | is_fail | 356816 | -0.089245 | -0.0925701 |
| train_v2_course | start_total_in_courses | points | 356816 | 0.066468 | 0.0399489 |
| train_v2_course | start_total_in_courses | final_mark | 356816 | 0.0559781 | 0.040043 |
| train_v2_course | start_total_in_courses | is_fail | 356816 | -0.0905573 | -0.0926366 |
| train_v2_course | total_reg_credits | points | 356816 | -0.0655244 | -0.0732324 |
| train_v2_course | total_reg_credits | final_mark | 356816 | -0.0771113 | -0.0736967 |
| train_v2_course | total_reg_credits | is_fail | 356816 | 0.00023941 | -0.0175209 |
| train_v2_course | total_reg_courses | points | 356816 | -0.0672839 | -0.0739202 |
| train_v2_course | total_reg_courses | final_mark | 356816 | -0.0796982 | -0.0743662 |
| train_v2_course | total_reg_courses | is_fail | 356816 | -0.00216279 | -0.0192256 |
| train_v2_status | start_total_in_credits | points | 75076 | 0.125133 | 0.106361 |
| train_v2_status | start_total_in_credits | final_mark | 75076 | 0.114568 | 0.0993553 |
| train_v2_status | start_total_in_credits | is_fail | 75076 | -0.140303 | -0.156057 |
| train_v2_status | start_total_in_courses | points | 75076 | 0.115359 | 0.0985258 |
| train_v2_status | start_total_in_courses | final_mark | 75076 | 0.103532 | 0.0913795 |
| train_v2_status | start_total_in_courses | is_fail | 75076 | -0.143292 | -0.15232 |
| train_v2_status | total_reg_credits | points | 75076 | -0.0574658 | -0.0561794 |
| train_v2_status | total_reg_credits | final_mark | 75076 | -0.0632715 | -0.0637051 |
| train_v2_status | total_reg_credits | is_fail | 75076 | -0.00496636 | -0.0295055 |
| train_v2_status | total_reg_courses | points | 75076 | -0.0690373 | -0.0632837 |
| train_v2_status | total_reg_courses | final_mark | 75076 | -0.0762697 | -0.0708594 |
| train_v2_status | total_reg_courses | is_fail | 75076 | -0.00441526 | -0.0258505 |

## Directed deterministic mapping checks

| dataset | source | destination | valid | source_values | ambiguous_source_values | max_destination_values_per_source | rows_in_ambiguous_source_values | deterministic_on_observed_data |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| raw | start_total_in_credits | start_total_in_courses | 92730 | 394 | 356 | 24 | 80591 | False |
| raw | start_total_in_courses | start_total_in_credits | 92730 | 82 | 81 | 84 | 81690 | False |
| raw | start_total_in_credits | total_reg_credits | 92730 | 394 | 371 | 322 | 92707 | False |
| raw | total_reg_credits | start_total_in_credits | 92730 | 1003 | 794 | 114 | 82514 | False |
| raw | start_total_in_credits | total_reg_courses | 92730 | 394 | 371 | 101 | 92707 | False |
| raw | total_reg_courses | start_total_in_credits | 92730 | 235 | 202 | 228 | 82697 | False |
| raw | start_total_in_courses | total_reg_credits | 92730 | 82 | 82 | 435 | 92730 | False |
| raw | total_reg_credits | start_total_in_courses | 92730 | 1003 | 790 | 66 | 82504 | False |
| raw | start_total_in_courses | total_reg_courses | 92730 | 82 | 82 | 117 | 92730 | False |
| raw | total_reg_courses | start_total_in_courses | 92730 | 235 | 202 | 66 | 82697 | False |
| raw | total_reg_credits | total_reg_courses | 92730 | 1003 | 786 | 40 | 82493 | False |
| raw | total_reg_courses | total_reg_credits | 92730 | 235 | 202 | 130 | 82697 | False |
| clean_v1 | start_total_in_credits | start_total_in_courses | 82300 | 392 | 356 | 24 | 74605 | False |
| clean_v1 | start_total_in_courses | start_total_in_credits | 82300 | 82 | 81 | 84 | 75416 | False |
| clean_v1 | start_total_in_credits | total_reg_credits | 82300 | 392 | 369 | 269 | 82277 | False |
| clean_v1 | total_reg_credits | start_total_in_credits | 82300 | 980 | 770 | 110 | 75702 | False |
| clean_v1 | start_total_in_credits | total_reg_courses | 82300 | 392 | 369 | 92 | 82277 | False |
| clean_v1 | total_reg_courses | start_total_in_credits | 82300 | 228 | 197 | 224 | 75883 | False |
| clean_v1 | start_total_in_courses | total_reg_credits | 82300 | 82 | 82 | 392 | 82300 | False |
| clean_v1 | total_reg_credits | start_total_in_courses | 82300 | 980 | 767 | 64 | 75694 | False |
| clean_v1 | start_total_in_courses | total_reg_courses | 82300 | 82 | 82 | 110 | 82300 | False |
| clean_v1 | total_reg_courses | start_total_in_courses | 82300 | 228 | 197 | 63 | 75883 | False |
| clean_v1 | total_reg_credits | total_reg_courses | 82300 | 980 | 764 | 39 | 75687 | False |
| clean_v1 | total_reg_courses | total_reg_credits | 82300 | 228 | 197 | 125 | 75883 | False |
| clean_v2 | start_total_in_credits | start_total_in_courses | 87892 | 393 | 356 | 24 | 79567 | False |
| clean_v2 | start_total_in_courses | start_total_in_credits | 87892 | 82 | 81 | 84 | 80640 | False |
| clean_v2 | start_total_in_credits | total_reg_credits | 87892 | 393 | 371 | 322 | 87870 | False |
| clean_v2 | total_reg_credits | start_total_in_credits | 87892 | 1003 | 793 | 114 | 81200 | False |
| clean_v2 | start_total_in_credits | total_reg_courses | 87892 | 393 | 371 | 101 | 87870 | False |
| clean_v2 | total_reg_courses | start_total_in_credits | 87892 | 235 | 202 | 228 | 81384 | False |
| clean_v2 | start_total_in_courses | total_reg_credits | 87892 | 82 | 82 | 435 | 87892 | False |
| clean_v2 | total_reg_credits | start_total_in_courses | 87892 | 1003 | 789 | 66 | 81190 | False |
| clean_v2 | start_total_in_courses | total_reg_courses | 87892 | 82 | 82 | 117 | 87892 | False |
| clean_v2 | total_reg_courses | start_total_in_courses | 87892 | 235 | 202 | 66 | 81384 | False |
| clean_v2 | total_reg_credits | total_reg_courses | 87892 | 1003 | 785 | 40 | 81179 | False |
| clean_v2 | total_reg_courses | total_reg_credits | 87892 | 235 | 202 | 130 | 81384 | False |
| train_v2_course | start_total_in_credits | start_total_in_courses | 356816 | 379 | 348 | 23 | 318520 | False |
| train_v2_course | start_total_in_courses | start_total_in_credits | 356816 | 82 | 81 | 82 | 320745 | False |
| train_v2_course | start_total_in_credits | total_reg_credits | 356816 | 379 | 363 | 223 | 356765 | False |
| train_v2_course | total_reg_credits | start_total_in_credits | 356816 | 760 | 681 | 100 | 322521 | False |
| train_v2_course | start_total_in_credits | total_reg_courses | 356816 | 379 | 363 | 81 | 356765 | False |
| train_v2_course | total_reg_courses | start_total_in_credits | 356816 | 163 | 152 | 213 | 322678 | False |
| train_v2_course | start_total_in_courses | total_reg_credits | 356816 | 82 | 82 | 332 | 356816 | False |
| train_v2_course | total_reg_credits | start_total_in_courses | 356816 | 760 | 677 | 59 | 322488 | False |
| train_v2_course | start_total_in_courses | total_reg_courses | 356816 | 82 | 82 | 93 | 356816 | False |
| train_v2_course | total_reg_courses | start_total_in_courses | 356816 | 163 | 152 | 59 | 322678 | False |
| train_v2_course | total_reg_credits | total_reg_courses | 356816 | 760 | 674 | 36 | 322464 | False |
| train_v2_course | total_reg_courses | total_reg_credits | 356816 | 163 | 152 | 121 | 322678 | False |
| train_v2_status | start_total_in_credits | start_total_in_courses | 75076 | 379 | 348 | 23 | 67493 | False |
| train_v2_status | start_total_in_courses | start_total_in_credits | 75076 | 82 | 81 | 82 | 68437 | False |
| train_v2_status | start_total_in_credits | total_reg_credits | 75076 | 379 | 363 | 223 | 75060 | False |
| train_v2_status | total_reg_credits | start_total_in_credits | 75076 | 760 | 681 | 100 | 68812 | False |
| train_v2_status | start_total_in_credits | total_reg_courses | 75076 | 379 | 363 | 81 | 75060 | False |
| train_v2_status | total_reg_courses | start_total_in_credits | 75076 | 163 | 152 | 213 | 68880 | False |
| train_v2_status | start_total_in_courses | total_reg_credits | 75076 | 82 | 82 | 332 | 75076 | False |
| train_v2_status | total_reg_credits | start_total_in_courses | 75076 | 760 | 677 | 59 | 68802 | False |
| train_v2_status | start_total_in_courses | total_reg_courses | 75076 | 82 | 82 | 93 | 75076 | False |
| train_v2_status | total_reg_courses | start_total_in_courses | 75076 | 163 | 152 | 59 | 68880 | False |
| train_v2_status | total_reg_credits | total_reg_courses | 75076 | 760 | 674 | 36 | 68796 | False |
| train_v2_status | total_reg_courses | total_reg_credits | 75076 | 163 | 152 | 121 | 68880 | False |

## Concept identity checks

| dataset | identity | valid | mismatch | mismatch_pct | difference_mean | difference_min | difference_max |
| --- | --- | --- | --- | --- | --- | --- | --- |
| raw | total_reg_credits = total_pass + total_fail | 92730 | 49486 | 53.3657 | 6.48529 | -5 | 181 |
| raw | start_total_in_credits = total_pass | 92730 | 44740 | 48.2476 | -2.33064 | -176 | 103 |
| raw | start_total_in_credits = total_reg - total_fail | 92730 | 62332 | 67.2188 | -8.81593 | -182 | 103 |
| raw | end_total_in_credits = start_total_in + semester_pass | 92730 | 2410 | 2.59894 | 0.282012 | -22 | 112 |
| raw | semester_reg_credits = semester_pass + semester_fail | 92730 | 17806 | 19.202 | 1.0452 | -18 | 25 |
| raw | end_total_in_credits = start_total_in + semester_in | 92730 | 1261 | 1.35986 | -0.0530357 | -45 | 0 |
| raw | total_reg_courses = total_pass + total_fail | 92730 | 49469 | 53.3474 | 2.31766 | -2 | 62 |
| raw | start_total_in_courses = total_pass | 92730 | 43944 | 47.3892 | -0.699019 | -62 | 35 |
| raw | start_total_in_courses = total_reg - total_fail | 92730 | 61712 | 66.5502 | -3.01668 | -74 | 35 |
| raw | end_total_in_courses = start_total_in + semester_pass | 92730 | 3845 | 4.14645 | 0.086919 | -10 | 34 |
| raw | semester_reg_courses = semester_pass + semester_fail | 92730 | 17840 | 19.2386 | 0.379758 | -7 | 11 |
| raw | end_total_in_courses = start_total_in + semester_in | 92730 | 2730 | 2.94403 | -0.036644 | -16 | 0 |
| clean_v1 | total_reg_credits = total_pass + total_fail | 82300 | 44423 | 53.9769 | 6.20201 | -5 | 152 |
| clean_v1 | start_total_in_credits = total_pass | 82300 | 41273 | 50.1495 | -2.34549 | -176 | 103 |
| clean_v1 | start_total_in_credits = total_reg - total_fail | 82300 | 56803 | 69.0194 | -8.5475 | -176 | 103 |
| clean_v1 | end_total_in_credits = start_total_in + semester_pass | 82300 | 2336 | 2.8384 | 0.308117 | -22 | 112 |
| clean_v1 | semester_reg_credits = semester_pass + semester_fail | 82300 | 14895 | 18.0984 | 0.796701 | 0 | 24 |
| clean_v1 | total_reg_courses = total_pass + total_fail | 82300 | 44405 | 53.955 | 2.21756 | -2 | 47 |
| clean_v1 | start_total_in_courses = total_pass | 82300 | 40535 | 49.2527 | -0.695176 | -57 | 35 |
| clean_v1 | start_total_in_courses = total_reg - total_fail | 82300 | 56195 | 68.2807 | -2.91273 | -60 | 35 |
| clean_v1 | end_total_in_courses = start_total_in + semester_pass | 82300 | 3761 | 4.56987 | 0.0946051 | -10 | 34 |
| clean_v1 | semester_reg_courses = semester_pass + semester_fail | 82300 | 14928 | 18.1385 | 0.288433 | 0 | 8 |
| clean_v2 | total_reg_credits = total_pass + total_fail | 87892 | 48673 | 55.3782 | 6.70748 | -5 | 154 |
| clean_v2 | start_total_in_credits = total_pass | 87892 | 44233 | 50.3265 | -2.4218 | -176 | 103 |
| clean_v2 | start_total_in_credits = total_reg - total_fail | 87892 | 61408 | 69.8676 | -9.12927 | -182 | 103 |
| clean_v2 | end_total_in_credits = start_total_in + semester_pass | 87892 | 2361 | 2.68625 | 0.294145 | -22 | 112 |
| clean_v2 | semester_reg_credits = semester_pass + semester_fail | 87892 | 17363 | 19.7549 | 1.06039 | 0 | 25 |
| clean_v2 | total_reg_courses = total_pass + total_fail | 87892 | 48653 | 55.3554 | 2.39555 | -2 | 53 |
| clean_v2 | start_total_in_courses = total_pass | 87892 | 43450 | 49.4357 | -0.724673 | -57 | 35 |
| clean_v2 | start_total_in_courses = total_reg - total_fail | 87892 | 60785 | 69.1587 | -3.12023 | -69 | 35 |
| clean_v2 | end_total_in_courses = start_total_in + semester_pass | 87892 | 3786 | 4.30756 | 0.0905202 | -10 | 34 |
| clean_v2 | semester_reg_courses = semester_pass + semester_fail | 87892 | 17396 | 19.7925 | 0.385382 | 0 | 11 |

## Lagged source transitions

Transitions group by student/degree; rows with ambiguous duplicate raw keys are excluded. `all_observed` may contain gaps. `calendar_adjacent_1_2_3` includes differences 1 or 8 between normal semester codes; semester-4 raw rows may disrupt adjacency. Current rows are limited to 2020–2024. Prior rows may predate 2020. Missing prior status history and filtering can explain failures and are not automatically leakage.

| cohort | dataset | identity | valid | mismatch | mismatch_pct | difference_mean | difference_min | difference_max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all_observed | raw | current_start_total_in_credits = previous_end_total_in | 82173 | 4942 | 6.01414 | -0.233556 | -24.5 | 32 |
| all_observed | raw | current_total_reg_credits = previous_total_reg + previous_semester_reg | 82173 | 7 | 0.00851861 | 0.00045027 | -72 | 32 |
| all_observed | raw | current_total_pass_credits = previous_total_pass + previous_semester_pass | 82173 | 6 | 0.00730167 | 8.51861e-05 | -72 | 32 |
| all_observed | raw | current_total_fail_credits = previous_total_fail + previous_semester_fail | 82173 | 5 | 0.00608472 | 2.43389e-05 | -3 | 3 |
| all_observed | raw | current_total_reg_credits = previous_total_reg + CURRENT_semester_reg_control | 82173 | 72204 | 87.8683 | 0.3831 | -57 | 46 |
| all_observed | raw | current_start_total_in_courses = previous_end_total_in | 82173 | 4940 | 6.01171 | -0.0788702 | -8 | 11 |
| all_observed | raw | current_total_reg_courses = previous_total_reg + previous_semester_reg | 82173 | 2159 | 2.62738 | -0.0259939 | -21 | 12 |
| all_observed | raw | current_total_pass_courses = previous_total_pass + previous_semester_pass | 82173 | 1594 | 1.93981 | -0.0192764 | -21 | 11 |
| all_observed | raw | current_total_fail_courses = previous_total_fail + previous_semester_fail | 82173 | 488 | 0.593869 | -0.0058535 | -1 | 2 |
| all_observed | raw | current_total_reg_courses = previous_total_reg + CURRENT_semester_reg_control | 82173 | 66787 | 81.2761 | 0.172027 | -22 | 14 |
| calendar_adjacent_1_2_3 | raw | current_start_total_in_credits = previous_end_total_in | 74185 | 4480 | 6.03896 | -0.233929 | -24.5 | 16 |
| calendar_adjacent_1_2_3 | raw | current_total_reg_credits = previous_total_reg + previous_semester_reg | 74185 | 1 | 0.00134798 | -0.000970547 | -72 | 0 |
| calendar_adjacent_1_2_3 | raw | current_total_pass_credits = previous_total_pass + previous_semester_pass | 74185 | 1 | 0.00134798 | -0.000970547 | -72 | 0 |
| calendar_adjacent_1_2_3 | raw | current_total_fail_credits = previous_total_fail + previous_semester_fail | 74185 | 2 | 0.00269596 | -8.08789e-05 | -3 | 0 |
| calendar_adjacent_1_2_3 | raw | current_total_reg_credits = previous_total_reg + CURRENT_semester_reg_control | 74185 | 66225 | 89.2701 | 0.405682 | -57 | 46 |
| calendar_adjacent_1_2_3 | raw | current_start_total_in_courses = previous_end_total_in | 74185 | 4479 | 6.03761 | -0.0792343 | -8 | 7 |
| calendar_adjacent_1_2_3 | raw | current_total_reg_courses = previous_total_reg + previous_semester_reg | 74185 | 1794 | 2.41828 | -0.0244793 | -21 | 0 |
| calendar_adjacent_1_2_3 | raw | current_total_pass_courses = previous_total_pass + previous_semester_pass | 74185 | 1313 | 1.7699 | -0.0179956 | -21 | 0 |
| calendar_adjacent_1_2_3 | raw | current_total_fail_courses = previous_total_fail + previous_semester_fail | 74185 | 421 | 0.5675 | -0.005675 | -1 | 0 |
| calendar_adjacent_1_2_3 | raw | current_total_reg_courses = previous_total_reg + CURRENT_semester_reg_control | 74185 | 61805 | 83.312 | 0.14759 | -22 | 11 |
| all_observed | clean_v1 | current_start_total_in_credits = previous_end_total_in | 70781 | 4522 | 6.38872 | -0.247877 | -24.5 | 32 |
| all_observed | clean_v1 | current_total_reg_credits = previous_total_reg + previous_semester_reg | 70781 | 1515 | 2.1404 | 0.231284 | -72 | 106 |
| all_observed | clean_v1 | current_total_pass_credits = previous_total_pass + previous_semester_pass | 70781 | 4 | 0.00565123 | -0.000254306 | -72 | 32 |
| all_observed | clean_v1 | current_total_fail_credits = previous_total_fail + previous_semester_fail | 70781 | 382 | 0.539693 | 0.0289414 | -3 | 33 |
| all_observed | clean_v1 | current_total_reg_credits = previous_total_reg + CURRENT_semester_reg_control | 70781 | 62851 | 88.7964 | 0.915832 | -57 | 108 |
| all_observed | clean_v1 | current_start_total_in_courses = previous_end_total_in | 70781 | 4520 | 6.38589 | -0.0836383 | -8 | 11 |
| all_observed | clean_v1 | current_total_reg_courses = previous_total_reg + previous_semester_reg | 70781 | 3441 | 4.86147 | 0.0576426 | -21 | 32 |
| all_observed | clean_v1 | current_total_pass_courses = previous_total_pass + previous_semester_pass | 70781 | 1461 | 2.06411 | -0.0206411 | -21 | 11 |
| all_observed | clean_v1 | current_total_fail_courses = previous_total_fail + previous_semester_fail | 70781 | 833 | 1.17687 | 0.00394174 | -1 | 11 |
| all_observed | clean_v1 | current_total_reg_courses = previous_total_reg + CURRENT_semester_reg_control | 70781 | 57757 | 81.5996 | 0.348851 | -22 | 33 |
| calendar_adjacent_1_2_3 | clean_v1 | current_start_total_in_credits = previous_end_total_in | 64026 | 4029 | 6.29276 | -0.242214 | -24.5 | 16 |
| calendar_adjacent_1_2_3 | clean_v1 | current_total_reg_credits = previous_total_reg + previous_semester_reg | 64026 | 1 | 0.00156187 | -0.00112454 | -72 | 0 |
| calendar_adjacent_1_2_3 | clean_v1 | current_total_pass_credits = previous_total_pass + previous_semester_pass | 64026 | 1 | 0.00156187 | -0.00112454 | -72 | 0 |
| calendar_adjacent_1_2_3 | clean_v1 | current_total_fail_credits = previous_total_fail + previous_semester_fail | 64026 | 2 | 0.00312373 | -9.37119e-05 | -3 | 0 |
| calendar_adjacent_1_2_3 | clean_v1 | current_total_reg_credits = previous_total_reg + CURRENT_semester_reg_control | 64026 | 57306 | 89.5043 | 0.781378 | -57 | 46 |
| calendar_adjacent_1_2_3 | clean_v1 | current_start_total_in_courses = previous_end_total_in | 64026 | 4028 | 6.29119 | -0.0818886 | -8 | 7 |
| calendar_adjacent_1_2_3 | clean_v1 | current_total_reg_courses = previous_total_reg + previous_semester_reg | 64026 | 1698 | 2.65205 | -0.0268641 | -21 | 0 |
| calendar_adjacent_1_2_3 | clean_v1 | current_total_pass_courses = previous_total_pass + previous_semester_pass | 64026 | 1258 | 1.96483 | -0.0199919 | -21 | 0 |
| calendar_adjacent_1_2_3 | clean_v1 | current_total_fail_courses = previous_total_fail + previous_semester_fail | 64026 | 397 | 0.620061 | -0.00620061 | -1 | 0 |
| calendar_adjacent_1_2_3 | clean_v1 | current_total_reg_courses = previous_total_reg + CURRENT_semester_reg_control | 64026 | 53118 | 82.9632 | 0.253944 | -22 | 11 |
| all_observed | clean_v2 | current_start_total_in_credits = previous_end_total_in | 76347 | 4547 | 5.9557 | -0.230801 | -24.5 | 32 |
| all_observed | clean_v2 | current_total_reg_credits = previous_total_reg + previous_semester_reg | 76347 | 4 | 0.00523924 | -0.000157177 | -72 | 32 |
| all_observed | clean_v2 | current_total_pass_credits = previous_total_pass + previous_semester_pass | 76347 | 4 | 0.00523924 | -0.000235766 | -72 | 32 |
| all_observed | clean_v2 | current_total_fail_credits = previous_total_fail + previous_semester_fail | 76347 | 3 | 0.00392943 | -3.92943e-05 | -3 | 3 |
| all_observed | clean_v2 | current_total_reg_credits = previous_total_reg + CURRENT_semester_reg_control | 76347 | 67030 | 87.7965 | 0.831211 | -57 | 46 |
| all_observed | clean_v2 | current_start_total_in_courses = previous_end_total_in | 76347 | 4545 | 5.95308 | -0.0778944 | -8 | 11 |
| all_observed | clean_v2 | current_total_reg_courses = previous_total_reg + previous_semester_reg | 76347 | 2006 | 2.62748 | -0.0262486 | -21 | 11 |
| all_observed | clean_v2 | current_total_pass_courses = previous_total_pass + previous_semester_pass | 76347 | 1471 | 1.92673 | -0.0192673 | -21 | 11 |
| all_observed | clean_v2 | current_total_fail_courses = previous_total_fail + previous_semester_fail | 76347 | 464 | 0.607751 | -0.00605132 | -1 | 1 |
| all_observed | clean_v2 | current_total_reg_courses = previous_total_reg + CURRENT_semester_reg_control | 76347 | 61828 | 80.9829 | 0.315716 | -22 | 14 |
| calendar_adjacent_1_2_3 | clean_v2 | current_start_total_in_credits = previous_end_total_in | 70054 | 4158 | 5.93542 | -0.228645 | -24.5 | 16 |
| calendar_adjacent_1_2_3 | clean_v2 | current_total_reg_credits = previous_total_reg + previous_semester_reg | 70054 | 1 | 0.00142747 | -0.00102778 | -72 | 0 |
| calendar_adjacent_1_2_3 | clean_v2 | current_total_pass_credits = previous_total_pass + previous_semester_pass | 70054 | 1 | 0.00142747 | -0.00102778 | -72 | 0 |
| calendar_adjacent_1_2_3 | clean_v2 | current_total_fail_credits = previous_total_fail + previous_semester_fail | 70054 | 2 | 0.00285494 | -8.56482e-05 | -3 | 0 |
| calendar_adjacent_1_2_3 | clean_v2 | current_total_reg_credits = previous_total_reg + CURRENT_semester_reg_control | 70054 | 62302 | 88.9343 | 0.88117 | -57 | 46 |
| calendar_adjacent_1_2_3 | clean_v2 | current_start_total_in_courses = previous_end_total_in | 70054 | 4157 | 5.93399 | -0.0773689 | -8 | 7 |
| calendar_adjacent_1_2_3 | clean_v2 | current_total_reg_courses = previous_total_reg + previous_semester_reg | 70054 | 1753 | 2.50236 | -0.0253376 | -21 | 0 |
| calendar_adjacent_1_2_3 | clean_v2 | current_total_pass_courses = previous_total_pass + previous_semester_pass | 70054 | 1282 | 1.83002 | -0.0186142 | -21 | 0 |
| calendar_adjacent_1_2_3 | clean_v2 | current_total_fail_courses = previous_total_fail + previous_semester_fail | 70054 | 413 | 0.589545 | -0.00589545 | -1 | 0 |
| calendar_adjacent_1_2_3 | clean_v2 | current_total_reg_courses = previous_total_reg + CURRENT_semester_reg_control | 70054 | 57948 | 82.719 | 0.304808 | -22 | 11 |

## V1 / V2 parity

Outer join counts in the 2020–2024 window: `{"both": 82300, "right_only": 5592, "left_only": 0}`.

| field | common_rows | mismatch | both_missing | v1_missing_only | v2_missing_only |
| --- | --- | --- | --- | --- | --- |
| start_total_in_courses | 82300 | 0 | 0 | 0 | 0 |
| start_total_in_credits | 82300 | 0 | 0 | 0 | 0 |
| end_total_in_courses | 82300 | 0 | 0 | 0 | 0 |
| end_total_in_credits | 82300 | 0 | 0 | 0 | 0 |
| semester_reg_courses | 82300 | 0 | 0 | 0 | 0 |
| semester_reg_credits | 82300 | 0 | 0 | 0 | 0 |
| semester_pass_courses | 82300 | 0 | 0 | 0 | 0 |
| semester_pass_credits | 82300 | 0 | 0 | 0 | 0 |
| semester_fail_courses | 82300 | 0 | 0 | 0 | 0 |
| semester_fail_credits | 82300 | 0 | 0 | 0 | 0 |
| total_semesters | 82300 | 0 | 0 | 0 | 0 |
| total_reg_courses | 82300 | 0 | 0 | 0 | 0 |
| total_reg_credits | 82300 | 0 | 0 | 0 | 0 |
| total_pass_courses | 82300 | 0 | 0 | 0 | 0 |
| total_pass_credits | 82300 | 0 | 0 | 0 | 0 |
| total_fail_courses | 82300 | 0 | 0 | 0 | 0 |
| total_fail_credits | 82300 | 0 | 0 | 0 | 0 |
| reg_total_semesters | 82300 | 0 | 0 | 0 | 0 |

## Representative real-source examples

These examples retain degree, part and measured progress numbers. Student keys are reproducible SHA256 pseudonyms. Previous/current differences demonstrate observed variation; they do not establish database business semantics.

| reason | student_sha256 | degree_id | part_id | previous_part_id | start_total_in_credits | total_reg_credits | previous_end_total_in_credits | previous_total_reg_credits | previous_semester_reg_credits |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lag_start_end_mismatch | a3f9bb3723104dcfa2022db4158aa0477083d86b49293240c8669bacc9ecb597 | 2.111 | 20223 | 20222 | 222 | 413.5 | 225 | 394.5 | 19 |
| lag_reg_increment_mismatch | 2159b3f40503d6e8e3f118aca3ccbc33a2973aefdb1856cd94f0f10d5f12e74d | 8.111 | 20212 | 20202 | 72 | 93 | 73 | 62 | 18 |
| start_vs_reg_difference | a3f9bb3723104dcfa2022db4158aa0477083d86b49293240c8669bacc9ecb597 | 2.111 | 20202 | 20201 | 156.5 | 294 | 156.5 | 270.5 | 23.5 |

## Evidence files

All tables are saved as CSV under `evidence/`. `schemas.json` records actual Parquet types; `input_manifest.json` records source SHA256 and row counts. `alias_equality.csv` verifies the training aliases. Stratified distribution, correlation, equality/difference and deterministic mapping tables are saved separately for year, degree and progress quartile. `anonymized_examples.csv` uses SHA256 of the source student ID; no original student or status IDs are emitted. This stable pseudonym is not proof of irreversible anonymization. `raw_clean_value_preservation.csv` checks whether cleaning changes the four fields for matched status IDs.
