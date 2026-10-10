# Phase 6 — Synthetic two-stage benchmark

**RECHECK STATUS: PARTIAL — quality comparisons need a corrected rerun.**

Restart recheck (2026-10-07): local command creation still failed with `helper_unknown_error: setup refresh had errors`, and the alternate local Node runtime exited unexpectedly. No new tests, corrected inference measurements, final protected-file hash check, or Graphify update could run after the restart. Phase 6 remains PARTIAL.

The recorded inference fixtures used grade_version_id=1, but the pinned real GradeScale pass bands use 1.111, 2.111 and 3.111. Predicted marks around 65 consequently converted to zero points. Do not use the recorded GPA/quality comparisons or inference/ranking timings to approve a strategy. Search-only observations do not use GradeScale and remain usable. The benchmark now chooses the smallest finite version present in the loaded pass bands, with regression tests added; this correction has not yet been verified because the local execution helper became unavailable. Full pytest ended without a recoverable final result. Corrected inference measurements, final verification, and Graphify update are pending.

Synthetic payloads and empty synthetic in-memory history; pinned real 33/47 models.

Ranking approvals: Stage 1 / Final / combination = **UNAPPROVED**.

Environment: `{'platform': 'Windows-10-10.0.26300-SP0', 'python': '3.11.5', 'threads': 1, 'pandas': '3.0.5', 'processor': 'Intel64 Family 6 Model 154 Stepping 4, GenuineIntel', 'measurement_repetitions': 1}`. Sequential fresh workers; one sample per job.

Primary worker deadline: 15s including setup; a timeout is censored, not a measured latency. Supplemental budgets, when used, are pinned per measurement batch in JSON.

Times are warm operation seconds. Peak memory is MiB, including worker setup; it is an actual process peak, not Python-only allocations.

