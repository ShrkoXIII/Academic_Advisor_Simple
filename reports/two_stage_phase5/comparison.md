# Phase 5 — Two-stage candidate comparison

Status: evaluation complete; Stage 1, Final and their combinations remain **UNAPPROVED**.

Synthetic course identities/predictions and saved aggregate credit mixes; no student records or real recommendations.

## Synthetic complete-set evidence

10 synthetic candidates produce 176 exact-15-credit feasible plans. Failed cap=6; Withdrawn cap=3; shortlist cap=50; Top K=3. Predictions are fabricated, not model outputs.

The full-set Stage 2 outcomes below are diagnostic synthetic values outside serving. The engine never uses them to score beyond its shortlist.

| Stage 1 | Overlap with academic 50 | Distinct courses / mixes | Global academic Top-3 lost | Final candidate Top-3 retained (balance / Pareto) |
| --- | ---: | --- | ---: | --- |
| balance_first | 0/50 | 10 / 2 | 2 | 3/3 / 3/3 |
| pareto | 13/50 | 10 / 4 | 3 | 1/3 / 1/3 |

Stage 1 changes below are means over the selected 50 compared with the academic 50. Final changes are means over Top 3. Lower penalties express closer distance to the bands; no penalties are summed.

| Stage 1 | GPA change | Failed-credit change | Failed penalty change | Withdrawn penalty change | Total-previous penalty change | Best-component Top-3 retained (F / W / Total) |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| balance_first | -0.068000 | 0.652500 | -0.164706 | -0.005647 | -0.222286 | 2/3 / 1/3 / 2/3 |
| pareto | -0.033800 | 0.450000 | -0.092235 | -0.008471 | -0.168571 | 0/3 / 0/3 / 1/3 |

Each candidate's metrics and full identities are recorded separately in JSON.

## Final candidates on the same fixed shortlist

The fixed set is the academic Stage 1 Top-50. Its identity list is shared by both comparisons.

| Final | Academic Top-3 overlap | GPA change | Failed-credit change | Failed penalty change | Withdrawn penalty change | Total-previous penalty change |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| balance_first | 0/3 | -0.050000 | 0.187500 | 0.000000 | -0.023529 | -0.200000 |
| pareto | 2/3 | -0.005556 | 0.000000 | 0.000000 | -0.007843 | -0.066667 |

## All four cross-stage combinations

| Stage 1 → Final | Academic Top-3 overlap within shortlist | Overlap with full synthetic Final Top-3 | Top course tuples |
| --- | ---: | ---: | --- |
| balance_first → balance_first | 1/3 | 3/3 | [['F2', 'N1', 'N3', 'N4', 'N5'], ['F2', 'N1', 'N2', 'N3', 'N5'], ['F3', 'N1', 'N2', 'N4', 'N5']] |
| balance_first → pareto | 1/3 | 3/3 | [['F2', 'N1', 'N3', 'N4', 'N5'], ['F2', 'N1', 'N2', 'N3', 'N5'], ['F3', 'N1', 'N2', 'N4', 'N5']] |
| pareto → balance_first | 1/3 | 1/3 | [['F2', 'N1', 'N2', 'N3', 'N5'], ['F2', 'N1', 'N2', 'N3', 'N4'], ['F1', 'N1', 'N2', 'N3', 'N4']] |
| pareto → pareto | 1/3 | 1/3 | [['F2', 'N1', 'N2', 'N3', 'N5'], ['F2', 'N1', 'N2', 'N3', 'N4'], ['F1', 'N1', 'N2', 'N3', 'N5']] |

## Saved aggregate-policy evidence

Saved mixes: 3507 unique compositions / 95150 descriptive cases. All credit-group sums match denominators. Load 12–18 and no Other select 686 mixes / 49907 descriptive cases.

These are evaluated with explicit synthetic semester 1 and positive eligible Failed/Withdrawn alternatives. They are not the saved reference cohort (23535 cases / 6910 students): the mix file does not carry semester or eligibility/backlog.

| Component | Zero-penalty cases | Positive-penalty cases | Descriptive weighted mean | Maximum |
| --- | ---: | ---: | ---: | ---: |
| failed | 4356 | 45551 | 0.152604 | 0.764706 |
| withdrawn | 46184 | 3723 | 0.012786 | 0.823529 |
| total_previous | 6587 | 43320 | 0.147467 | 0.714286 |

Historical counts are descriptive composition weights, not ranking weights or evidence of student outcome improvement.

## Boundary and scope sensitivity

| Case | Scope applies | Active Failed / Withdrawn / Total | Failed / Withdrawn / Total distance |
| --- | --- | --- | --- |
| failed_lower_boundary | True | [True, True, True] | [0.0, 0.0, 0.0] |
| failed_upper_boundary | True | [True, True, True] | [0.0, 0.0, 0.0] |
| failed_above_upper | True | [True, True, True] | [0.014705882352941176, 0.0, 0.0] |
| summer | False | [False, False, False] | [None, None, None] |
| outside_load | False | [False, False, False] | [None, None, None] |
| zero_other | False | [False, False, False] | [None, None, None] |
| zero_new | True | [True, True, True] | [0.0, 0.0, 0.0] |
| no_repeat_eligibility | True | [False, False, False] | [None, None, None] |
| withdrawn_upper_boundary | True | [True, True, True] | [0.0, 0.0, 0.06722689075630252] |
| total_previous_upper_boundary | True | [True, True, True] | [0.023809523809523808, 0.0, 0.0] |

Zero New remains a separate identity without credit-ratio changes; zero Other disables scope. Distances outside bands remain soft, and disabled components are missing rather than ideal zero.

Mixed-scope cases in both stages and both candidates reorder [academic, outside, balanced] to [balanced, outside, academic]; the outside position stays fixed. Full results are in JSON.

## Correctness, cost and limits

Independent tests enumerate all subsets with Fraction and peel complete Pareto fronts. They compare both Stage 1 top-50 orders and all four Final top-3 selections. Complete ties and mixed scope remain covered by Phase 4 tests.

Exact decimal credit scaling and sums remain independent of Decimal context; Stage 1 aggregation uses exact Fraction products before float conversion. These narrow arithmetic fixes preserve the approved search algorithm and architecture.

Existing exhaustive/pruned search is unchanged; Pareto uses quadratic pairwise dominance. Operational cost is deferred to Phase 6.

No Phase 6 benchmark, approved strategy, model training, history/data mutation or real-student recommendation occurred.

- Synthetic predictions do not establish GPA or failure improvements for students.
- Saved aggregates lack historical eligible alternatives, their predictions, and all university policies.
- Top K is optimal only under the chosen candidate order within Stage 1 shortlist, without global guarantee.
- Strategies and their combination require independent review and approval; no automatic selection.

Source hashes and the complete synthetic metrics are in comparison.json.
