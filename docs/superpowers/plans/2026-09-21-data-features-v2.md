# Data and features V2 structural migration

**Goal:** Move the user's current data/features code without changing cleaning, feature semantics, or temporal splits, and isolate new artifacts with `versioned_path()`.

**Execution:** Inline, as authorized by the user's detailed implementation request. Preserve local edits; do not commit, reset, or overwrite any existing data. The binding specification is the 17-section user request in this task.

**Architecture:** Absolute `src.data.*` / `src.features.*` imports. Original path constants remain unchanged; moved pipeline stages use explicit `_V2` constants derived from originals. Immutable history directories retain their existing cutoff versioning.

**Tech stack:** Python project venv, pandas, Parquet, pytest.

## Tasks

- [x] Snapshot current source and SHA-256 hashes of every existing data/model artifact; run baseline tests.
- [x] Add regression tests for versioned paths, isolated artifact constants, roster duplicate rejection, and V2 chaining; observe failures first.
- [x] Move 10 data modules and 5 feature modules; create package initializers; update repository imports and active CLI references.
- [x] Add `versioned_path(path, version="v2")` and constants for all 16 stage outputs plus category levels; use V2 inputs and outputs throughout moved entrypoints.
- [x] Add only the two requested roster `many_to_one` validations; preserve all other logic.
- [x] Correct the existing test fixture typo `st art_part_id` to `start_part_id`, without changing production cleaning.
- [x] Run data, feature, full suites, source compile/import checks, and stale-import scans.
- [x] Run available real-data V2 stages without overwriting files. Compare existing V1 outputs and freshly executed pre-move code where possible. Record blocked stages rather than bypassing business rules.
- [x] Verify all original hashes unchanged; write comparison results and final report.

## Review focus

- Absolute imports must work in a fresh interpreter from the project root, including experiment/recommendation consumers.
- Existing frozen-history and course-state serialization must remain readable after module relocation.
- Raw inputs remain shared, including the intentional full raw status history in feature construction.
- No training/evaluation execution or path migration outside the requested sections.
- Existing V1 outputs may be stale relative to the user's local cleaning edits; distinguish that from relocation regressions.

## Evidence and rulings

- Baseline: 250 passed, 30 failed. 28 failures originate in a misspelled test fixture column; two integration failures are `Invalid part_id 20214` in existing raw status data.
- The follow-up policy now authorizes excluding missing `course_id`/`part_id` rows and semester-4 status rows in cleaning only; raw inputs remain immutable and `academic_calendar` remains strict.
- Snapshot: `reports/data_features_v2_20260921/source_before.zip`; original artifact manifest covers 461 files.

## Completion evidence

Cleaning policy resolution complete: one course row with both critical keys missing and eight semester-4 status rows are excluded in cleaning. Data/cleaning tests: 116 passed; features: 26 passed; full suite: 317 passed. All nine V2 stages completed and 16 V2 artifacts were generated. 38 source imports and all compile checks passed; raw and V1 artifact hashes remain unchanged. Detailed evidence: reports/data_features_v2_20260921/report.md.
