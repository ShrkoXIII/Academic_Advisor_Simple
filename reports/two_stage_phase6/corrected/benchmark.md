# Phase 6 — Synthetic two-stage benchmark

**CORRECTED RESULT:** all 168 non-search observations below are fresh replacements (128 completed, 40 censored). The 25 `search` rows are **RETAINED / UNAFFECTED SEARCH** with their original metric values and provenance; they are not new measurements. See `benchmark.json.evidence_validity` and each row's `evidence_status`. No old inference metric is reused.

**OLD / INVALIDATED RESULT:** original reports are archived separately under `old_invalidated/`; their inference, ranking, runtime and memory observations are stale. Benchmark conversion uses supported GradeVersion 1.111, which the models encode as an unknown category. Independent quality evidence uses known-category 2.111 and separate 3.111 sensitivity. See [RESULT.md](<D:/AI/Real projects/Academic_Advisor_Simple/reports/two_stage_phase6/corrected/RESULT.md>) for the independent recommendations and limitations. This validity annotation changes no measured values.

Synthetic payloads and empty synthetic in-memory history; pinned real 33/47 models.

Ranking approvals: Stage 1 / Final / combination = **UNAPPROVED**.

Environment: `{'platform': 'Windows-10-10.0.26300-SP0', 'python': '3.11.5', 'threads': 1, 'pandas': '3.0.5', 'processor': 'Intel64 Family 6 Model 154 Stepping 4, GenuineIntel', 'measurement_repetitions': 1}`. Sequential fresh workers; one sample per job.

Primary worker deadline: 15s including setup; a timeout is censored, not a measured latency. Supplemental budgets, when used, are pinned per measurement batch in JSON.

Times are warm operation seconds. Peak memory is MiB, including worker setup; it is an actual process peak, not Python-only allocations.

