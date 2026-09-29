# Model Artifact Isolation Audit Implementation Plan

> **For agentic workers:** Use the approved scope below. The current implementation already has isolated paths; add characterization tests and documentation without changing production behavior.

**Goal:** Make the official V2 baseline and experimental artifact boundary explicit and regression tested.

**Architecture:** Keep existing paths and persistence unchanged. Test official consumer imports and experiment destinations, then exercise the real experiment save logic with synthetic frames and a mock fit in temporary directories.

**Tech Stack:** Python, pytest, AST, pandas/Parquet, SHA-256.

**Spec:** User's attached Model Artifact Isolation Audit + Cleanup request; findings and inventory are recorded in `reports/model_artifact_isolation_audit.md`.

## Global Constraints

- Official artifacts: `grade_regressor_v2.txt`, `fail_risk_classifier_v2.txt`, `model_metadata_v2.json`, `category_levels_v2.json`.
- No training, pipeline evaluation, experiment rerun, recommendation run, artifact recreation, deletion or relocation.
- Preserve V1, unknown artifacts, immutable history, and the existing untracked winner-decision report.
- Recommendation is inspected and reported only; its migration is a separate task.
- `degree_history_mark_temporal`: KEEP EXPERIMENTAL.

## Review Focus

- Aliased and relative experiment imports must be detected in all four official packages.
- Literal experiment model paths and path constants must not bypass the dependency check.
- Experiment model, category and result saves must leave both V1 and official V2 bytes unchanged.
- Generic persistence helpers accept caller-supplied paths; the guarantee covers the configured experiment workflow, not arbitrary callers.
- Historical overview text must not identify the V1 experiment winner as official V2.

## Task 1: Inventory and protections

- [x] Scan requested extensions including ignored project artifacts, excluding dependency and Git internals.
- [x] Inspect model headers, metadata, producers, consumers and result namespaces before editing.
- [x] Capture SHA-256 for all 79 pre-existing files in models, feature artifacts, history, experiment results, Recommendation source and the winner report.

## Task 2: Regression tests

**Create:** `tests/test_model_artifact_isolation.py`.

- [x] Assert exact official and experiment paths, including preserved V1 destinations.
- [x] Detect absolute/relative/aliased imports and experiment artifact references using AST; prove the checker detects synthetic violations.
- [x] Run `load_or_train_holdout()` and `save_results()` with synthetic frames, mocked fit, actual serialization, and dummy official/V1 files; assert unchanged hashes and correct saved experiment outputs.
- [x] Run focused isolation and existing V2 I/O tests, then `.venv/Scripts/python.exe -m pytest -q`.

## Task 3: Policy and audit report

**Create:** `docs/MODEL_ARTIFACT_POLICY.md`, `reports/model_artifact_isolation_audit.md`.
**Modify:** `START_HERE.md` (current boundary notice and policy link only).

- [x] Document the four official V2 artifacts, legacy exceptions, experimental namespaces, missing-artifact failure and KEEP EXPERIMENTAL.
- [x] Record every model-related artifact's classification, producer, consumers and action; list auxiliary history states separately.
- [x] Report Recommendation's unsuffixed experiment dependency and out-of-scope provenance limitations.
- [x] Recheck protected hashes, inspect the final diff and run `git diff --check`; record fresh test results.

## Execution notes

Existing behavior is characterized rather than redesigned, as requested. No production change is needed, so a failing implementation test is not applicable. No commit or artifact movement is planned.

Verified results: 77 focused checks passed; full suite 481 passed, 1 failed,
6 subtests passed. The pre-existing candidate label `capaciy_63` fails the
existing `capacity_63` test and reproduces alone; the trainer remains unchanged.
All 79 protected files retain the same hashes. XML serving evaluation is a
documented transitive Recommendation exception, guarded explicitly in tests.
