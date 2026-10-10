# Corrected Phase 6 Result

Date: 2026-10-07. Scope: **Phase 6 only**. All strategy recommendations below are **RECOMMENDED**, with no approval or serving change. The official plan remains [RECOMMENDATION_TWO_STAGE_IMPLEMENTATION_PLAN.md](<D:/AI/Real projects/Academic_Advisor_Simple/docs/architecture/RECOMMENDATION_TWO_STAGE_IMPLEMENTATION_PLAN.md>).

## Evidence validity

The earlier benchmark supplied `grade_version_id=1`, which is absent from the loaded GradeScale pass bands. Marks around 65 therefore converted to zero points. Every old observation involving model inference or ranking was invalidated, including runtime, memory and timeouts whose independence from this mistake could not be proven.

| Evidence | OLD / INVALIDATED RESULT | CORRECTED RESULT |
|---|---|---|
| Non-search observations | 168 stale: 42 Stage1, 42 Final, 84 full; 128 completed and 40 censored | All 168 rerun in fresh sequential workers: 128 completed, 40 freshly censored, zero worker errors |
| Pure search | 25 measurements demonstrably load neither models nor GradeScale | Retained unchanged, explicitly labeled `RETAINED / UNAFFECTED SEARCH`; not claimed as new measurements |
| Combined benchmark | 193 old observations | 193 records: 168 replacements plus 25 retained search records; 153 completed and 40 censored |
| Easy N=15, Balance/Balance, expected plan GPA | 0.000000, invalid conversion | 1.000000 with supported GradeVersion 1.111 |
| Same easy case, projected cumulative GPA | 1.923077, invalid conversion | 2.153846 |
| Phase5 comparison | Fabricated predictions over 176 synthetic plans | Excluded from corrected real-model quality conclusions; original bytes preserved |
| Ranking quality and recall | Incomplete corrected evidence | Both real pinned 33/47 Grade/Fail pairs; complete bounded Stage2 oracles and independent fixed-pool Final comparisons |

The numerical GPA correction is a conversion repair, not evidence of improved student outcomes. No old non-search metric is copied into a corrected observation. Four original Phase6 reports remain byte-identical and are also archived under [old_invalidated](<D:/AI/Real projects/Academic_Advisor_Simple/reports/two_stage_phase6/corrected/old_invalidated/README.md>).

GradeVersion provenance is separated deliberately:

- **Benchmark replacement coverage: 1.111.** This is the corrected benchmark's lowest supported pass-band version. Conversion is valid, but both models encode it as `__UNKNOWN__` because their saved category lists contain 2.111/3.111. These observations describe that benchmark workload; they are not silently combined with the quality sample.
- **Primary quality: 2.111.** Supported by GradeScale and a known saved category in both stages.
- **Sensitivity: 3.111.** Also supported and known; the same eleven cases were rerun separately. Prediction-only Stage1 values and all Stage2 prediction/metric hashes match the primary run for these cases. Full Stage1 scored-frame hashes differ because the GradeVersion input differs. This does not prove universal equivalence between versions.

Each quality run evaluates **11 predefined synthetic cases, 1,750 feasible plans and 8,210 Stage2 rows**, before its additional permutation verification. Historical outcomes are fabricated in memory, with 30 rows/course at cutoff 20243. No real student records, historical bundles, datasets, training or backend are used. Every fixture has at most 441 plans, below the explicit offline oracle bound of 1,000. Candidate IDs are synthetic and may be unknown model categories; this is controlled diagnostic evidence, not a representative student cohort.

Raw reproducible evidence:

- [Corrected benchmark JSON](<D:/AI/Real projects/Academic_Advisor_Simple/reports/two_stage_phase6/corrected/benchmark.json>) and [benchmark tables](<D:/AI/Real projects/Academic_Advisor_Simple/reports/two_stage_phase6/corrected/benchmark.md>).
- [Primary 2.111 quality evidence](<D:/AI/Real projects/Academic_Advisor_Simple/reports/two_stage_phase6/corrected/corrected_ranking_evaluation.json>).
- [Separate 3.111 sensitivity](<D:/AI/Real projects/Academic_Advisor_Simple/reports/two_stage_phase6/corrected/grade_version_3_sensitivity.json>).
- [Derived review metrics](<D:/AI/Real projects/Academic_Advisor_Simple/reports/two_stage_phase6/corrected/review_metrics.json>) with input hashes and [its reproducible source](<D:/AI/Real projects/Academic_Advisor_Simple/reports/two_stage_phase6/corrected/measurement_source/summarize_evidence.py.txt>).