| N | Scenario | Measurement | Stage1 / Final | Status | States | Feasible | Shortlist | Seconds | Peak MiB |
|---|---|---|---|---|---:|---:|---:|---:|---:|
| 15 | easy | search | None / None | completed | 1279 | 1 | 1 | 0.0118 | 86.1719 |
| 15 | easy | stage1_ranking | balance_first / None | completed | 1279 | 1 | 1 | 0.0026 | 179.7109 |
| 15 | easy | stage1_ranking | pareto / None | completed | 1279 | 1 | 1 | 0.0027 | 178.4766 |
| 15 | easy | final_ranking | None / balance_first | completed | 1279 | 1 | 1 | 0.0034 | 178.7852 |
| 15 | easy | final_ranking | None / pareto | completed | 1279 | 1 | 1 | 0.0037 | 179.3828 |
| 15 | easy | full | balance_first / balance_first | completed | 1279 | 1 | 1 | 0.3236 | 179.3945 |
| 15 | easy | full | balance_first / pareto | completed | 1279 | 1 | 1 | 0.2373 | 178.5508 |
| 15 | easy | full | pareto / balance_first | completed | 1279 | 1 | 1 | 0.2600 | 179.3906 |
| 15 | easy | full | pareto / pareto | completed | 1279 | 1 | 1 | 0.3451 | 179.2656 |
| 15 | fractional_zero_constraints | search | None / None | completed | 5391 | 76 | 50 | 0.0324 | 85.8047 |
| 15 | fractional_zero_constraints | stage1_ranking | balance_first / None | completed | 5391 | 76 | 50 | 0.3010 | 179.7031 |
| 15 | fractional_zero_constraints | stage1_ranking | pareto / None | completed | 5391 | 76 | 50 | 0.2388 | 179.3633 |
| 15 | fractional_zero_constraints | final_ranking | None / balance_first | completed | 5391 | 76 | 50 | 0.1131 | 179.1836 |
| 15 | fractional_zero_constraints | final_ranking | None / pareto | completed | 5391 | 76 | 50 | 0.1928 | 178.8867 |
| 15 | fractional_zero_constraints | full | balance_first / balance_first | completed | 5391 | 76 | 50 | 2.1623 | 178.9727 |
| 15 | fractional_zero_constraints | full | balance_first / pareto | completed | 5391 | 76 | 50 | 1.6093 | 178.8672 |
| 15 | fractional_zero_constraints | full | pareto / balance_first | completed | 5391 | 76 | 50 | 1.9004 | 179.6211 |
| 15 | fractional_zero_constraints | full | pareto / pareto | completed | 5391 | 76 | 50 | 1.6394 | 178.8281 |
| 15 | dense_ties | search | None / None | completed | 9645 | 1365 | 50 | 0.0545 | 85.7305 |
| 15 | dense_ties | stage1_ranking | balance_first / balance_first | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 15 | dense_ties | stage1_ranking | pareto / balance_first | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 15 | dense_ties | final_ranking | balance_first / balance_first | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 15 | dense_ties | final_ranking | balance_first / pareto | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 15 | dense_ties | full | balance_first / balance_first | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 15 | dense_ties | full | balance_first / pareto | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 15 | dense_ties | full | pareto / balance_first | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 15 | dense_ties | full | pareto / pareto | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 15 | no_solution | search | None / None | completed | 3639 | 0 | 0 | 0.0162 | 85.5664 |
| 15 | no_solution | stage1_ranking | balance_first / None | completed | 3639 | 0 | 0 | 0.0000 | 178.9258 |
| 15 | no_solution | stage1_ranking | pareto / None | completed | 3639 | 0 | 0 | 0.0000 | 179.4102 |
| 15 | no_solution | final_ranking | None / balance_first | completed | 3639 | 0 | 0 | 0.0000 | 179.3477 |
| 15 | no_solution | final_ranking | None / pareto | completed | 3639 | 0 | 0 | 0.0000 | 179.3633 |
| 15 | no_solution | full | balance_first / balance_first | completed | 3639 | 0 | 0 | 0.3246 | 179.2031 |
| 15 | no_solution | full | balance_first / pareto | completed | 3639 | 0 | 0 | 0.2354 | 178.9766 |
| 15 | no_solution | full | pareto / balance_first | completed | 3639 | 0 | 0 | 0.2062 | 178.9023 |
| 15 | no_solution | full | pareto / pareto | completed | 3639 | 0 | 0 | 0.2646 | 178.8164 |
| 20 | easy | search | None / None | completed | 1919 | 1 | 1 | 0.0215 | 85.5039 |
| 20 | easy | stage1_ranking | balance_first / None | completed | 1919 | 1 | 1 | 0.0041 | 179.3398 |
| 20 | easy | stage1_ranking | pareto / None | completed | 1919 | 1 | 1 | 0.0080 | 179.2578 |
| 20 | easy | final_ranking | None / balance_first | completed | 1919 | 1 | 1 | 0.0065 | 179.7344 |
| 20 | easy | final_ranking | None / pareto | completed | 1919 | 1 | 1 | 0.0081 | 179.4258 |
| 20 | easy | full | balance_first / balance_first | completed | 1919 | 1 | 1 | 0.4748 | 179.0508 |
| 20 | easy | full | balance_first / pareto | completed | 1919 | 1 | 1 | 0.8677 | 178.9102 |
| 20 | easy | full | pareto / balance_first | completed | 1919 | 1 | 1 | 0.3409 | 178.8906 |
| 20 | easy | full | pareto / pareto | completed | 1919 | 1 | 1 | 0.3706 | 179.1523 |
| 20 | fractional_zero_constraints | search | None / None | completed | 13451 | 190 | 50 | 0.0347 | 85.7695 |
| 20 | fractional_zero_constraints | stage1_ranking | balance_first / None | completed | 13451 | 190 | 50 | 0.3099 | 179.1719 |
| 20 | fractional_zero_constraints | stage1_ranking | pareto / None | completed | 13451 | 190 | 50 | 0.3535 | 179.4648 |
| 20 | fractional_zero_constraints | final_ranking | None / balance_first | completed | 13451 | 190 | 50 | 0.1067 | 179.1797 |
| 20 | fractional_zero_constraints | final_ranking | None / pareto | completed | 13451 | 190 | 50 | 0.0966 | 179.6055 |
| 20 | fractional_zero_constraints | full | balance_first / balance_first | completed | 13451 | 190 | 50 | 1.9901 | 179.0742 |
| 20 | fractional_zero_constraints | full | balance_first / pareto | completed | 13451 | 190 | 50 | 3.3232 | 179.8711 |
| 20 | fractional_zero_constraints | full | pareto / balance_first | completed | 13451 | 190 | 50 | 3.7004 | 179.2578 |
| 20 | fractional_zero_constraints | full | pareto / pareto | completed | 13451 | 190 | 50 | 3.3593 | 178.6094 |
| 20 | dense_ties | search | None / None | completed | 42977 | 4845 | 50 | 0.1675 | 85.7344 |
| 20 | dense_ties | stage1_ranking | balance_first / balance_first | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 20 | dense_ties | stage1_ranking | pareto / balance_first | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 20 | dense_ties | final_ranking | balance_first / balance_first | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 20 | dense_ties | final_ranking | balance_first / pareto | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 20 | dense_ties | full | balance_first / balance_first | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 20 | dense_ties | full | balance_first / pareto | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 20 | dense_ties | full | pareto / balance_first | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 20 | dense_ties | full | pareto / pareto | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 20 | no_solution | search | None / None | completed | 11969 | 0 | 0 | 0.0252 | 86.0547 |
| 20 | no_solution | stage1_ranking | balance_first / None | completed | 11969 | 0 | 0 | 0.0000 | 179.7344 |
| 20 | no_solution | stage1_ranking | pareto / None | completed | 11969 | 0 | 0 | 0.0000 | 179.1719 |
| 20 | no_solution | final_ranking | None / balance_first | completed | 11969 | 0 | 0 | 0.0000 | 179.9023 |
| 20 | no_solution | final_ranking | None / pareto | completed | 11969 | 0 | 0 | 0.0000 | 179.6016 |
| 20 | no_solution | full | balance_first / balance_first | completed | 11969 | 0 | 0 | 0.2991 | 178.6406 |
| 20 | no_solution | full | balance_first / pareto | completed | 11969 | 0 | 0 | 0.2665 | 179.0391 |
| 20 | no_solution | full | pareto / balance_first | completed | 11969 | 0 | 0 | 0.2590 | 179.1133 |
| 20 | no_solution | full | pareto / pareto | completed | 11969 | 0 | 0 | 0.2882 | 179.0078 |
| 25 | easy | search | None / None | completed | 2559 | 1 | 1 | 0.0261 | 85.8008 |
| 25 | easy | stage1_ranking | balance_first / None | completed | 2559 | 1 | 1 | 0.0063 | 179.5312 |
| 25 | easy | stage1_ranking | pareto / None | completed | 2559 | 1 | 1 | 0.0066 | 178.4375 |
| 25 | easy | final_ranking | None / balance_first | completed | 2559 | 1 | 1 | 0.0055 | 178.7852 |
| 25 | easy | final_ranking | None / pareto | completed | 2559 | 1 | 1 | 0.0144 | 178.9492 |
| 25 | easy | full | balance_first / balance_first | completed | 2559 | 1 | 1 | 0.4511 | 178.5664 |
| 25 | easy | full | balance_first / pareto | completed | 2559 | 1 | 1 | 0.4858 | 179.2734 |
| 25 | easy | full | pareto / balance_first | completed | 2559 | 1 | 1 | 1.1479 | 179.0859 |
| 25 | easy | full | pareto / pareto | completed | 2559 | 1 | 1 | 0.3827 | 178.1250 |
| 25 | fractional_zero_constraints | search | None / None | completed | 27615 | 290 | 50 | 0.0394 | 85.7656 |
| 25 | fractional_zero_constraints | stage1_ranking | balance_first / None | completed | 27615 | 290 | 50 | 0.7783 | 178.7070 |
| 25 | fractional_zero_constraints | stage1_ranking | pareto / None | completed | 27615 | 290 | 50 | 1.0654 | 179.2656 |
| 25 | fractional_zero_constraints | final_ranking | None / balance_first | completed | 27615 | 290 | 50 | 0.0891 | 178.8750 |
| 25 | fractional_zero_constraints | final_ranking | None / pareto | completed | 27615 | 290 | 50 | 0.0692 | 179.1484 |
| 25 | fractional_zero_constraints | full | balance_first / balance_first | completed | 27615 | 290 | 50 | 4.1457 | 178.3164 |
| 25 | fractional_zero_constraints | full | balance_first / pareto | completed | 27615 | 290 | 50 | 3.9576 | 179.0078 |
| 25 | fractional_zero_constraints | full | pareto / balance_first | completed | 27615 | 290 | 50 | 3.8342 | 179.0156 |
| 25 | fractional_zero_constraints | full | pareto / pareto | completed | 27615 | 290 | 50 | 3.7571 | 179.1484 |
| 25 | dense_ties | search | None / None | completed | 136159 | 12650 | 50 | 0.2642 | 85.6406 |
| 25 | dense_ties | stage1_ranking | balance_first / balance_first | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 25 | dense_ties | stage1_ranking | pareto / balance_first | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 25 | dense_ties | final_ranking | balance_first / balance_first | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 25 | dense_ties | final_ranking | balance_first / pareto | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 25 | dense_ties | full | balance_first / balance_first | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 25 | dense_ties | full | balance_first / pareto | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 25 | dense_ties | full | pareto / balance_first | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 25 | dense_ties | full | pareto / pareto | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 25 | no_solution | search | None / None | completed | 29899 | 0 | 0 | 0.0263 | 85.5234 |
| 25 | no_solution | stage1_ranking | balance_first / None | completed | 29899 | 0 | 0 | 0.0000 | 179.3906 |
| 25 | no_solution | stage1_ranking | pareto / None | completed | 29899 | 0 | 0 | 0.0000 | 179.5312 |
| 25 | no_solution | final_ranking | None / balance_first | completed | 29899 | 0 | 0 | 0.0000 | 178.9688 |
| 25 | no_solution | final_ranking | None / pareto | completed | 29899 | 0 | 0 | 0.0000 | 179.3359 |
| 25 | no_solution | full | balance_first / balance_first | completed | 29899 | 0 | 0 | 0.3650 | 179.2578 |
| 25 | no_solution | full | balance_first / pareto | completed | 29899 | 0 | 0 | 0.3218 | 179.2031 |
| 25 | no_solution | full | pareto / balance_first | completed | 29899 | 0 | 0 | 0.2152 | 179.2773 |
| 25 | no_solution | full | pareto / pareto | completed | 29899 | 0 | 0 | 0.3674 | 178.8398 |
| 30 | easy | search | None / None | completed | 3199 | 1 | 1 | 0.0276 | 85.7031 |
| 30 | easy | stage1_ranking | balance_first / None | completed | 3199 | 1 | 1 | 0.0092 | 179.4922 |
| 30 | easy | stage1_ranking | pareto / None | completed | 3199 | 1 | 1 | 0.0089 | 179.4922 |
| 30 | easy | final_ranking | None / balance_first | completed | 3199 | 1 | 1 | 0.0068 | 179.2227 |
| 30 | easy | final_ranking | None / pareto | completed | 3199 | 1 | 1 | 0.0054 | 178.0938 |
| 30 | easy | full | balance_first / balance_first | completed | 3199 | 1 | 1 | 0.5816 | 179.1680 |
| 30 | easy | full | balance_first / pareto | completed | 3199 | 1 | 1 | 0.4283 | 179.3750 |
| 30 | easy | full | pareto / balance_first | completed | 3199 | 1 | 1 | 0.4255 | 178.9219 |
| 30 | easy | full | pareto / pareto | completed | 3199 | 1 | 1 | 0.4854 | 179.2070 |
| 30 | fractional_zero_constraints | search | None / None | completed | 48231 | 508 | 50 | 0.0668 | 86.0430 |
| 30 | fractional_zero_constraints | stage1_ranking | balance_first / None | completed | 48231 | 508 | 50 | 0.7837 | 179.4180 |
| 30 | fractional_zero_constraints | stage1_ranking | pareto / None | completed | 48231 | 508 | 50 | 1.1429 | 178.7773 |
| 30 | fractional_zero_constraints | final_ranking | None / balance_first | completed | 48231 | 508 | 50 | 0.0849 | 178.9766 |
| 30 | fractional_zero_constraints | final_ranking | None / pareto | completed | 48231 | 508 | 50 | 0.1343 | 178.5273 |
| 30 | fractional_zero_constraints | full | balance_first / balance_first | completed | 48231 | 508 | 50 | 5.4883 | 178.9805 |
| 30 | fractional_zero_constraints | full | balance_first / pareto | completed | 48231 | 508 | 50 | 7.4202 | 179.4258 |
| 30 | fractional_zero_constraints | full | pareto / balance_first | completed | 48231 | 508 | 50 | 4.4613 | 179.2266 |
| 30 | fractional_zero_constraints | full | pareto / pareto | completed | 48231 | 508 | 50 | 5.8846 | 179.3945 |
| 30 | dense_ties | search | None / None | completed | 347941 | 27405 | 50 | 0.5588 | 85.6211 |
| 30 | dense_ties | stage1_ranking | balance_first / balance_first | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 30 | dense_ties | stage1_ranking | pareto / balance_first | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 30 | dense_ties | final_ranking | balance_first / balance_first | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 30 | dense_ties | final_ranking | balance_first / pareto | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 30 | dense_ties | full | balance_first / balance_first | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 30 | dense_ties | full | balance_first / pareto | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 30 | dense_ties | full | pareto / balance_first | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 30 | dense_ties | full | pareto / pareto | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 30 | no_solution | search | None / None | completed | 62929 | 0 | 0 | 0.0333 | 85.8555 |
| 30 | no_solution | stage1_ranking | balance_first / None | completed | 62929 | 0 | 0 | 0.0000 | 179.0312 |
| 30 | no_solution | stage1_ranking | pareto / None | completed | 62929 | 0 | 0 | 0.0000 | 179.1523 |
| 30 | no_solution | final_ranking | None / balance_first | completed | 62929 | 0 | 0 | 0.0000 | 179.1680 |
| 30 | no_solution | final_ranking | None / pareto | completed | 62929 | 0 | 0 | 0.0000 | 178.9805 |
| 30 | no_solution | full | balance_first / balance_first | completed | 62929 | 0 | 0 | 0.2808 | 179.4531 |
| 30 | no_solution | full | balance_first / pareto | completed | 62929 | 0 | 0 | 0.3855 | 179.4805 |
| 30 | no_solution | full | pareto / balance_first | completed | 62929 | 0 | 0 | 0.3317 | 179.5508 |
| 30 | no_solution | full | pareto / pareto | completed | 62929 | 0 | 0 | 0.4520 | 179.6094 |
| 35 stress | easy | search | None / None | completed | 3839 | 1 | 1 | 0.0309 | 85.8359 |
| 35 stress | easy | stage1_ranking | balance_first / None | completed | 3839 | 1 | 1 | 0.0074 | 179.1875 |
| 35 stress | easy | stage1_ranking | pareto / None | completed | 3839 | 1 | 1 | 0.0054 | 179.2422 |
| 35 stress | easy | final_ranking | None / balance_first | completed | 3839 | 1 | 1 | 0.0049 | 178.6758 |
| 35 stress | easy | final_ranking | None / pareto | completed | 3839 | 1 | 1 | 0.0042 | 178.9453 |
| 35 stress | easy | full | balance_first / balance_first | completed | 3839 | 1 | 1 | 0.4889 | 178.9844 |
| 35 stress | easy | full | balance_first / pareto | completed | 3839 | 1 | 1 | 0.3476 | 178.8906 |
| 35 stress | easy | full | pareto / balance_first | completed | 3839 | 1 | 1 | 0.3043 | 179.2383 |
| 35 stress | easy | full | pareto / pareto | completed | 3839 | 1 | 1 | 0.3131 | 179.1328 |
| 35 stress | fractional_zero_constraints | search | None / None | completed | 77011 | 730 | 50 | 0.0815 | 85.8672 |
| 35 stress | fractional_zero_constraints | stage1_ranking | balance_first / None | completed | 77011 | 730 | 50 | 1.2010 | 179.6758 |
| 35 stress | fractional_zero_constraints | stage1_ranking | pareto / None | completed | 77011 | 730 | 50 | 1.2455 | 179.9922 |
| 35 stress | fractional_zero_constraints | final_ranking | None / balance_first | completed | 77011 | 730 | 50 | 0.0545 | 179.5156 |
| 35 stress | fractional_zero_constraints | final_ranking | None / pareto | completed | 77011 | 730 | 50 | 0.1161 | 178.8086 |
| 35 stress | fractional_zero_constraints | full | balance_first / balance_first | completed | 77011 | 730 | 50 | 7.7676 | 179.0273 |
| 35 stress | fractional_zero_constraints | full | balance_first / pareto | completed | 77011 | 730 | 50 | 5.5650 | 178.6914 |
| 35 stress | fractional_zero_constraints | full | pareto / balance_first | completed | 77011 | 730 | 50 | 8.6894 | 181.1719 |
| 35 stress | fractional_zero_constraints | full | pareto / pareto | completed | 77011 | 730 | 50 | 9.4608 | 180.9609 |
| 35 stress | dense_ties | search | None / None | completed | 767073 | 52360 | 50 | 1.0778 | 86.0039 |
| 35 stress | dense_ties | stage1_ranking | balance_first / balance_first | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 35 stress | dense_ties | stage1_ranking | pareto / balance_first | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 35 stress | dense_ties | final_ranking | balance_first / balance_first | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 35 stress | dense_ties | final_ranking | balance_first / pareto | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 35 stress | dense_ties | full | balance_first / balance_first | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 35 stress | dense_ties | full | balance_first / pareto | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 35 stress | dense_ties | full | pareto / balance_first | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 35 stress | dense_ties | full | pareto / pareto | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 35 stress | no_solution | search | None / None | completed | 117809 | 0 | 0 | 0.0553 | 85.7070 |
| 35 stress | no_solution | stage1_ranking | balance_first / None | completed | 117809 | 0 | 0 | 0.0000 | 179.2773 |
| 35 stress | no_solution | stage1_ranking | pareto / None | completed | 117809 | 0 | 0 | 0.0000 | 179.3945 |
| 35 stress | no_solution | final_ranking | None / balance_first | completed | 117809 | 0 | 0 | 0.0000 | 178.7188 |
| 35 stress | no_solution | final_ranking | None / pareto | completed | 117809 | 0 | 0 | 0.0000 | 179.4141 |
| 35 stress | no_solution | full | balance_first / balance_first | completed | 117809 | 0 | 0 | 0.2434 | 179.0430 |
| 35 stress | no_solution | full | balance_first / pareto | completed | 117809 | 0 | 0 | 0.2749 | 179.1328 |
| 35 stress | no_solution | full | pareto / balance_first | completed | 117809 | 0 | 0 | 0.2424 | 179.2852 |
| 35 stress | no_solution | full | pareto / pareto | completed | 117809 | 0 | 0 | 0.3086 | 178.8164 |
| 15 | dense_ties | stage1_ranking | balance_first / None | completed | 9645 | 1365 | 50 | 1.8689 | 179.2734 |
| 15 | dense_ties | stage1_ranking | pareto / None | completed | 9645 | 1365 | 50 | 7.9867 | 179.1328 |
| 15 | dense_ties | final_ranking | None / balance_first | completed | 9645 | 1365 | 50 | 0.0589 | 178.9570 |
| 15 | dense_ties | final_ranking | None / pareto | completed | 9645 | 1365 | 50 | 0.0610 | 178.3867 |
| 15 | dense_ties | full | balance_first / balance_first | completed | 9645 | 1365 | 50 | 8.4379 | 179.2383 |
| 15 | dense_ties | full | balance_first / pareto | completed | 9645 | 1365 | 50 | 9.7441 | 179.2695 |
| 15 | dense_ties | full | pareto / balance_first | completed | 9645 | 1365 | 50 | 18.8793 | 181.7305 |
| 15 | dense_ties | full | pareto / pareto | completed | 9645 | 1365 | 50 | 18.3665 | 181.4023 |
| 15 | dense_upper_18 | search | None / None | completed | 28885 | 5005 | 50 | 0.1436 | 85.6367 |
| 20 | dense_upper_18 | search | None / None | completed | 263567 | 38760 | 50 | 1.2075 | 85.7227 |
| 25 | dense_upper_18 | search | None / None | completed | 1421859 | 177100 | 50 | 6.6769 | 85.5977 |
| 30 | dense_upper_18 | search | None / None | completed | 5544161 | 593775 | 50 | 25.5347 | 85.6602 |
| 35 stress | dense_upper_18 | search | None / None | completed | 17344623 | 1623160 | 50 | 68.6609 | 85.7305 |

