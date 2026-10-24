# Pilot Backend Snapshots Implementation Plan

> Execute inline using `superpowers:executing-plans`; no commits or branch changes.

**Goal:** Preserve before-fix evidence and make corrected Courses captures and normal A/B/C runs use an independent after-fix snapshot.

**Architecture:** Keep the pilot root/cohort and shared model selection independent of API snapshot selection. Resolve inputs explicitly; never fall back to before-fix inputs. Copy archives exclusively and verify SHA-256 before integration.

**Spec:** User attachment `59611074-9b49-4199-a588-9d80cd73ca56/Pasted text.txt`.

**Constraints:** No network collection, training, real new batch, production contracts, algorithm/ranking changes, deletes, commits, or pushes.

## Tasks

- [x] Inventory and hash the observed legacy layout; test and execute copy-only migration; verify every source and destination.
- [x] Add shared path resolution; keep B/C bundles at their observed existing location. Restore the root cohort by verified copy if absent.
- [x] Route collector, student/course/history readers and run storage through `after_backend_fix`; archive browsing is read-only.
- [x] Keep normal dashboard execution on original API candidates; diagnostic injection requires explicit selection.
- [x] Block historical observed-plan recomputation rather than risk current-model/input rescoring. Preserve saved historical forecasts when present.
- [x] Test missing-data blocking, no overwrite, model loading, historical browsing, metadata, and a synthetic end-to-end smoke path.
- [x] Run related/full suites, graphify update, final integrity verification, independent review, and write the requested report/commands.

## Decisions and evidence

- Observed source is already `recommendation_pilot_20251/before_backend_fix/`, containing cohort, captures, models, preparations and runs; canonical root paths are absent. This predates our changes.
- Leave all originals in place. Keep model/preparation directories in that observed location and resolve them as shared dependencies; no bundle copy or relocation.
- Archive exact run bytes under the requested before-fix paths. Compatibility discovery also understands original locations.
- Before-fix snapshots are write-protected by application paths, not Windows ACL changes. No permission changes to existing data.

## Verification ledger

- Archive and final verification: 823 original files unchanged; 471 copies match; 29 complete runs accessible (21 comparison + 8 diagnostic).
- After has Student 30/30, History 15/15, Courses 0/30 intentionally. Missing inputs block all 30 until operator collection.
- Related suite 216 passed; full suite 1825 passed, 1 Windows/POSIX-specific skip, 6 subtests passed.
- Independent review: no unresolved finding after fixing cross-snapshot observed enrichment; 7 independent synthetic checks passed.
- Streamlit AppTest passed with requests blocked; graphify AST update and git diff --check passed.
- Ruling: use pytest temp storage outside `data/`; API ingestion correctly rejects SQLite under protected academic data. The first full-run command caused 25 failures, resolved by using `.pytest_cache/t`.
- Ruling: fix only the existing Courses fixture missing `registserRule`; production validation remains unchanged. All 51 focused cause checks passed.
- Final evidence: `reports/pilot_20251_backend_snapshot_migration.md` and the private `migration_audits/migration_20261022T110600_c622ec5b/` directory.
