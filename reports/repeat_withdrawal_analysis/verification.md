# Verification — 2026-10-05

The analysis ran against the current local V2 registration roster and raw course/grade sources. It performed no training, recommendation runs, dataset rebuilds, or changes to the production feature contract or Frozen History.

- Focused command: `.\.venv\Scripts\python.exe -m pytest tests/test_repeat_withdrawal_balance.py -q` — **20 passed**.
- Full command: `.\.venv\Scripts\python.exe -m pytest -q` — **612 passed, 1 failed, 6 subtests passed**.
- The failure is `tests/test_train_models.py::test_tune_model_evaluates_every_candidate_fold_and_selects_mean_metric[grade-capacity_63-mae]`, line 186. The existing implementation returns `capaciy_63`; the test expects `capacity_63`. Production training code was not changed in this task.
- An independent pandas `merge_asof` reconstruction checked **474,165 registrations**. Previous status, previous part, previous credits, and credit partition each had **zero differences**. All matched history parts were strictly earlier than their target part. See `independent_verification.json`.
- Before/after SHA-256 during the main run matched all **954 captured files**. After completing the additional diagnostics, a final comparison separately verified **951 pre-existing data, model, and source files** unchanged. The remaining three files are the newly created analysis modules, which were refined during this task. See `final_integrity.json` and `protected_final_sha256.json`.
- The user-supplied graph contains **541 nodes / 1,318 edges** and its SHA-256 remained unchanged. CLI `query` did not complete and was interrupted; the analysis used a deterministic scoped BFS directly over the existing graph. The directed `path` command reported no directed path between the roster and previous-status files. Actual graph nodes, edges, source paths, and source locations are preserved in `graph_navigation.json` and were checked against live source.
- `graphify update . --no-cluster` completed locally using AST extraction, producing **1,862 nodes / 4,430 edges** in the project's new `graphify-out/`. It used no semantic extraction or API calls.
- Nonstandard historical part-4 sensitivity recomputed **6,703 student-semesters** for the **1,172 affected students**. It changed failed-retake credits in 76 cases and withdrawn-retake credits in 2 cases, with no change in new-course credits. Middle-policy failed credits remained 3–4; its upper failed ratio moved from 23.53% to 25%. See `nonstandard_part_policy_sensitivity.json`.
- Source checks found **68 explicit F registrations** with marks 50–57 linked to grade version 3's failing range 0–49. They remain F rather than being relabeled by a mark threshold. See `grade_range_disagreements.csv`.
- All **961 registrations with 24 credits** refer to the national examination in Medicine. Raw and V2 catalog course credits agree at 24. The separate plan-credit field is 210. See `24_credit_course_source_audit.csv`.

The raw roster window was also compared with supplementary raw histories. That comparison corrected **6,731 course registrations** that would have been labeled new by the roster window alone. Student-level output files remain local and are excluded from Git by this report folder's `.gitignore`.

These checks establish arithmetic and numerical semester-cutoff integrity. They cannot establish historical course eligibility, the exact result publication time, university hard constraints, or a causal benefit of any candidate policy.