Search-only shortlist counts are min(50, feasible), not a scored selection. Ranking rows count visits during untimed preparation.

Search decision: **PROPOSE SEPARATE search optimization study; current algorithm remains unchanged**

All search-only observations at sizes <=30; ranking, full, setup and stress costs are evaluated separately

Slow/censored full operations require a separate investigation of metrics construction, ranking and inference; they do not identify the search as the bottleneck

Diagnostic timing bands: <1s; 1–3s; 3–5s; >5s. No hard memory gate or production candidate cap.

Independent Stage 1 and Final comparisons and every cross-stage pair are recorded in benchmark.json; metrics keep each Balance component separate.

The Phase 5 fabricated-prediction snapshot is NOT USED for corrected quality conclusions. Real-model recall and Final tradeoffs are evaluated separately in the corrected Phase 6 evaluation report.

## Stage 1 tradeoffs

| N / scenario / choice | Academic overlap | GPA change | Failed credits change | Failed penalty change | Withdrawn penalty change | Total penalty change |
|---|---:|---:|---:|---:|---:|---:|
| 15 / easy / balance_first | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 15 / easy / pareto | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 15 / fractional_zero_constraints / balance_first | 44 | 0.0000 | 0.0025 | -0.0182 | 0.0000 | -0.0143 |
| 15 / fractional_zero_constraints / pareto | 44 | 0.0000 | 0.0025 | -0.0182 | 0.0000 | -0.0143 |
| 20 / easy / balance_first | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 20 / easy / pareto | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 20 / fractional_zero_constraints / balance_first | 30 | 0.0000 | 0.0172 | -0.0608 | 0.0000 | -0.0476 |
| 20 / fractional_zero_constraints / pareto | 40 | 0.0000 | 0.0052 | -0.0304 | 0.0000 | -0.0238 |
| 25 / easy / balance_first | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 25 / easy / pareto | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 25 / fractional_zero_constraints / balance_first | 20 | 0.0000 | 0.0253 | -0.0912 | 0.0000 | -0.0714 |
| 25 / fractional_zero_constraints / pareto | 32 | 0.0000 | 0.0080 | -0.0547 | 0.0000 | -0.0429 |
| 30 / easy / balance_first | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 30 / easy / pareto | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 30 / fractional_zero_constraints / balance_first | 6 | 0.0000 | 0.0520 | -0.1337 | 0.0000 | -0.1048 |
| 30 / fractional_zero_constraints / pareto | 34 | 0.0000 | 0.0082 | -0.0486 | 0.0000 | -0.0381 |
| 35 / easy / balance_first | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 35 / easy / pareto | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 35 / fractional_zero_constraints / balance_first | 0 | 0.0000 | 0.0637 | -0.1520 | 0.0000 | -0.1190 |
| 35 / fractional_zero_constraints / pareto | 32 | 0.0000 | 0.0090 | -0.0547 | 0.0000 | -0.0429 |
| 15 / dense_ties / balance_first | 0 | 0.0000 | 0.0028 | -0.1520 | 0.0000 | -0.1667 |
| 15 / dense_ties / pareto | 0 | 0.0000 | 0.0028 | -0.1520 | 0.0000 | -0.1667 |
## Final on fixed shortlist tradeoffs

