# Attempt-Sum Removal Implementation Plan

> Execution: Superpowers planning/testing and independent task delegation. The user's attached specification explicitly authorizes creating and executing this isolated experiment. No production edits, commits, promotion, or extra approval stages.

**Goal:** Compare pinned official V2 47/33-feature models with fixed-configuration 44/32-feature variants, and prove an experimental history/update/inference path needs no historical attempt sum.

**Architecture:** New modules only under this directory; generated evidence under `data/evaluation/experiments/attempt_sum_removal/`, models under `models/experiments/attempt_sum_removal/`, and a new `reports/attempt_sum_removal_experiment.md`. Read original V2 datasets without rewriting them. Reuse official matrix conversion, training, metrics, GradeScale, plan GPA aggregation, history keys and temporal weights. A separate reduced history/context adapter implements the parts which unconditionally read a removed feature in production.

**Specification:** User attachment `C:/Users/ASUS/.codex/attachments/3e678393-3439-4b39-bb64-d60a19055817/Pasted text.txt`.

## Invariants

- Remove exactly `course_history_avg_attempt`, `plan_credit_weighted_avg_attempt`, `peer_credit_weighted_avg_attempt`; retain personal `attempt_number` and historical retake rate/sum.
- The reduced state has five sums, never stores or consumes a historical attempt sum, and accepts deltas without it. No fabricated placeholders or replacement features.
- Use official manifest models and archived metadata for both stages, with unchanged objectives, seeds, row order, weights, cutoffs and fixed round counts. No retuning or holdout-driven choices.
- Compare official and refitted baseline predictions; record any failure to reproduce rather than silently substituting a different baseline.
- Operational thread count may be bounded equally for both arms; record the original/effective parameters and require baseline prediction reproduction.
- Keep 2023/2024 chronological validation folds; 2025 is a previously inspected retrospective holdout, not a new blind test.
- Known Local `attempt_number` mismatch and historical error-report fold bug are out of scope. Use saved training feature values and explicit fold definitions.
- Snapshot and verify all pre-existing data/models/source/tests/reports/configuration outside the allowed experiment outputs. Never update Graphify outputs during this isolated change.

## Tasks

- [x] 1. Contract and reduced history/context implementation, failing tests first, temporal/update/fallback/missingness tests and parity against remaining official outputs.
- [x] 2. Evaluation module, failing tests first: official metric reuse, observed-plan/student aggregation, prior-GPA/zero-history cohorts, paired student bootstrap.
- [x] 3. Runner and isolation safeguards: pinned baseline verification, row/data/source hashes, fixed-config temporal fits and holdout variants, baseline reproduction, compatibility replay, timings and output metadata.
- [x] 4. Run focused tests, execute both families, inspect numerical and compatibility results, and write Arabic report A–J and machine-readable comparisons.
- [x] 5. Review experiment implementation, run required verification, recheck protected hashes and Git diff, and deliver measured verdict without production adoption.

## Evaluation decisions fixed before results

Primary families are evaluated separately. Report metric deltas as candidate minus baseline. Use 2,000 paired student-cluster bootstrap draws, seed 42, with per-metric denominators preserved. Primary non-inferiority tolerances are research assumptions, not university approval: overall Plan GPA MAE +0.01, positive prior GPA <=2 Plan GPA MAE +0.02, failure Log Loss +0.002 and Brier +0.001. Require upper 95% delta bounds within these margins to call removal comparable; require meaningful plan improvement and no primary harm for BETTER. Overlapping margins imply INCONCLUSIVE, rather than claiming equivalence from a nonsignificant difference. Very-low and other GPA slices remain explicit secondary checks.

## Review focus

No hidden average-attempt placeholder in plan context; sparse fallback uses existing key-existence semantics and global smoothing; no future outcome consumption; zero GPA is not automatically academic failure; output overwrite/resume safeguards; macro student averages and course/plan-weighted averages remain distinct; uncertainty does not certify counterfactual recommendation quality.

## Ledger

- User scope is the execution authority; skill defaults for additional approval, commits, worktrees, and external plan directories do not override the explicit isolated-experiment request.
- No replacement features, production edits, retraining of official artifacts, or publication is authorized.
- Completed fixed-round holdout and both temporal folds for full and shortlist, both arms. Pinned baseline replicas match all predictions exactly; both practical verdicts COMPARABLE.
- Full 44/32 matrix replay matches saved V2 values, categories, ordering, dtypes and missingness across all train/test rows; reduced aggregate delta matches raw update.
- Focused: 53 passed, 2 Windows symlink skips. Related: 57 passed, 6 subtests. Full suite INCOMPLETE: existing HTTP TestClient test hangs during Windows asyncio socketpair initialization; standalone faulthandler trace retained. No full-suite PASS claimed.
- Protected snapshot includes 7,198 pre-existing files, including existing uncommitted user work. Official artifacts and source unchanged. Existing Git dirtiness is not attributed to this experiment.
- Read-only independent review corrected baseline artifact sizes to pinned official file sizes. Training/prediction timing is descriptive and may be affected by concurrent verification load.
