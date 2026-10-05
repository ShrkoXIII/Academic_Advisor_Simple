# Isolated attempt-number experiment plan

**Goal:** Answer the user's 22-part specification using unchanged V2 inputs, production mechanics and paired evidence.

**Architecture:** Add research-only modules under `src/experiments/attempt_number_*`. All model and row-level outputs stay under separate `models/experiments/attempt_number` and `data/evaluation/experiments/attempt_number` namespaces. Reuse production functions by import without mutation or monkeypatching.

**Execution:** Native, continuously in this session, as authorized by the request. No commits, promotion, rebuilds or production edits. The user's explicit experiment specification overrides generic plan approval workflows.

**Spec:** Current user request, sections 1–22.

## Constraints and decisions fixed before fitting

- A = 47 official columns; B replaces only `attempt_number` in its position with `is_repeat`; C removes only that column (46).
- Same V2 parquet rows, category handling, targets, training weights and seed 42.
- Freeze the selected official metadata parameters and rounds: grade 114, fail 112. Use these for every variant and temporal fold; no variant tuning or early stopping. This deliberately controls tree budget as well as hyperparameters. Original production selection used early stopping and mean fold iterations; selection is already finalized using pre-2025 data.
- Official folds: through 20223 → 20231–20233; through 20233 → 20241–20243. Final train through 20243; holdout 20251/20252 with existing sequential history.
- No D: fixed primary comparison A/B/C; no feature decisions or new trials based on holdout outcomes.
- Descriptive quality margins, not user-approved product tolerances: absolute increase <=0.10 mark MAE, <=0.02 points MAE, <=0.005 fail log loss. Show 95% paired student-cluster bootstrap bounds (1000 draws, seed 42); no automatic equivalence or deployment claim.
- Recommendation sample: deterministic valid existing JSON exports with repeat candidates and <=18 candidates, exact 18 credits; include available 3+ candidates before 2-only cases. Selection uses inputs only. Same feasible plans, frozen base history, context recomputation and production ranking. Report changed rankings as sensitivity, not realized quality or causal regret.
- Hash all existing production source, models and input/history files before/after. Never overwrite existing experiment results silently.

## Review focus

Missing/invalid attempts must fail rather than become first attempts; keep row order and categorical dtypes; deny stale feature tables and overlapping temporal splits; compute uncertainty across students rather than independent rows; recommendation wrappers must leave every other feature and ranking function unchanged.

## Tasks

- [x] Test transformation immutability, exact feature order, invalid values, paired row fingerprints and student-cluster bootstrap.
- [x] Implement isolated preparation, protection, training and diagnostic artifacts; verify fresh A reproduces official predictions (maximum prediction difference 0.0 for both).
- [x] Run fixed A/B/C models and temporal folds; write distribution, outcomes, overlap, calibration, prediction differences and uncertainty.
- [x] Compare real exported repeat recommendation cases with identical production functions and frozen history (four cases, 4599 feasible exact18 plans).
- [x] Write `reports/attempt_number_feature_analysis.md` covering A–K, numeric summary and limitations; run focused/full suites and verify 799 protected hashes.

## Execution rulings

- Added original production early-stopping CV (max 900, patience75) as a second diagnostic view, using the same frozen candidates. No holdout-driven choices or final-round changes. The final ablation retains official 114/112 rounds.
- Put the recommendation workflow and entry point in `scripts/experiments/`, because the architectural test prohibits new upstream imports of serving. Kept production modules and the architectural test unchanged.
- Vectorized the prior saved-attempt audit after the per-key Python transform was slow; its semantics remain cumulative max followed by a group shift.
- Full suite: 592 passed, 1 pre-existing `capaciy_63` vs `capacity_63` failure, 6 subtests passed. Focused suite: 11 passed.
- Decision: INCONCLUSIVE for replacement without meaningful product loss; keep production unchanged.