| N | Scenario | Measurement | Stage1 / Final | Status | States | Feasible | Shortlist | Seconds | Peak MiB |
|---|---|---|---|---|---:|---:|---:|---:|---:|
| 15 | easy | search | None / None | completed | 1279 | 1 | 1 | 0.0118 | 86.1719 |
| 15 | easy | stage1_ranking | balance_first / None | completed | 1279 | 1 | 1 | 0.0030 | 179.8398 |
| 15 | easy | stage1_ranking | pareto / None | completed | 1279 | 1 | 1 | 0.0099 | 179.8398 |
| 15 | easy | final_ranking | None / balance_first | completed | 1279 | 1 | 1 | 0.0047 | 180.2344 |
| 15 | easy | final_ranking | None / pareto | completed | 1279 | 1 | 1 | 0.0068 | 180.2266 |
| 15 | easy | full | balance_first / balance_first | completed | 1279 | 1 | 1 | 0.5595 | 179.9961 |
| 15 | easy | full | balance_first / pareto | completed | 1279 | 1 | 1 | 0.4476 | 180.6797 |
| 15 | easy | full | pareto / balance_first | completed | 1279 | 1 | 1 | 0.4713 | 180.4570 |
| 15 | easy | full | pareto / pareto | completed | 1279 | 1 | 1 | 0.5807 | 180.3047 |
| 15 | fractional_zero_constraints | search | None / None | completed | 5391 | 76 | 50 | 0.0324 | 85.8047 |
| 15 | fractional_zero_constraints | stage1_ranking | balance_first / None | completed | 5391 | 76 | 50 | 0.1581 | 180.1250 |
| 15 | fractional_zero_constraints | stage1_ranking | pareto / None | completed | 5391 | 76 | 50 | 0.1914 | 180.1328 |
| 15 | fractional_zero_constraints | final_ranking | None / balance_first | completed | 5391 | 76 | 50 | 0.0633 | 179.9531 |
| 15 | fractional_zero_constraints | final_ranking | None / pareto | completed | 5391 | 76 | 50 | 0.1009 | 180.5664 |
| 15 | fractional_zero_constraints | full | balance_first / balance_first | completed | 5391 | 76 | 50 | 1.0040 | 179.8242 |
| 15 | fractional_zero_constraints | full | balance_first / pareto | completed | 5391 | 76 | 50 | 1.1623 | 180.3281 |
| 15 | fractional_zero_constraints | full | pareto / balance_first | completed | 5391 | 76 | 50 | 2.8733 | 180.1055 |
| 15 | fractional_zero_constraints | full | pareto / pareto | completed | 5391 | 76 | 50 | 3.2095 | 180.9883 |
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
| 15 | no_solution | stage1_ranking | balance_first / None | completed | 3639 | 0 | 0 | 0.0000 | 180.5117 |
| 15 | no_solution | stage1_ranking | pareto / None | completed | 3639 | 0 | 0 | 0.0000 | 180.6367 |
| 15 | no_solution | final_ranking | None / balance_first | completed | 3639 | 0 | 0 | 0.0000 | 180.1094 |
| 15 | no_solution | final_ranking | None / pareto | completed | 3639 | 0 | 0 | 0.0000 | 180.2305 |
| 15 | no_solution | full | balance_first / balance_first | completed | 3639 | 0 | 0 | 0.3115 | 180.4102 |
| 15 | no_solution | full | balance_first / pareto | completed | 3639 | 0 | 0 | 0.3849 | 180.2188 |
| 15 | no_solution | full | pareto / balance_first | completed | 3639 | 0 | 0 | 0.1643 | 179.9805 |
| 15 | no_solution | full | pareto / pareto | completed | 3639 | 0 | 0 | 0.1972 | 180.4297 |
| 20 | easy | search | None / None | completed | 1919 | 1 | 1 | 0.0215 | 85.5039 |
| 20 | easy | stage1_ranking | balance_first / None | completed | 1919 | 1 | 1 | 0.0046 | 180.3789 |
| 20 | easy | stage1_ranking | pareto / None | completed | 1919 | 1 | 1 | 0.0052 | 180.1211 |
| 20 | easy | final_ranking | None / balance_first | completed | 1919 | 1 | 1 | 0.0099 | 179.9844 |
| 20 | easy | final_ranking | None / pareto | completed | 1919 | 1 | 1 | 0.0081 | 180.2773 |
| 20 | easy | full | balance_first / balance_first | completed | 1919 | 1 | 1 | 0.4421 | 180.3867 |
| 20 | easy | full | balance_first / pareto | completed | 1919 | 1 | 1 | 0.3424 | 180.0000 |
| 20 | easy | full | pareto / balance_first | completed | 1919 | 1 | 1 | 0.2558 | 179.9727 |
| 20 | easy | full | pareto / pareto | completed | 1919 | 1 | 1 | 0.4923 | 180.2266 |
| 20 | fractional_zero_constraints | search | None / None | completed | 13451 | 190 | 50 | 0.0347 | 85.7695 |
| 20 | fractional_zero_constraints | stage1_ranking | balance_first / None | completed | 13451 | 190 | 50 | 0.3557 | 180.9531 |
| 20 | fractional_zero_constraints | stage1_ranking | pareto / None | completed | 13451 | 190 | 50 | 0.3060 | 180.4375 |
| 20 | fractional_zero_constraints | final_ranking | None / balance_first | completed | 13451 | 190 | 50 | 0.1375 | 180.2617 |
| 20 | fractional_zero_constraints | final_ranking | None / pareto | completed | 13451 | 190 | 50 | 0.0863 | 179.9727 |
| 20 | fractional_zero_constraints | full | balance_first / balance_first | completed | 13451 | 190 | 50 | 2.1296 | 180.0781 |
| 20 | fractional_zero_constraints | full | balance_first / pareto | completed | 13451 | 190 | 50 | 2.5431 | 180.1953 |
| 20 | fractional_zero_constraints | full | pareto / balance_first | completed | 13451 | 190 | 50 | 2.9159 | 180.6523 |
| 20 | fractional_zero_constraints | full | pareto / pareto | completed | 13451 | 190 | 50 | 3.2462 | 180.4102 |
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
| 20 | no_solution | stage1_ranking | balance_first / None | completed | 11969 | 0 | 0 | 0.0000 | 180.2891 |
| 20 | no_solution | stage1_ranking | pareto / None | completed | 11969 | 0 | 0 | 0.0000 | 180.4570 |
| 20 | no_solution | final_ranking | None / balance_first | completed | 11969 | 0 | 0 | 0.0000 | 180.2383 |
| 20 | no_solution | final_ranking | None / pareto | completed | 11969 | 0 | 0 | 0.0000 | 180.8984 |
| 20 | no_solution | full | balance_first / balance_first | completed | 11969 | 0 | 0 | 0.3382 | 180.0312 |
| 20 | no_solution | full | balance_first / pareto | completed | 11969 | 0 | 0 | 0.4075 | 180.5508 |
| 20 | no_solution | full | pareto / balance_first | completed | 11969 | 0 | 0 | 0.2880 | 180.3398 |
| 20 | no_solution | full | pareto / pareto | completed | 11969 | 0 | 0 | 0.3711 | 180.4219 |
| 25 | easy | search | None / None | completed | 2559 | 1 | 1 | 0.0261 | 85.8008 |
| 25 | easy | stage1_ranking | balance_first / None | completed | 2559 | 1 | 1 | 0.0039 | 180.0156 |
| 25 | easy | stage1_ranking | pareto / None | completed | 2559 | 1 | 1 | 0.0053 | 180.6758 |
| 25 | easy | final_ranking | None / balance_first | completed | 2559 | 1 | 1 | 0.0053 | 179.8750 |
| 25 | easy | final_ranking | None / pareto | completed | 2559 | 1 | 1 | 0.0056 | 180.5156 |
| 25 | easy | full | balance_first / balance_first | completed | 2559 | 1 | 1 | 0.4930 | 180.3320 |
| 25 | easy | full | balance_first / pareto | completed | 2559 | 1 | 1 | 0.5208 | 180.3711 |
| 25 | easy | full | pareto / balance_first | completed | 2559 | 1 | 1 | 0.5053 | 180.3828 |
| 25 | easy | full | pareto / pareto | completed | 2559 | 1 | 1 | 0.4897 | 181.0703 |
| 25 | fractional_zero_constraints | search | None / None | completed | 27615 | 290 | 50 | 0.0394 | 85.7656 |
| 25 | fractional_zero_constraints | stage1_ranking | balance_first / None | completed | 27615 | 290 | 50 | 0.3653 | 180.7070 |
| 25 | fractional_zero_constraints | stage1_ranking | pareto / None | completed | 27615 | 290 | 50 | 0.5074 | 180.0078 |
| 25 | fractional_zero_constraints | final_ranking | None / balance_first | completed | 27615 | 290 | 50 | 0.0665 | 180.2734 |
| 25 | fractional_zero_constraints | final_ranking | None / pareto | completed | 27615 | 290 | 50 | 0.0741 | 180.2305 |
| 25 | fractional_zero_constraints | full | balance_first / balance_first | completed | 27615 | 290 | 50 | 2.5467 | 180.5664 |
| 25 | fractional_zero_constraints | full | balance_first / pareto | completed | 27615 | 290 | 50 | 2.6590 | 180.2969 |
| 25 | fractional_zero_constraints | full | pareto / balance_first | completed | 27615 | 290 | 50 | 2.8723 | 180.5234 |
| 25 | fractional_zero_constraints | full | pareto / pareto | completed | 27615 | 290 | 50 | 3.6972 | 180.4102 |
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
| 25 | no_solution | stage1_ranking | balance_first / None | completed | 29899 | 0 | 0 | 0.0000 | 180.5820 |
| 25 | no_solution | stage1_ranking | pareto / None | completed | 29899 | 0 | 0 | 0.0000 | 179.8516 |
| 25 | no_solution | final_ranking | None / balance_first | completed | 29899 | 0 | 0 | 0.0000 | 180.4570 |
| 25 | no_solution | final_ranking | None / pareto | completed | 29899 | 0 | 0 | 0.0000 | 180.6758 |
| 25 | no_solution | full | balance_first / balance_first | completed | 29899 | 0 | 0 | 0.1835 | 180.2188 |
| 25 | no_solution | full | balance_first / pareto | completed | 29899 | 0 | 0 | 0.1797 | 179.8438 |
| 25 | no_solution | full | pareto / balance_first | completed | 29899 | 0 | 0 | 0.1926 | 180.5859 |
| 25 | no_solution | full | pareto / pareto | completed | 29899 | 0 | 0 | 0.2085 | 179.3711 |
| 30 | easy | search | None / None | completed | 3199 | 1 | 1 | 0.0276 | 85.7031 |
| 30 | easy | stage1_ranking | balance_first / None | completed | 3199 | 1 | 1 | 0.0033 | 180.5391 |
| 30 | easy | stage1_ranking | pareto / None | completed | 3199 | 1 | 1 | 0.0043 | 180.3008 |
| 30 | easy | final_ranking | None / balance_first | completed | 3199 | 1 | 1 | 0.0040 | 180.3906 |
| 30 | easy | final_ranking | None / pareto | completed | 3199 | 1 | 1 | 0.0039 | 179.9648 |
| 30 | easy | full | balance_first / balance_first | completed | 3199 | 1 | 1 | 0.7362 | 180.4883 |
| 30 | easy | full | balance_first / pareto | completed | 3199 | 1 | 1 | 0.6189 | 180.3203 |
| 30 | easy | full | pareto / balance_first | completed | 3199 | 1 | 1 | 0.6480 | 180.1016 |
| 30 | easy | full | pareto / pareto | completed | 3199 | 1 | 1 | 1.7454 | 180.8906 |
| 30 | fractional_zero_constraints | search | None / None | completed | 48231 | 508 | 50 | 0.0668 | 86.0430 |
| 30 | fractional_zero_constraints | stage1_ranking | balance_first / None | completed | 48231 | 508 | 50 | 1.1594 | 180.0664 |
| 30 | fractional_zero_constraints | stage1_ranking | pareto / None | completed | 48231 | 508 | 50 | 1.0327 | 179.9844 |
| 30 | fractional_zero_constraints | final_ranking | None / balance_first | completed | 48231 | 508 | 50 | 0.1066 | 180.5430 |
| 30 | fractional_zero_constraints | final_ranking | None / pareto | completed | 48231 | 508 | 50 | 0.0850 | 180.4844 |
| 30 | fractional_zero_constraints | full | balance_first / balance_first | completed | 48231 | 508 | 50 | 4.8538 | 180.4766 |
| 30 | fractional_zero_constraints | full | balance_first / pareto | completed | 48231 | 508 | 50 | 5.5228 | 180.7266 |
| 30 | fractional_zero_constraints | full | pareto / balance_first | completed | 48231 | 508 | 50 | 4.6141 | 179.8867 |
| 30 | fractional_zero_constraints | full | pareto / pareto | completed | 48231 | 508 | 50 | 5.0334 | 181.0078 |
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
| 30 | no_solution | stage1_ranking | balance_first / None | completed | 62929 | 0 | 0 | 0.0000 | 180.5898 |
| 30 | no_solution | stage1_ranking | pareto / None | completed | 62929 | 0 | 0 | 0.0000 | 180.3906 |
| 30 | no_solution | final_ranking | None / balance_first | completed | 62929 | 0 | 0 | 0.0000 | 180.4570 |
| 30 | no_solution | final_ranking | None / pareto | completed | 62929 | 0 | 0 | 0.0000 | 180.3867 |
| 30 | no_solution | full | balance_first / balance_first | completed | 62929 | 0 | 0 | 0.2067 | 180.4219 |
| 30 | no_solution | full | balance_first / pareto | completed | 62929 | 0 | 0 | 0.2124 | 179.9609 |
| 30 | no_solution | full | pareto / balance_first | completed | 62929 | 0 | 0 | 0.2224 | 180.1133 |
| 30 | no_solution | full | pareto / pareto | completed | 62929 | 0 | 0 | 0.2069 | 180.2148 |
| 35 stress | easy | search | None / None | completed | 3839 | 1 | 1 | 0.0309 | 85.8359 |
| 35 stress | easy | stage1_ranking | balance_first / None | completed | 3839 | 1 | 1 | 0.0032 | 179.8203 |
| 35 stress | easy | stage1_ranking | pareto / None | completed | 3839 | 1 | 1 | 0.0038 | 180.2227 |
| 35 stress | easy | final_ranking | None / balance_first | completed | 3839 | 1 | 1 | 0.0034 | 180.6289 |
| 35 stress | easy | final_ranking | None / pareto | completed | 3839 | 1 | 1 | 0.0041 | 180.3984 |
| 35 stress | easy | full | balance_first / balance_first | completed | 3839 | 1 | 1 | 0.3428 | 180.4766 |
| 35 stress | easy | full | balance_first / pareto | completed | 3839 | 1 | 1 | 0.3087 | 180.5742 |
| 35 stress | easy | full | pareto / balance_first | completed | 3839 | 1 | 1 | 0.3055 | 180.5312 |
| 35 stress | easy | full | pareto / pareto | completed | 3839 | 1 | 1 | 0.3110 | 180.4219 |
| 35 stress | fractional_zero_constraints | search | None / None | completed | 77011 | 730 | 50 | 0.0815 | 85.8672 |
| 35 stress | fractional_zero_constraints | stage1_ranking | balance_first / None | completed | 77011 | 730 | 50 | 1.2682 | 180.4180 |
| 35 stress | fractional_zero_constraints | stage1_ranking | pareto / None | completed | 77011 | 730 | 50 | 1.5911 | 180.5859 |
| 35 stress | fractional_zero_constraints | final_ranking | None / balance_first | completed | 77011 | 730 | 50 | 0.0795 | 179.8516 |
| 35 stress | fractional_zero_constraints | final_ranking | None / pareto | completed | 77011 | 730 | 50 | 0.0788 | 180.3398 |
| 35 stress | fractional_zero_constraints | full | balance_first / balance_first | completed | 77011 | 730 | 50 | 7.0499 | 180.7500 |
| 35 stress | fractional_zero_constraints | full | balance_first / pareto | completed | 77011 | 730 | 50 | 7.0668 | 180.4375 |
| 35 stress | fractional_zero_constraints | full | pareto / balance_first | completed | 77011 | 730 | 50 | 6.9470 | 180.1914 |
| 35 stress | fractional_zero_constraints | full | pareto / pareto | completed | 77011 | 730 | 50 | 7.3955 | 180.3008 |
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
| 35 stress | no_solution | stage1_ranking | balance_first / None | completed | 117809 | 0 | 0 | 0.0000 | 180.1250 |
| 35 stress | no_solution | stage1_ranking | pareto / None | completed | 117809 | 0 | 0 | 0.0000 | 180.3672 |
| 35 stress | no_solution | final_ranking | None / balance_first | completed | 117809 | 0 | 0 | 0.0000 | 179.8945 |
| 35 stress | no_solution | final_ranking | None / pareto | completed | 117809 | 0 | 0 | 0.0000 | 180.0938 |
| 35 stress | no_solution | full | balance_first / balance_first | completed | 117809 | 0 | 0 | 0.4364 | 180.5234 |
| 35 stress | no_solution | full | balance_first / pareto | completed | 117809 | 0 | 0 | 0.2581 | 180.1445 |
| 35 stress | no_solution | full | pareto / balance_first | completed | 117809 | 0 | 0 | 0.2554 | 180.0508 |
| 35 stress | no_solution | full | pareto / pareto | completed | 117809 | 0 | 0 | 0.2514 | 180.3320 |
| 15 | dense_ties | stage1_ranking | balance_first / None | completed | 9645 | 1365 | 50 | 1.9636 | 179.8203 |
| 15 | dense_ties | stage1_ranking | pareto / None | completed | 9645 | 1365 | 50 | 3.8735 | 180.6484 |
| 15 | dense_ties | final_ranking | None / balance_first | completed | 9645 | 1365 | 50 | 0.0766 | 180.3828 |
| 15 | dense_ties | final_ranking | None / pareto | completed | 9645 | 1365 | 50 | 0.0796 | 180.3203 |
| 15 | dense_ties | full | balance_first / balance_first | completed | 9645 | 1365 | 50 | 11.8031 | 179.7773 |
| 15 | dense_ties | full | balance_first / pareto | completed | 9645 | 1365 | 50 | 12.3219 | 180.0195 |
| 15 | dense_ties | full | pareto / balance_first | completed | 9645 | 1365 | 50 | 13.6881 | 180.5312 |
| 15 | dense_ties | full | pareto / pareto | completed | 9645 | 1365 | 50 | 14.7530 | 179.9414 |
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

