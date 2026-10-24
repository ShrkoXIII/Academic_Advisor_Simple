# Unified Streamlit Pilot Implementation Plan

> Execute with `superpowers:subagent-driven-development`; user forbids commits, branch switches, live collection, real 30-student runs and retraining.

**Goal:** The current Streamlit website orchestrates production and offline Pilot comparisons without a Pilot server.

**Spec:** User's complete Unified Streamlit Pilot Interface request in this conversation.

**Architecture:** Preserve Production block and migration paths. Extend the existing engine/observer/runner with optional selected models (default remains ABC), and an optional post-score enrichment callback. A thin service uses a stable single-worker runner, saves observed display data only after scoring, and loads compact saved projections without rescoring. A separate Streamlit presentation module owns controls/tables/cards.

## Contracts

- `PilotEngine.evaluate_student(..., models=None)`: default ABC, selected-only scoring when supplied, shared plan generation/ranking unchanged; real stage timers where available.
- `ObservedPlanPredictor.predict/predict_many(..., models=None)`: same backward-compatible selection; no unselected scoring; cache provenance explicit.
- `ComparisonRunner(..., result_enricher=None, reuse_engine=False, max_retained_jobs=64)`; `start/run_sync(..., models=None, include_reserve=False)`; callback `(result, student, engine, selected_models) -> result` runs after scoring. Manifest records selection. Progress adds bounded per-student statuses.
- `read_students(root, include_reserve=False)` remains primary-only by default.
- `RunStore.load_compact(run_id)` uses immutable top-three `presentation_results.json` for new runs; legacy reads project in memory only. Never rewrite old runs or infer on load.
- `PilotService(root=PILOT_ROOT, ...)`: `cohort(include_reserve=False)`, `completeness(snapshot_id='after_backend_fix', include_reserve=False)`, `preview(sample_id, snapshot_id=...)`, `start(sample_ids, models=('B','C'), snapshot_id=..., target_credits=18, max_plans=200, include_reserve=False) -> run_id`, `progress(run_id)`, `list_runs()`, `load_run(run_id, family='comparison')`, `presentation(saved_run, sample_id)`.
- `presentation` returns `sample_id,snapshot_id,student_summary,summary_rows,plans_by_model,actual_course_rows,actual_summary,timing_rows,warnings`; missing values stay None with explicit reasons. Selected model defaults come from manifest, not current controls when browsing old runs.
- `completeness` returns `snapshot_id,student_saved,courses_saved,history_saved,history_total,primary_count,ready_sample_ids,blocked,records`; blocked rows have `sample_id,reason,field`. Uses snapshot implementation and verified metadata; no network.
- `list_runs` labels family (`comparison` or `actual_candidate_injection`) and snapshot. New normal runs never inject actual courses. Before browsing is stored-results-only.

## Task ownership

1. Root: integrity inventory, selected engine/observed execution, runner hooks/projections/progress, cohort optional reserve; tests proving parity and no unselected execution.
2. Service implementer: `tools/academic_advisor_streamlit/pilot_service.py`, presentation helpers as needed, `actual_metrics.py` optional models argument if needed, focused service/metric tests. No modifications to root-owned engine/runner/observer/UI files.
3. UI implementer: `tools/academic_advisor_streamlit/pilot_ui.py`, mode-switch integration in `streamlit_app.py`, Streamlit AppTest tests. Preserve Production block byte-for-byte except indentation under mode branch; existing collector/history unchanged.
4. Independent task/final review, related/full tests, integrity verification, graphify AST update, requested Arabic report and launch command. No real new evaluation.

## Review focus and rulings

| Shared boundary | Resolution |
|---|---|
| Service consumes new runner kwargs | Root implements exact contract; service tests use stub engine until ready |
| UI consumes service presentation | Keys above are stable; agents may coordinate additions, not change scoring |
| Metrics consume observed labels | Only callback after candidate/actual-plan scoring receives outcomes; label isolation tests |
| Old run loading | Never enrich/recompute on browsing; unavailable historic fields stay labelled unavailable |
| Resource lifetime | Single worker, reused models, bounded job caches, no full datasets in session_state/cache_data |
| Repository state | Stay on `new_branch`; migration and uncommitted work from earlier turns preserved |
| Temp test paths | Use `.pytest_cache/<unique>` outside `data/`, and escalate only local TestClient if Windows sandbox blocks socketpair |

## Ledger

- [x] Initial archive/model/snapshot/run fingerprint inventory: 1468 files / 7,199,939,413 bytes.
- [x] Selective scoring and observer parity tests, then core implementation.
- [x] Service and presentation tests/implementation, independent scenario/retirement fixes verified.
- [x] Streamlit integration and 20 passing AppTests; actual cohort layout verified without inference/HTTP.
- [x] Independent review, full final suite: 1878 passed, 1 skipped, 6 subtests passed; protected hashes identical and no added protected files/runs.
- [x] Graphify AST update and `reports/unified_streamlit_pilot_integration.md`.