The uninterrupted benchmark completed before resume-provenance hardening. Exact measurement source copies are preserved under `measurement_source/` and match the hashes recorded in `rerun_progress.json` and `benchmark.json`. Future resume refuses this historical checkpoint, which lacks the new pinned context; no checkpoint was migrated or blended. The worker, models and all Production sources remained fixed during the measured run.

## Stage 1 comparison

Stage1 is evaluated as a filter: can it retain plans that the actual 47-feature Stage2 ranker prefers? It is not selected for having the smallest Balance penalty.

Strict `recall@50 = |shortlist IDs intersect complete Stage2 Top-K IDs| / min(K, feasible plans)`. Identity and deterministic tie order are preserved. Headline aggregation uses the **nine cases with more than 50 plans**; easy has one plan and is shown separately, while no-solution recall is undefined. Each case has K=3/10 available, so equal-case macro and pooled recall coincide. Exact-objective tie sensitivity equals strict recall in this evidence and does not replace it.

| Stage1 strategy | Stage2 oracle | Top-3 recall@50 | Top-10 recall@50 | Other metrics / Notes |
|---|---|---:|---:|---|
| balance_first v1 | balance_first | 27/27 = 100.00% | 90/90 = 100.00% | Full retention for this Final objective |
| pareto v1 | balance_first | 25/27 = 92.59% | 86/90 = 95.56% | Loses 2/4 oracle positions respectively |
| balance_first v1 | pareto | 25/27 = 92.59% | 66/90 = 73.33% | Loses 2/24 positions |
| pareto v1 | pareto | 26/27 = 96.30% | 85/90 = 94.44% | Loses 1/5 positions |
| balance_first v1 | academic diagnostic | 12/27 = 44.44% | 46/90 = 51.11% | Diagnostic reference, not another approved candidate |
| pareto v1 | academic diagnostic | 26/27 = 96.30% | 81/90 = 90.00% | Greater protection of academic choices |

These are separate objectives: 100% against Balance-first and 96.30% against Pareto cannot be treated as scores against one common oracle. Across both candidate Final oracles, Balance Stage1 actually has the higher average Top3 retention (96.30% vs 94.44%). Pareto Stage1 has broader Top10 retention (95.00% vs 86.67%). The recommendation prioritizes Top10 coverage and protection against premature academic exclusion, with the recommended Final oracle reported explicitly.

Within the **seven fully in-scope >50 cases**, Stage1 Balance/Pareto recall against the Pareto Final oracle is respectively **90.48%/95.24% for Top3** and **65.71%/92.86% for Top10**. The mixed-scope and summer cases are not allowed to dilute this effect.

| Case | Feasible plans | B/P shortlist overlap /50 | Balance Stage1 → Pareto oracle retained Top3 / Top10 | Pareto Stage1 → Pareto oracle retained Top3 / Top10 |
|---|---:|---:|---:|---:|
| retake_weak | 176 | 32 | 3/3; 7/10 | 3/3; 10/10 |
| retake_strong | 176 | 24 | 3/3; 6/10 | 2/3; 7/10 |
| alternating | 176 | 28 | 3/3; 8/10 | 3/3; 10/10 |
| low_gpa | 176 | 34 | 2/3; 6/10 | 3/3; 9/10 |
| high_gpa | 176 | 35 | 2/3; 5/10 | 3/3; 10/10 |
| load_12 | 441 | 19 | 3/3; 4/10 | 3/3; 9/10 |
| fractional_zero | 76 | 48 | 3/3; 10/10 | 3/3; 10/10 |
| mixed_scope | 176 | 48 | 3/3; 10/10 | 3/3; 10/10 |
| summer | 176 | 50 | 3/3; 10/10 | 3/3; 10/10 |

Mean B/P shortlist overlap is 35.33/50; overlap with the Stage1 academic shortlist is 31.56/50 for Balance and 38.44/50 for Pareto. Mean shortlist characteristics below use the seven fully in-scope cases and their **actual Stage2 predictions**, not Stage1 proxies:

| Stage1 strategy | Projected GPA | Expected plan GPA | Expected failed credits | Failed penalty | Withdrawn penalty | Total previous penalty |
|---|---:|---:|---:|---:|---:|---:|
| balance_first | 2.526870 | 2.631881 | 0.878897 | 0.020700 | 0.011765 | 0.076871 |
| pareto | 2.532502 | 2.661536 | 0.831304 | 0.077689 | 0.012706 | 0.081510 |

Pareto retains academically stronger and lower-failure shortlists here despite worse mean Balance penalties. JSON contains per-case min/p25/median/p75/max, Stage1 and Stage2 characteristics, separate ratios, Failed/Withdrawn/New/Other credit distributions, distinct courses/mixes, scope and enabled-component counts. Disabled penalties remain missing. Mixed-scope shortlists have 9 applicable and 41 non-applicable plans; summer has no applicable plans. These plans remain feasible under the existing rules.

Lost plans are explicit. In `retake_strong`, Pareto Stage1 excludes global Pareto Top3 plan `29282e7d…`: projected GPA 2.52, plan GPA 2.60, expected failed credits 0.371629, penalties F/W/T = 0 / 0.023529 / 0.114286. Three global Top10 plans are lost in that case; another one each is lost in `low_gpa` and `load_12`. Full IDs and metrics are recorded in each `lost_plan_details` array. No claim of perfect retention is made.

All candidate-permutation Stage1 full-order/shortlist checks, Stage2 complete metric checks and both independent Final frame-permutation checks passed for both versions. A skipped check or any false Final check cannot produce a global determinism PASS.

## Final ranking comparison

For each case, both Final candidates receive **exactly the same Stage1 academic Top50 IDs and the same Stage2-scored metrics/predictions**. This isolates the Final ranking decision from Stage1 selection. Pool identity, metrics and prediction hashes are saved. Four actual cross-stage shortlists are evaluated separately.

Headline values below are equal-case mean changes versus academic Final ranking, for **seven fully in-scope cases with >50 plans**. Projected GPA uses the existing additive projection and `current_gpa_credits`; it does not replace previous grades. Lower penalties and failed credits are better. Negative penalty deltas mean an improvement; none are summed into a hidden score.

| Strategy / Top-K | Projected GPA Δ | Plan GPA Δ | Expected failed credits Δ | Failed penalty Δ | Withdrawn penalty Δ | Total previous penalty Δ |
|---|---:|---:|---:|---:|---:|---:|
| balance_first / Top3 | −0.013748 | −0.069048 | +0.070172 | −0.107516 | −0.007843 | −0.079365 |
| pareto / Top3 | −0.013709 | −0.067857 | +0.053884 | −0.084407 | −0.000980 | −0.060544 |
| balance_first / Top10 | −0.008498 | −0.044583 | +0.064191 | −0.071835 | −0.002899 | −0.043741 |
| pareto / Top10 | −0.006886 | −0.035595 | +0.010651 | −0.032255 | +0.004244 | −0.015918 |

Pareto versus Balance-first changes Top3 projected GPA by only **+0.00003968**, a negligible academic advantage in this sample, and failed credits by **−0.01628759**. At Top10, differences are **+0.00161218 projected GPA**, **+0.00898810 plan GPA**, and **−0.05354007 failed credits**. All three Balance penalties are worse with Pareto than Balance-first; Pareto's Top10 Withdrawn penalty also worsens versus the academic reference. Pareto does not dominate Balance-first across all six metrics, and neither improves every objective against academic ranking.

The two candidates change Top3 order in 6/7 cases, with set overlap 13/21; Top10 order changes in 7/7, with overlap 40/70. Academic Top3 overlap is 6/21 for Balance and 8/21 for Pareto; Top10 overlap is 35/70 and 40/70. Summer and the mixed-scope TopK retain academic behavior; the one-plan easy case cannot distinguish strategies. All-nonempty aggregates are retained separately in `review_metrics.json`.

Explainability follows the actual code: Balance-first lexicographically prioritizes enabled Failed penalty, then Total Previous, then Withdrawn, then academic metrics/identity. Pareto first orders nondomination fronts using GPA, failure and each enabled penalty, then uses the same complete lexicographic order within a front. Pareto has no hidden weights and is not a GPA-first ranker. Non-applicable plans keep their academic positions. Front membership depends on the pool, so shortlist coverage and actual returned TopK are verified separately rather than assumed equal.

