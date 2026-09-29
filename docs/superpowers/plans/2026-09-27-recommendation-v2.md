# Official Recommendation V2 Implementation Plan

**Goal:** Serve only the existing 47-feature official V2 grade/fail baseline, with grade-to-points conversion and exact upper-bound credits.

**Architecture:** Reuse `prepare_model_matrix`, `GradeScale` and base `CourseHistoryState`. Keep exhaustive Decimal enumeration, additive GPA projection, four-key ranking, all feasible plans and top three. Isolate finalized history in `history_v2`; retain every old model, experiment result, history bundle and recommendation run.

**Spec:** User's attached Recommendation V2 request and mandatory `docs/MODEL_ARTIFACT_POLICY.md`; prior state in `reports/model_artifact_isolation_audit.md`.

## Constraints and review focus

- No trainer, feature-contract, experiment logic or model-artifact changes; preserve `capaciy_63` as a separate issue.
- No real student Recommendation, XML evaluation, heavy benchmark, training or `--all` execution.
- Official inputs fail if missing; never fall back to V1 or experiment artifacts.
- A requested range preserves its lower/upper provenance but enumerates only the upper bound; no lower-credit fallback.
- V2 history must attest dataset version and source hashes, reject specialty state, validate hashes and remain immutable.
- Current/future outcomes cannot alter start-of-semester snapshots or selected history prefixes.
- Imports remain free of model loading; new tests and migrated integrations use synthetic data.

## Tasks

- [x] **Core:** Test first, then replace the artifact loader and constructor with grade/fail/categories/GradeScale/base history; validate metadata/model feature order and target; capture all five artifact paths/hashes. Convert finite grade predictions to points/grade; reuse the exact matrix for failure prediction; update course schema.
- [x] **History:** Add `FROZEN_HISTORY_DIR_V2`; keep generic history APIs backward compatible while requiring V2 provenance for official use. Test base-only immutable bundles and source/cutoff integrity. Create only new `20243` and `20251` snapshots from the existing finalized V2 feature sources after synthetic tests pass.
- [x] **Inputs/XML:** Use common-cohort cleaned V2 status/course/catalog/diploma tables; preserve snapshot and XML comparison semantics, add explicit older-history opt-in.
- [x] **Business rules/adapters:** Enumerate exact upper-bound credits, record requested bounds and no-match reason; update local CLI help, benchmark paths and request-specific runner labels.
- [x] **Tests:** Migrate existing serving integrations to synthetic official fixtures; test artifact isolation, mark conversion across grading versions, failure clipping, exact credits/no fallback, variable course count, all poor plans retained, top three, ranking, cumulative formula, repeats, output schema and no-leakage.
- [x] **Verification/report:** Run focused tests, complete pytest suite, CLI help/list/dry-run and static audits; compare all 563 protected pre-existing data/model/trainer/experiment/feature-contract hashes. Record the known trainer label test separately. Write a final migration report and concise diff; stop before any real recommendation run.

The supplied specification authorizes this execution. Independent history, input/XML and existing-test work is delegated without overlapping file ownership; the core implementation and final integration remain in this chat. No commit is planned.