| N / scenario / choice | Academic overlap | GPA change | Failed credits change | Failed penalty change | Withdrawn penalty change | Total penalty change |
|---|---:|---:|---:|---:|---:|---:|
| 15 / easy / balance_first | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 15 / easy / pareto | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 15 / fractional_zero_constraints / balance_first | 3 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 15 / fractional_zero_constraints / pareto | 2 | -0.0045 | -0.0138 | 0.0507 | 0.0000 | 0.0397 |
| 20 / easy / balance_first | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 20 / easy / pareto | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 20 / fractional_zero_constraints / balance_first | 3 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 20 / fractional_zero_constraints / pareto | 3 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 25 / easy / balance_first | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 25 / easy / pareto | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 25 / fractional_zero_constraints / balance_first | 3 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 25 / fractional_zero_constraints / pareto | 3 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 30 / easy / balance_first | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 30 / easy / pareto | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 30 / fractional_zero_constraints / balance_first | 3 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 30 / fractional_zero_constraints / pareto | 3 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 35 / easy / balance_first | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 35 / easy / pareto | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 35 / fractional_zero_constraints / balance_first | 3 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 35 / fractional_zero_constraints / pareto | 3 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 15 / dense_ties / balance_first | 3 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 15 / dense_ties / pareto | 3 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Cross-stage combinations — actual warm engine