Prior global-shortlist retention/tradeoff evidence: [Phase 5 comparison](../two_stage_phase5/comparison.md), SHA-256 pinned in JSON. This is a saved evidence snapshot, not a new historical run.

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
| 15 / fractional_zero_constraints / balance_first | 0 | 0.0000 | 0.0330 | -0.1520 | 0.0000 | -0.1190 |
| 15 / fractional_zero_constraints / pareto | 1 | 0.0000 | 0.0192 | -0.1013 | 0.0000 | -0.0794 |
| 20 / easy / balance_first | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 20 / easy / pareto | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 20 / fractional_zero_constraints / balance_first | 0 | 0.0000 | 0.0317 | -0.1520 | 0.0000 | -0.1190 |
| 20 / fractional_zero_constraints / pareto | 0 | 0.0000 | 0.0317 | -0.1520 | 0.0000 | -0.1190 |
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
| 15 / easy | balance_first / balance_first | completed | 0.5595 | 1.9231 | 1.3171 | 0.0000 | 0.0000 | 0.0476 |
| 15 / easy | balance_first / pareto | completed | 0.4476 | 1.9231 | 1.3171 | 0.0000 | 0.0000 | 0.0476 |
| 15 / easy | pareto / balance_first | completed | 0.4713 | 1.9231 | 1.3171 | 0.0000 | 0.0000 | 0.0476 |
| 15 / easy | pareto / pareto | completed | 0.5807 | 1.9231 | 1.3171 | 0.0000 | 0.0000 | 0.0476 |
| 15 / fractional_zero_constraints | balance_first / balance_first | completed | 1.0040 | 1.9231 | 1.3747 | 0.0147 | 0.0000 | 0.0476 |
| 15 / fractional_zero_constraints | balance_first / pareto | completed | 1.1623 | 1.9231 | 1.3609 | 0.0654 | 0.0000 | 0.0873 |
| 15 / fractional_zero_constraints | pareto / balance_first | completed | 2.8733 | 1.9231 | 1.3747 | 0.0147 | 0.0000 | 0.0476 |
| 15 / fractional_zero_constraints | pareto / pareto | completed | 3.2095 | 1.9231 | 1.3609 | 0.0654 | 0.0000 | 0.0873 |
| 15 / dense_ties | balance_first / balance_first | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 15 / dense_ties | balance_first / pareto | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 15 / dense_ties | pareto / balance_first | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 15 / dense_ties | pareto / pareto | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 15 / no_solution | balance_first / balance_first | completed | 0.3115 | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 15 / no_solution | balance_first / pareto | completed | 0.3849 | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 15 / no_solution | pareto / balance_first | completed | 0.1643 | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 15 / no_solution | pareto / pareto | completed | 0.1972 | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 20 / easy | balance_first / balance_first | completed | 0.4421 | 1.9231 | 1.3171 | 0.0000 | 0.0000 | 0.0476 |
| 20 / easy | balance_first / pareto | completed | 0.3424 | 1.9231 | 1.3171 | 0.0000 | 0.0000 | 0.0476 |
| 20 / easy | pareto / balance_first | completed | 0.2558 | 1.9231 | 1.3171 | 0.0000 | 0.0000 | 0.0476 |
| 20 / easy | pareto / pareto | completed | 0.4923 | 1.9231 | 1.3171 | 0.0000 | 0.0000 | 0.0476 |
| 20 / fractional_zero_constraints | balance_first / balance_first | completed | 2.1296 | 1.9231 | 1.3715 | 0.0147 | 0.0000 | 0.0476 |
| 20 / fractional_zero_constraints | balance_first / pareto | completed | 2.5431 | 1.9231 | 1.3715 | 0.0147 | 0.0000 | 0.0476 |
| 20 / fractional_zero_constraints | pareto / balance_first | completed | 2.9159 | 1.9231 | 1.3715 | 0.0147 | 0.0000 | 0.0476 |
| 20 / fractional_zero_constraints | pareto / pareto | completed | 3.2462 | 1.9231 | 1.3715 | 0.0147 | 0.0000 | 0.0476 |
| 20 / dense_ties | balance_first / balance_first | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 20 / dense_ties | balance_first / pareto | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 20 / dense_ties | pareto / balance_first | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 20 / dense_ties | pareto / pareto | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 20 / no_solution | balance_first / balance_first | completed | 0.3382 | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 20 / no_solution | balance_first / pareto | completed | 0.4075 | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 20 / no_solution | pareto / balance_first | completed | 0.2880 | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 20 / no_solution | pareto / pareto | completed | 0.3711 | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 25 / easy | balance_first / balance_first | completed | 0.4930 | 1.9231 | 1.3171 | 0.0000 | 0.0000 | 0.0476 |
| 25 / easy | balance_first / pareto | completed | 0.5208 | 1.9231 | 1.3171 | 0.0000 | 0.0000 | 0.0476 |
| 25 / easy | pareto / balance_first | completed | 0.5053 | 1.9231 | 1.3171 | 0.0000 | 0.0000 | 0.0476 |
| 25 / easy | pareto / pareto | completed | 0.4897 | 1.9231 | 1.3171 | 0.0000 | 0.0000 | 0.0476 |
| 25 / fractional_zero_constraints | balance_first / balance_first | completed | 2.5467 | 1.9231 | 1.3715 | 0.0147 | 0.0000 | 0.0476 |
| 25 / fractional_zero_constraints | balance_first / pareto | completed | 2.6590 | 1.9231 | 1.3715 | 0.0147 | 0.0000 | 0.0476 |
| 25 / fractional_zero_constraints | pareto / balance_first | completed | 2.8723 | 1.9231 | 1.3715 | 0.0147 | 0.0000 | 0.0476 |
| 25 / fractional_zero_constraints | pareto / pareto | completed | 3.6972 | 1.9231 | 1.3715 | 0.0147 | 0.0000 | 0.0476 |
| 25 / dense_ties | balance_first / balance_first | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 25 / dense_ties | balance_first / pareto | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 25 / dense_ties | pareto / balance_first | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 25 / dense_ties | pareto / pareto | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 25 / no_solution | balance_first / balance_first | completed | 0.1835 | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 25 / no_solution | balance_first / pareto | completed | 0.1797 | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 25 / no_solution | pareto / balance_first | completed | 0.1926 | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 25 / no_solution | pareto / pareto | completed | 0.2085 | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 30 / easy | balance_first / balance_first | completed | 0.7362 | 1.9231 | 1.3171 | 0.0000 | 0.0000 | 0.0476 |
| 30 / easy | balance_first / pareto | completed | 0.6189 | 1.9231 | 1.3171 | 0.0000 | 0.0000 | 0.0476 |
| 30 / easy | pareto / balance_first | completed | 0.6480 | 1.9231 | 1.3171 | 0.0000 | 0.0000 | 0.0476 |
| 30 / easy | pareto / pareto | completed | 1.7454 | 1.9231 | 1.3171 | 0.0000 | 0.0000 | 0.0476 |
| 30 / fractional_zero_constraints | balance_first / balance_first | completed | 4.8538 | 1.9231 | 1.3715 | 0.0147 | 0.0000 | 0.0476 |
| 30 / fractional_zero_constraints | balance_first / pareto | completed | 5.5228 | 1.9231 | 1.3715 | 0.0147 | 0.0000 | 0.0476 |
| 30 / fractional_zero_constraints | pareto / balance_first | completed | 4.6141 | 1.9231 | 1.3715 | 0.0147 | 0.0000 | 0.0476 |
| 30 / fractional_zero_constraints | pareto / pareto | completed | 5.0334 | 1.9231 | 1.3715 | 0.0147 | 0.0000 | 0.0476 |
| 30 / dense_ties | balance_first / balance_first | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 30 / dense_ties | balance_first / pareto | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 30 / dense_ties | pareto / balance_first | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 30 / dense_ties | pareto / pareto | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 30 / no_solution | balance_first / balance_first | completed | 0.2067 | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 30 / no_solution | balance_first / pareto | completed | 0.2124 | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 30 / no_solution | pareto / balance_first | completed | 0.2224 | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 30 / no_solution | pareto / pareto | completed | 0.2069 | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 35 / easy | balance_first / balance_first | completed | 0.3428 | 1.9231 | 1.3171 | 0.0000 | 0.0000 | 0.0476 |
| 35 / easy | balance_first / pareto | completed | 0.3087 | 1.9231 | 1.3171 | 0.0000 | 0.0000 | 0.0476 |
| 35 / easy | pareto / balance_first | completed | 0.3055 | 1.9231 | 1.3171 | 0.0000 | 0.0000 | 0.0476 |
| 35 / easy | pareto / pareto | completed | 0.3110 | 1.9231 | 1.3171 | 0.0000 | 0.0000 | 0.0476 |
| 35 / fractional_zero_constraints | balance_first / balance_first | completed | 7.0499 | 1.9231 | 1.3715 | 0.0147 | 0.0000 | 0.0476 |
| 35 / fractional_zero_constraints | balance_first / pareto | completed | 7.0668 | 1.9231 | 1.3715 | 0.0147 | 0.0000 | 0.0476 |
| 35 / fractional_zero_constraints | pareto / balance_first | completed | 6.9470 | 1.9231 | 1.3715 | 0.0147 | 0.0000 | 0.0476 |
| 35 / fractional_zero_constraints | pareto / pareto | completed | 7.3955 | 1.9231 | 1.3715 | 0.0147 | 0.0000 | 0.0476 |
| 35 / dense_ties | balance_first / balance_first | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 35 / dense_ties | balance_first / pareto | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 35 / dense_ties | pareto / balance_first | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 35 / dense_ties | pareto / pareto | timeout | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 35 / no_solution | balance_first / balance_first | completed | 0.4364 | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 35 / no_solution | balance_first / pareto | completed | 0.2581 | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 35 / no_solution | pareto / balance_first | completed | 0.2554 | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 35 / no_solution | pareto / pareto | completed | 0.2514 | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| 15 / dense_ties | balance_first / balance_first | completed | 11.8031 | 2.0833 | 0.9141 | 0.0147 | 0.0000 | 0.0000 |
| 15 / dense_ties | balance_first / pareto | completed | 12.3219 | 2.0833 | 0.9141 | 0.0147 | 0.0000 | 0.0000 |
| 15 / dense_ties | pareto / balance_first | completed | 13.6881 | 2.0833 | 0.9141 | 0.0147 | 0.0000 | 0.0000 |
| 15 / dense_ties | pareto / pareto | completed | 14.7530 | 2.0833 | 0.9141 | 0.0147 | 0.0000 | 0.0000 |

## Limits and decisions still required

- One measurement per fresh process; no production SLA, tail latency or throughput claim.
- Peak includes setup/native allocations; ranking preparation peak is not ranker-only incremental memory.
- Search/full timing includes optional counter overhead; ranking timing excludes search and metrics preparation.
- Timeouts censor complete counts, latency and memory; worker lower bounds are not request latency lower bounds.
- Dense ties use identical new-course model features; repeat candidates retain their official attempt feature.
- Synthetic history exercises fallback and does not measure the size/cost of real history.
- Final comparisons use the same fixed academic Stage 1 shortlist; full pairs use their actual chosen shortlist.
- Zero seconds for an empty ranking workload means no ranker invocation; it is not a timed inference/search measurement.
- No global Top K guarantee or empirical student outcome improvement; approvals require human review.

backend_max_candidate_count / recommendation_latency_sla / memory_budget_per_request = UNRESOLVED.

Review and approve Stage 1, Final, and their combination independently before Phase 7 manifest work. No choice was approved by this benchmark.