## Trade-off examples

Both examples below use the same **fixed50** pool, not different shortlists. Full IDs/course tuples are in `review_metrics.json`.

| retake_weak fixed50 | Plan A `f7763642…` | Plan B `07beeda2…` |
|---|---:|---:|
| Projected cumulative GPA | 2.540000 | 2.500000 |
| Expected plan GPA | 2.700000 | 2.500000 |
| Expected failed credits | 0.846666 | 1.143941 |
| Failed penalty | 0.166667 | 0.164706 |
| Withdrawn penalty | 0.000000 | 0.000000 |
| Total previous penalty | 0.166667 | 0.114286 |
| Balance-first position | 50 | 39 |
| Pareto position / front (zero-based) | 6 / 0 | 48 / 9 |

Balance-first prefers B because its Failed penalty is lower by about 0.001961, despite GPA being 0.04 lower and expected failed credits about 0.297275 higher. Pareto prefers A because A is on an earlier nondomination front; B is dominated by other plans in this pool. The pair alone does not dominate one another: front order reflects all 50 plans.

In `alternating`, A `cdeb98…` has GPA 2.57, expected failed credits 0.606075 and F/W/T penalties 0.164706/0.023529/0.314286. B `75d082…` has GPA 2.52, failed credits 0.634498 and penalties 0/0.023529/0.114286. Balance-first ranks A/B at 36/25; Pareto ranks them 6/46 (fronts 1/11). Balance is a real objective capable of changing choices; it is not merely a tie-breaker.

## Runtime / benchmark impact

Windows, Python 3.11.5, pandas 3.0.5, one model thread. Fresh isolated benchmark workers run sequentially, one sample per observation. Times are warm operation times; process peak working set includes imports/setup/native allocations. Diagnostic worker deadlines of 15/90 seconds include preparation and are not request SLA or measured latency bounds.

| N | Easy full pipeline, four-pair range (s) | Fractional/zero full range (s) | Dense full pipeline |
|---:|---:|---:|---|
| 15 | 0.237–0.345 | 1.609–2.162 | All four primary attempts censored; supplemental 8.438–18.879s |
| 20 | 0.341–0.868 | 1.990–3.700 | All four censored at 15s worker deadline |
| 25 | 0.383–1.148 | 3.757–4.146 | All four censored at 15s |
| 30 | 0.425–0.582 | 4.461–7.420 | All four censored at 15s |
| 35, stress only | 0.304–0.489 | 5.565–9.461 | All four censored at 15s |

For supplemental dense N=15, Stage1 rank-only time is **1.869s Balance-first vs 7.987s Pareto**. Final rank-only time on the same fixed50 is **0.05893s vs 0.06099s**. Full B/B, B/P, P/B, P/P times are **8.438 / 9.744 / 18.879 / 18.366s**. Preparation is excluded from rank-only timings but included in the worker deadline, explaining why a primary attempt may time out although a later warm measurement is below 15 seconds.

All **40 fresh censored observations** belong to the dense primary workload: 8 per size, covering Stage1, Final and full modes. No elapsed operation time, completed plan count or peak memory is invented for these rows. Completed corrected peaks reach **181.73 MiB**; retained search observations have their older approximately 85.64 MiB process peaks and provenance, not the newer inference environment's cost.

The bounded real-model quality run has diagnostic Stage1 rank means **0.354s Balance vs 0.424s Pareto** over nine cases. These are not isolated timings or production bounds. The GradeVersion 1.111 benchmark and GradeVersion 2.111/3.111 quality runtimes are explicitly different workloads.

Pure search is retained because it does not use GradeVersion:

| All-3-credit exact18 search | States visited | Feasible plans | Retained search seconds |
|---:|---:|---:|---:|
| 15 | 28,885 | 5,005 | 0.144 |
| 20 | 263,567 | 38,760 | 1.207 |
| 25 | 1,421,859 | 177,100 | 6.677 |
| 30 | 5,544,161 | 593,775 | 25.535 |
| 35, stress only | 17,344,623 | 1,623,160 | 68.661 |