| N / scenario | Stage 1 / Final | Status | Seconds | Top-3 GPA mean | Failed credits mean | Failed penalty | Withdrawn penalty | Total penalty |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 15 / easy | balance_first / balance_first | completed | 0.3236 | 2.1538 | 1.3171 | 0.0000 | 0.0000 | 0.0476 |
| 15 / easy | balance_first / pareto | completed | 0.2373 | 2.1538 | 1.3171 | 0.0000 | 0.0000 | 0.0476 |
| 15 / easy | pareto / balance_first | completed | 0.2600 | 2.1538 | 1.3171 | 0.0000 | 0.0000 | 0.0476 |
| 15 / easy | pareto / pareto | completed | 0.3451 | 2.1538 | 1.3171 | 0.0000 | 0.0000 | 0.0476 |
| 15 / fractional_zero_constraints | balance_first / balance_first | completed | 2.1623 | 2.1942 | 1.3747 | 0.0147 | 0.0000 | 0.0476 |
| 15 / fractional_zero_constraints | balance_first / pareto | completed | 1.6093 | 2.1897 | 1.3609 | 0.0654 | 0.0000 | 0.0873 |
| 15 / fractional_zero_constraints | pareto / balance_first | completed | 1.9004 | 2.1942 | 1.3747 | 0.0147 | 0.0000 | 0.0476 |
| 15 / fractional_zero_constraints | pareto / pareto | completed | 1.6394 | 2.1897 | 1.3609 | 0.0654 | 0.0000 | 0.0873 |
| 15 / dense_ties | balance_first / balance_first | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 15 / dense_ties | balance_first / pareto | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 15 / dense_ties | pareto / balance_first | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 15 / dense_ties | pareto / pareto | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 15 / no_solution | balance_first / balance_first | completed | 0.3246 | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 15 / no_solution | balance_first / pareto | completed | 0.2354 | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 15 / no_solution | pareto / balance_first | completed | 0.2062 | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 15 / no_solution | pareto / pareto | completed | 0.2646 | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 20 / easy | balance_first / balance_first | completed | 0.4748 | 2.1538 | 1.3171 | 0.0000 | 0.0000 | 0.0476 |
| 20 / easy | balance_first / pareto | completed | 0.8677 | 2.1538 | 1.3171 | 0.0000 | 0.0000 | 0.0476 |
| 20 / easy | pareto / balance_first | completed | 0.3409 | 2.1538 | 1.3171 | 0.0000 | 0.0000 | 0.0476 |
| 20 / easy | pareto / pareto | completed | 0.3706 | 2.1538 | 1.3171 | 0.0000 | 0.0000 | 0.0476 |
| 20 / fractional_zero_constraints | balance_first / balance_first | completed | 1.9901 | 2.1942 | 1.3715 | 0.0147 | 0.0000 | 0.0476 |
| 20 / fractional_zero_constraints | balance_first / pareto | completed | 3.3232 | 2.1942 | 1.3715 | 0.0147 | 0.0000 | 0.0476 |
| 20 / fractional_zero_constraints | pareto / balance_first | completed | 3.7004 | 2.1942 | 1.3715 | 0.0147 | 0.0000 | 0.0476 |
| 20 / fractional_zero_constraints | pareto / pareto | completed | 3.3593 | 2.1942 | 1.3715 | 0.0147 | 0.0000 | 0.0476 |
| 20 / dense_ties | balance_first / balance_first | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 20 / dense_ties | balance_first / pareto | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 20 / dense_ties | pareto / balance_first | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 20 / dense_ties | pareto / pareto | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 20 / no_solution | balance_first / balance_first | completed | 0.2991 | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 20 / no_solution | balance_first / pareto | completed | 0.2665 | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 20 / no_solution | pareto / balance_first | completed | 0.2590 | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 20 / no_solution | pareto / pareto | completed | 0.2882 | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 25 / easy | balance_first / balance_first | completed | 0.4511 | 2.1538 | 1.3171 | 0.0000 | 0.0000 | 0.0476 |
| 25 / easy | balance_first / pareto | completed | 0.4858 | 2.1538 | 1.3171 | 0.0000 | 0.0000 | 0.0476 |
| 25 / easy | pareto / balance_first | completed | 1.1479 | 2.1538 | 1.3171 | 0.0000 | 0.0000 | 0.0476 |
| 25 / easy | pareto / pareto | completed | 0.3827 | 2.1538 | 1.3171 | 0.0000 | 0.0000 | 0.0476 |
| 25 / fractional_zero_constraints | balance_first / balance_first | completed | 4.1457 | 2.1942 | 1.3715 | 0.0147 | 0.0000 | 0.0476 |
| 25 / fractional_zero_constraints | balance_first / pareto | completed | 3.9576 | 2.1942 | 1.3715 | 0.0147 | 0.0000 | 0.0476 |
| 25 / fractional_zero_constraints | pareto / balance_first | completed | 3.8342 | 2.1942 | 1.3715 | 0.0147 | 0.0000 | 0.0476 |
| 25 / fractional_zero_constraints | pareto / pareto | completed | 3.7571 | 2.1942 | 1.3715 | 0.0147 | 0.0000 | 0.0476 |
| 25 / dense_ties | balance_first / balance_first | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 25 / dense_ties | balance_first / pareto | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 25 / dense_ties | pareto / balance_first | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 25 / dense_ties | pareto / pareto | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 25 / no_solution | balance_first / balance_first | completed | 0.3650 | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 25 / no_solution | balance_first / pareto | completed | 0.3218 | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 25 / no_solution | pareto / balance_first | completed | 0.2152 | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 25 / no_solution | pareto / pareto | completed | 0.3674 | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 30 / easy | balance_first / balance_first | completed | 0.5816 | 2.1538 | 1.3171 | 0.0000 | 0.0000 | 0.0476 |
| 30 / easy | balance_first / pareto | completed | 0.4283 | 2.1538 | 1.3171 | 0.0000 | 0.0000 | 0.0476 |
| 30 / easy | pareto / balance_first | completed | 0.4255 | 2.1538 | 1.3171 | 0.0000 | 0.0000 | 0.0476 |
| 30 / easy | pareto / pareto | completed | 0.4854 | 2.1538 | 1.3171 | 0.0000 | 0.0000 | 0.0476 |
| 30 / fractional_zero_constraints | balance_first / balance_first | completed | 5.4883 | 2.1942 | 1.3715 | 0.0147 | 0.0000 | 0.0476 |
| 30 / fractional_zero_constraints | balance_first / pareto | completed | 7.4202 | 2.1942 | 1.3715 | 0.0147 | 0.0000 | 0.0476 |
| 30 / fractional_zero_constraints | pareto / balance_first | completed | 4.4613 | 2.1942 | 1.3715 | 0.0147 | 0.0000 | 0.0476 |
| 30 / fractional_zero_constraints | pareto / pareto | completed | 5.8846 | 2.1942 | 1.3715 | 0.0147 | 0.0000 | 0.0476 |
| 30 / dense_ties | balance_first / balance_first | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 30 / dense_ties | balance_first / pareto | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 30 / dense_ties | pareto / balance_first | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 30 / dense_ties | pareto / pareto | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 30 / no_solution | balance_first / balance_first | completed | 0.2808 | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 30 / no_solution | balance_first / pareto | completed | 0.3855 | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 30 / no_solution | pareto / balance_first | completed | 0.3317 | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 30 / no_solution | pareto / pareto | completed | 0.4520 | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 35 / easy | balance_first / balance_first | completed | 0.4889 | 2.1538 | 1.3171 | 0.0000 | 0.0000 | 0.0476 |
| 35 / easy | balance_first / pareto | completed | 0.3476 | 2.1538 | 1.3171 | 0.0000 | 0.0000 | 0.0476 |
| 35 / easy | pareto / balance_first | completed | 0.3043 | 2.1538 | 1.3171 | 0.0000 | 0.0000 | 0.0476 |
| 35 / easy | pareto / pareto | completed | 0.3131 | 2.1538 | 1.3171 | 0.0000 | 0.0000 | 0.0476 |
| 35 / fractional_zero_constraints | balance_first / balance_first | completed | 7.7676 | 2.1942 | 1.3715 | 0.0147 | 0.0000 | 0.0476 |
| 35 / fractional_zero_constraints | balance_first / pareto | completed | 5.5650 | 2.1942 | 1.3715 | 0.0147 | 0.0000 | 0.0476 |
| 35 / fractional_zero_constraints | pareto / balance_first | completed | 8.6894 | 2.1942 | 1.3715 | 0.0147 | 0.0000 | 0.0476 |
| 35 / fractional_zero_constraints | pareto / pareto | completed | 9.4608 | 2.1942 | 1.3715 | 0.0147 | 0.0000 | 0.0476 |
| 35 / dense_ties | balance_first / balance_first | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 35 / dense_ties | balance_first / pareto | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 35 / dense_ties | pareto / balance_first | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 35 / dense_ties | pareto / pareto | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 35 / no_solution | balance_first / balance_first | completed | 0.2434 | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 35 / no_solution | balance_first / pareto | completed | 0.2749 | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 35 / no_solution | pareto / balance_first | completed | 0.2424 | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 35 / no_solution | pareto / pareto | completed | 0.3086 | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 15 / dense_ties | balance_first / balance_first | completed | 8.4379 | 2.2500 | 0.9141 | 0.0147 | 0.0000 | 0.0000 |
| 15 / dense_ties | balance_first / pareto | completed | 9.7441 | 2.2500 | 0.9141 | 0.0147 | 0.0000 | 0.0000 |
| 15 / dense_ties | pareto / balance_first | completed | 18.8793 | 2.2500 | 0.9141 | 0.0147 | 0.0000 | 0.0000 |
| 15 / dense_ties | pareto / pareto | completed | 18.3665 | 2.2500 | 0.9141 | 0.0147 | 0.0000 | 0.0000 |

## Limits and decisions still required

- One measurement per fresh process; no production SLA, tail latency or throughput claim.
- Peak includes setup/native allocations; ranking preparation peak is not ranker-only incremental memory.
- Search/full timing includes optional counter overhead; ranking timing excludes search and metrics preparation.
- Timeouts censor complete counts, latency and memory; worker lower bounds are not request latency lower bounds.
- Dense ties use identical new-course model features; repeat candidates retain their official attempt feature.
- Synthetic history exercises fallback and does not measure the size/cost of real history.
- Inference fixtures use a version present in loaded GradeScale pass bands; unsupported integer-ID observations must not be used as quality evidence.
- Final comparisons use the same fixed academic Stage 1 shortlist; full pairs use their actual chosen shortlist.
- Zero seconds for an empty ranking workload means no ranker invocation; it is not a timed inference/search measurement.
- No global Top K guarantee or empirical student outcome improvement; approvals require human review.

backend_max_candidate_count / recommendation_latency_sla / memory_budget_per_request = UNRESOLVED.

Review and approve Stage 1, Final, and their combination independently before Phase 7 manifest work. No choice was approved by this benchmark.
