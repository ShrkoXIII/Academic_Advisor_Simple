# Course-only recommendation experiment

The user-supplied 19-section specification authorizes implementation, training,
inference, bounded batch evaluation, and a final report. No promotion or official
recommendation changes are authorized. Execute inline in the current checkout:
the existing uncommitted V2 implementation and local data are the comparison
baseline. Namespace isolation and before/after hashes protect that baseline.

1. Capture hashes of official source, models, category artifacts, feature inputs,
   raw/clean inputs, immutable history, and the existing student trace.
2. Add only experiment path constants to `src/paths.py`. Derive the 33-feature
   contract from BASE_FEATURES minus exactly the named 14 features. Test matrix
   handling without plan columns, exact fractional credits, zero-credit optional
   courses, complete Top K, deterministic ties, and invalid predictions.
3. Implement isolated matrix/inference and exact exhaustive subset search. Reuse
   official input normalization, history, GradeScale, metrics, temporal fold and
   LightGBM training helpers read-only. Fit the same three configurations on the
   same two folds; choose Grade by MAE and Fail by LogLoss, independent of holdout.
4. Evaluate both fitted official models and experimental models on the same V2
   holdout. Record CV provenance (official saved CV, experimental fresh CV), full
   input hashes, model parameters, categories, cutoffs, and runtime.
5. Run student 29485.111 / degree 42.111 / 20251 / exact 18 with the supplied
   export and history through 20243. Count actual model calls/rows, retain all
   official course-in-plan scores, calculate per-course sensitivity, compare
   course sets, and independently score the experimental winner under official
   predictions to distinguish cross-model differences from ranking regret.
6. Batch: deterministic target-20251 company export cases with valid V2 snapshots,
   membership in the test cohort, 2-18 candidates, and feasible exact 18 credits.
   Use at most 12 cases; record every rejection. Exports are scenario inputs with
   unknown historical availability, not proof of counterfactual academic outcomes.
   Report requested overlap, sensitivity, signed cross-model GPA gaps, official
   rescoring regret, runtime and prediction reductions as distributions.
7. Run focused then full pytest; review correctness/isolation and verify protected
   hashes. Render the requested report with all 15 courses and Top 10 plans;
   deliver measured evidence, keep experiment isolated, stop without promotion.

Verification commands: `.venv/Scripts/python.exe -m pytest tests/test_course_only_recommendation.py -q`,
then `.venv/Scripts/python.exe -m pytest -q`, and `git diff --check`.
Experiment CLI: `.venv/Scripts/python.exe -m src.experiments.course_only_recommendation`.

Progress: specification read; current V2 paths/models verified; no production edits yet.

Progress 2: 12 focused tests passed. Training complete: Grade regularized_47,
Fail capacity_63(the existing name spelling), same finite grid and official helper implementation. Primary
and six additional feasible scenarios measured with three timing repetitions.
Pandas string aggregation converts tuple results to lists: immutable plan keys
now built outside aggregation, covered by a regression test.

Ruling: extend the existing dependency test's explicit downstream workflow
exceptions to exactly the three new course-only orchestration/inference files.
The user expressly authorized read-only imports from Recommendation and this
experiment combines recommendation/evaluation. Do not disguise imports or edit
production serving to satisfy a static test. Official trainer/config has a
pre-existing `capaciy_63` typo, also present in HEAD; leave unchanged and report
the associated full-suite failure.

Final measurements: primary 21,235→15 prediction rows, 3.048x warm runtime
speedup. Six additional cases: median speedup 1.919x, Top1 recall@1 1/6,
Top1 recall@3 3/6, Top1 recall@10 5/6. Course-set and official rescoring
comparisons preserved. Report and all requested CSV/Top3/Top10 outputs saved.
Validation: 20 focused checks pass; full suite 557 pass / 1 pre-existing
trainer candidate-name failure / 6 subtests pass. SHA-256 matches all 110
protected files. Module and direct-script CLI help succeed. Protection
preflight captures before any first run and refuses to replace old hashes.
Final independent review: complete; no Critical or Important findings. Source
and saved evidence reviewed by review_course_only. No promotion, commit, or
official edit.

Deferred P3: some explanatory prose in course_only_report.py embeds the current
six-case cohort / 80 pairs / three repetitions and measured numeric conclusions.
The delivered report matches this run; changing exported inputs or --repeats in
a future rerun requires updating that prose to avoid stale narrative. Current
tables and summary fields are generated from the measured data.