**RECOMMENDED: a separate search/metrics/ranking optimization study.** No algorithm or request limit is changed here. Slow/censored full runs alone do not prove search is their bottleneck; the independent search timings above do show search exceeding the plan's >5-second diagnostic category at 25/30 candidates. `backend_max_candidate_count`, latency SLA and memory budget remain `UNRESOLVED`. No operational gate is invented.

## Recommended Stage-1 Strategy

**RECOMMENDED: `pareto`, version `v1`.** The purpose is preservation of valuable Stage2 choices, especially Top10 under the provisional Final Pareto objective and academic diagnostics. It reaches 94.44% Pareto Top10 recall against 73.33% for Balance Stage1, and 90.00% academic Top10 recall against 51.11%. It retains more GPA/failure trade-offs, even though its mean Balance penalties and dense rank cost are worse. It is not universally best at Top3, and has nonzero losses.

If a human chooses **Final Balance-first** instead, **Stage1 Balance-first is the stronger measured retention choice**, with 100% Top3/Top10 on these fixtures. The Stage1 recommendation is therefore a reasoned recommendation for review, not an architecture requirement or default.

## Recommended Final Strategy

**RECOMMENDED: `pareto`, version `v1`.** It exposes nondomination and reduces the measured failure/GPA cost, most clearly at Top10, while treating each Balance component as an independent objective. This accepts weaker Balance improvement and somewhat greater explanation/runtime cost. The tiny Top3 GPA difference is not the basis for the recommendation. Balance-first remains a defensible human choice if strict Balance priority is desired; it can choose lower GPA/higher failure for small improvements in an earlier penalty.

## Recommended Combination

**RECOMMENDED: `pareto v1 → pareto v1`.** This is the result of the two independent evaluations, not an assumption that names must match.

| Stage1 / Final | Actual returned Top3 overlap with complete own Final oracle | Actual returned Top10 overlap |
|---|---:|---:|
| balance_first / balance_first | 27/27 = 100.00% | 90/90 = 100.00% |
| balance_first / pareto | 25/27 = 92.59% | 66/90 = 73.33% |
| pareto / balance_first | 25/27 = 92.59% | 86/90 = 95.56% |
| pareto / pareto | 26/27 = 96.30% | 85/90 = 94.44% |

Returned TopK overlap and shortlist retention happen to coincide here; they are computed separately because Pareto fronts can change inside a restricted pool. Each row uses its own Final oracle. These percentages are not a shared quality score and do not imply that Balance/Balance has better academic outcomes. `balance_first → balance_first` is the explicit alternative if the human review prioritizes that Final objective.

## Remaining uncertainty

- These are synthetic profiles, not a held-out population or evidence of causal improvement for students. There are no historical eligible-alternative candidate sets in the available policy summaries.
- Pareto/Pareto still loses a global Top3 plan and five Top10 positions across cases. The worst fixture is `retake_strong`; no global TopK guarantee follows from 33→50→47.
- Forty diagnostic timeouts remain censored. Dense operational reliability and candidate/SLA/memory contracts require a separate decision; a timeout is a measured failure to finish within the worker budget, not a pytest failure.
- GradeVersion 2.111/3.111 equivalence is observed only here. Benchmark 1.111 conversion is valid but uses the unknown model category; future representative/version-stratified evidence may change recommendations.
- Fixed50 isolates Final strategy; it does not assume every real shortlist resembles academic Top50. All four actual pair shortlists are additionally recorded.
- Full pytest retains one known baseline failure, classified below. No production approval is inferred from a Phase6 evidence result.

## Phase 6 Status

**PASS — corrected Phase6 evaluation/benchmark evidence is complete.**

```yaml
READY FOR HUMAN APPROVAL: YES
production_ranking_strategy: UNAPPROVED
manifest_approvals: UNAPPROVED
```

This is readiness to review the recommendations. Dense runtime and operational contracts remain uncertain; it is not production-readiness approval. Phase7 is not started.

`production_ranking_strategy`, Stage1/Final approvals and combination approval remain **UNAPPROVED**. No Phase7 work is performed.

## Technical delivery appendix

### What changed conceptually and data flow

