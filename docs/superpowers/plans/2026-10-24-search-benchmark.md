# Search benchmark implementation ledger

The user supplied the full specification and ordered execution, including a bounded local run. Implement in the existing checkout, without commits, training, production changes, or actual-course injection. This document records implementation choices; the supplied specification remains authoritative.

## Design

- Resolve exact target from saved Courses `registserRule` credit bounds. A confirmed registration-policy load profile intersects its corresponding bounds. Unconfirmed profile fields and course counts are evidence, not invented credit caps. Missing/conflicting applicable bounds block automatic execution. Manual diagnostic targets are explicit and cannot exceed known API bounds.
- Reuse Pilot `_candidates`, `build_snapshot`, B/C `predict_course_rows`, and `_attach_scores`. Canonical identities use sorted course sets; deterministic DFS ordinal remains the original final tie break.
- A counted exact Decimal subset space supports include-first DFS ranks, reproducible rank sampling without replacement, and a heuristic additive best-first discovery score. Heuristic course history is strictly prior and common to both models, with no extra model inference. It guides discovery only. No uniformity claim beyond the exact enforced subset constraints.
- Fixed-pool selection uses only the persisted first 2000 feasible identities. Global selection uses the entire implicit space. Neither reads oracle scores. Score selected complete plans afresh in bounded chunks for each experiment; count every model evaluation.
- Exhaustive scoring uses the same DFS identities and scorer, SQLite compact score summaries, atomic per-chunk checkpoints, input/config fingerprints, and a completed-count proof. Time, count, storage and state guards produce `EXHAUSTIVE_INCOMPLETE`. Top 3 retain course details. Resume validates fingerprints and resumes after committed chunks.
- Separate Streamlit experimental controls and progress, button-only execution and saved-run browsing. Keep the Production tab and collection unchanged.

## Tasks and verification

- [x] API targets: tests first for 12-credit, exact, missing/conflicting bounds, profile precedence, explicit override, and per-student batch/default reset. Modify only Pilot code and UI.
- [x] Space/selection: tests first for DFS parity, Decimal/zero-credit uniqueness, common constraints, budgets 200/1000/2000, reproducibility, pool containment and synthetic optimum beyond DFS 2000.
- [x] Offline runner/oracle: tests first for original scorer/ranking parity, plan-dependent recomputation, interrupted/resumed integrity, count proof and oracle metrics with ties.
- [x] Unified UI: AppTest coverage for explicit execution, rerender safety, separate progress, before/after isolation and saved results.
- [x] Targeted and full regression, AST graph update, protected-artifact hashes.
- [x] Inventory 30 saved students; choose 3-5 objectively by GPA, candidate count and exact space size; run bounded benchmark and resource-limited oracles only.
- [x] Write Arabic evidence report, CSV/JSON results and integrity manifest; declare PASS/PARTIAL/BLOCKED from actual evidence.

## Review focus

Unknown policy evidence must stay visible; huge integer counts must not allocate the universe; zero-credit optional courses must preserve DFS semantics; resume must reject source/model/code drift and corrupt chunks; failed model jobs must not produce completed oracle claims.

## Execution rulings

- The explicit implementation request authorizes proceeding through the supplied scope without a separate design approval. No Git commits.
- Independent implementation domains may be delegated using the `dispatching-parallel-agents` skill; source edits must have disjoint ownership.
- Resource defaults will be conservative and recorded. Student selection is based on source/snapshot features and counts, never oracle rankings or actual registrations.

## Final evidence

- Completed run: `benchmark_20261024T120117_4a7c2fc8`, 5 students, 190 experiment rows, 10 completed B/C oracles, 215086 independent plan/model evaluations.
- Final focused suite: 150 passed. Full suite: 1968 passed, 1 skipped, 6 subtests passed. One Starlette/httpx deprecation warning.
- Protected-file audit: 1421 files unchanged; real B/C predictions and all plan score fields equal to original Pilot on 200 plans/model.
- Read-only independent review fixed stale resume seals; report guard and existing C peer-feature wording corrected.
- Implementation acceptance: PASS for the specified bounded local validation. Overall algorithm choice across 30 students: INCONCLUSIVE. No commits or next all-student exhaustive job.
