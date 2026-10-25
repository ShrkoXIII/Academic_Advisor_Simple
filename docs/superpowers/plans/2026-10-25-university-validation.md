# Unified university validation integration

The supplied specification authorizes implementation in the existing checkout and existing Streamlit entry point. Preserve all prior uncommitted search work, source snapshots, models, historic runs and Production. No training, API calls, new server or commits.

## Minimal design

- Add one `🏛️ University Validation` operating mode alongside the existing Production, Pilot and Search Benchmark modes. Six Arabic-first sections share snapshot, sample, historical observation run, recommendation source, models and experimental configuration. Default new configuration is SMART_SEARCH / 1000 / FULL_SPACE / B+C.
- Add a read-only `validation_service.py` facade over PilotService and SearchBenchmarkService. Historical observed predictions stay attached to their own run/context and do not depend on search controls. Reuse the current presentation and error/grade computations, not a prediction engine copy.
- Exact matching checks snapshot, semester, sample, model version/input fingerprints and recommendation strategy/budget/scope/target. A legacy-view toggle displays old provenance explicitly; it never renames FIRST_N. API bounds and a saved historical target are separate values. Missing selections show an explicit message, never an automatic job.
- Benchmark observations and the 30-student historical cohort remain separate datasets. Oracles are usable only with completed proofs and compatible model/input/target context. Compare canonical sets and shared-course predictions; no objective/rank changes.
- Whitelist display/export fields: sample IDs, course IDs/names, numeric results and safe run provenance. No raw identities, paths containing personal data, credentials or raw API JSON in presentation. New cross-model scoring, if invoked explicitly, reuses score_chunk/prepare_context and writes a distinct experiment without changing historic runs.
- Cohort analytics reuse existing prediction error aggregation on valid pairs and report denominators. Filters apply before metrics. Downloads contain provenance and no unnecessary personal data.

## Implementation order and ownership

1. Audit actual schemas and inventory; preserve pre-work hashes.
2. Add facade and synthetic correctness/mismatch tests (independent service domain).
3. Add six-section UI and entry-point dispatch, with shared-state and AppTests (UI domain).
4. Add plan matrices, independent historical validation, grouped search/oracle and cohort views; explicit resource-guarded actions only.
5. Add presentation flow, privacy/exports and optional saved cross-model evaluation.
6. Run focused tests and full suite; inspect actual saved examples with oracle, without oracle and blocked recommendations with independent forecasts.
7. Independent review, AST graph update, protected-file hashes, final report and demo guide.

## Review focus

No fallback to mismatched runs; no oracle claims from incomplete journals; no KPI denominator drift; zero starting GPA is a source value; missing data stays unavailable; saved actual GPA is descriptive and cumulative GPA unsupported. Rendering and downloads must never trigger inference or mutate saved data.