The prior evidence mixed invalid GPA conversion with partial comparison evidence. This phase replaces every affected benchmark attempt and adds a bounded complete Stage2 diagnostic oracle. Stage1 is judged by what survives its filter, while Final is judged on one identical scored pool. This separates recall losses from ranking preferences and gives a human the actual GPA/failure/Balance cost of each choice.

```text
Synthetic snapshot/candidates + fabricated finalized history (20243)
  → existing payload/feature preparation (33 ordered features)
  → pinned Grade33 / Fail33 once per candidate
  → existing exact-credit search → complete feasible plan metrics + Balance
       ├─ Stage1 Balance / Pareto → each Top50 → compare retained IDs
       └─ offline bounded oracle: add existing 14 Plan/Peer features
            → pinned Grade47 / Fail47 → complete Stage2 metrics
                ├─ complete academic / Balance / Pareto oracles → recall@50
                ├─ identical academic Stage1 Top50 scored pool → independent Final comparison
                └─ each actual Stage1 Top50 → both Final candidates → four combinations
  → separate corrected evidence + RECOMMENDED choices for human review
```

The all-feasible Stage2 branch exists only in the offline evaluator, under its explicit diagnostic bound. Serving still has the existing ≤50 Stage2 path and its approval gate.

### File Change Map

| File (repository-relative display) | Action | Responsibility after change |
|---|---|---|
| scripts/rerun_corrected_phase6.py | ADD | Invalidate all affected observations, preserve old bytes, rerun pinned jobs, protect resume context and artifacts |
| scripts/evaluate_corrected_phase6.py | ADD | Real-model complete oracle, strict recall, identical Final pool, tradeoffs, separate version sensitivity |
| scripts/benchmark_two_stage.py | MODIFY | Remove fabricated Phase5 quality snapshot from corrected conclusions; retain explicit provenance-only exclusion |
| tests/test_corrected_phase6_rerun.py | ADD | Coverage, no stale mixing, unchanged archives, resume and source guards |
| tests/test_corrected_phase6_evaluation.py | ADD | Recall denominators, shared pools, version validation, bounded oracle, missing penalties and truthful determinism |
| tests/test_two_stage_benchmark.py | MODIFY | Prove corrected report excludes fabricated Phase5 quality |
| reports/two_stage_phase6/corrected/* | ADD | Separate corrected observations, old-byte copies, source snapshots and review evidence |
| docs/architecture/RECOMMENDATION_TWO_STAGE_IMPLEMENTATION_PLAN.md | MODIFY progress only | Record corrected Phase6 completion/evidence and remaining human approval boundary |
| graphify-out/* | UPDATE generated | AST graph refresh for new evaluation utilities |

### Function/Class Change Map

| Function | File | Type / role |
|---|---|---|
| classify_old_evidence, corrected_jobs | scripts/rerun_corrected_phase6.py | new; partition search-only/stale records and preserve each workload/deadline |
| validate_replacement, assemble_corrected_results | same | new; require exact replacement coverage and supported completed conversion, never copy old inference values |
| archive_old_evidence, protected_inventory | same | new; exact-byte archive and model/data/Production source fingerprints |
| run_corrected_benchmarks | same | new; fresh sequential workers, immutable initial baseline, pinned resume context and end-of-run verification |
| corrected_fixture, evaluate_fixture | scripts/evaluate_corrected_phase6.py | new; predefined synthetic inputs and real bounded Stage2 scoring via shared existing helpers |
| recall_evidence, _tie_recall | same | new; strict identity recall and separately labeled exact-objective sensitivity |
| compare_fixed_final, tradeoff_examples, distributions | same | new; identical pool comparison, actual plan/rank examples and separate metric distributions |
| summarize_evidence, build_report | same | new; explicit aggregation populations, performed determinism checks and source/model/version provenance |
| build_report, save_report | scripts/benchmark_two_stage.py | modified; exclude fabricated old quality snapshot and explain evidence limits |

No Production function is modified, moved or duplicated. Existing `score_course_rows`, `build_stage1_shortlist`, `_final_metrics`, plan context and rankers are reused; no legacy wrapper or dependency on `src.experiments` is added.

### Tests and what they prove

| Test group | Proves |
|---|---|
| Exact stale partition and replacement coverage | Every nonsearch attempt, including duplicate supplemental and timeout attempts, needs one fresh replacement; old metrics cannot leak into corrected aggregates |
| Supported GradeVersion and matching jobs | Unsupported/nonfinite/boolean versions fail before inference; replacement size/scenario/strategy/deadline match the old observation |
| Old-byte archive and resume context | Source reports remain byte-identical; changed models/Production source/threads are rejected before resume; the initial baseline is preserved |
| Worker source change during completion | Results cannot be published if benchmark source changed during measurement |
| Strict recall / no solution / duplicate identity / >50 rejection | Correct independent K=3/10 denominators, explicit losses, undefined empty recall, no inflation by duplicated IDs or oversized shortlist |
| Same Final pool and all four combinations | Comparisons use the same scored plans/predictions for Final choices; Stage1 and Final are independently selected |
| Missing penalty and finite metric checks | Disabled components stay missing and cannot look like ideal zero penalties; nonfinite metrics fail |
| Offline oracle bound | Complete scoring refuses an oversized diagnostic fixture before Stage2 inference |
| All determinism channels and skipped-check regressions | A failed Final, Stage1, Stage2 or unperformed check cannot produce global PASS |
| Approval regression and existing related suites | Evaluation produces no approval; existing payload, history, constraints, shortlist, Local/Backtesting behavior and dependency direction remain covered |

Focused: **65 passed** (25.57s). Related suite: **583 passed** (138.31s). Full pytest: **1119 passed, 1 failed, 6 subtests passed** (153.91s, exit 1, no skips). The suite is not green. The sole failure is **KNOWN BASELINE FAILURE**: `tests/test_train_models.py::test_tune_model_evaluates_every_candidate_fold_and_selects_mean_metric[grade-capacity_63-mae]`, because source returns `capaciy_63` while the test expects `capacity_63`. **NEW REGRESSION: 0. UNRELATED EXISTING FAILURE: 0.** Training source was not changed to repair it.

Final SHA-256 verification: **877 files under models/data and 83 Production Python sources unchanged**, with zero additions/deletions/changes. All four original Phase6 reports and archived copies retain their recorded hashes; old Phase5 comparison, quality sources and measurement snapshots also match. Manifest SHA-256 remains `d34bd605b7d1e36ee0b646b00aad3e434c74bb80feb69ef18d0ebb3cbaa9e124`. [Verification record](<D:/AI/Real projects/Academic_Advisor_Simple/reports/two_stage_phase6/corrected/verification.json>) records exact counts/results. AST-only Graphify refresh completed: **2954 nodes, 7122 edges, 167 communities**; some community labels were derived from hubs, without an LLM or semantic document re-extraction.

### Before → After and protected scope

| Area | Before | After |
|---|---|---|
| Phase6 evidence | Unsupported GradeVersion and stale inference measurements | Supported benchmark conversion; separate known-category primary/sensitivity quality evidence |
| Stage1 review | Incomplete corrected retention evidence | Strict real Stage2 Top3/Top10 recall@50, explicit losses and diversity/metric distributions |
| Final review | Insufficient corrected comparison evidence | Same scored pool with six separate metrics, TopK changes and real tradeoff examples |
| Evidence restart | Baseline could be overwritten between measurement contexts | Pinned context/threads and preserved initial baseline; changed source rejected |
| Determinism reporting | Final checks omitted from aggregate | All actually performed Stage1/Stage2/Final checks required |

**NOT CHANGED:** all Production source modules, ranking algorithms/strategy defaults, Manifest approvals, models/model bytes, experimental artifacts, training data, old Frozen bundles, old Phase5/6 reports and Local/Backtesting paths. No retraining, real student recommendation, backend connection, FastAPI/PHP, deployment, search replacement or Phase7 implementation. No Git commit was created.

### Git status

Modified tracked work: the existing plan's Implementation Progress, benchmark report builder, its regression test and generated Graphify files. New work: two offline evaluation utilities, their two test modules, and `reports/two_stage_phase6/corrected/` evidence. Graphify generated cache entries and backup files are also dirty; they are generated navigation material. `git diff -- src models data` is empty, and tracked `git diff --check` passes (only configured CRLF normalization notices). No commit/staging/push was performed.

Suggested commit: `test(recommendation): complete corrected phase 6 ranking evidence`.

Next action: human review of the two strategies and their combination, with operational limits kept explicit. **Do not start Phase7 automatically.**
