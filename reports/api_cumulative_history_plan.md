# API configuration and cumulative history — implementation ledger

Approved scope: user specification dated 2026-10-11 in this conversation. Current repository; preserve existing uncommitted capacity-name fix. No training, model/feature/ranking changes, real-student recommendations, production history migration, or Git commit.

Tasks:

1. Optional configured HTTP client; PHP-push default unchanged. Synthetic security/configuration tests.
2. Authoritative GPA denominator timing and official course attempts/status. Synthetic temporal and conflict tests; audit training semantics.
3. Separate cumulative storage, validated 20251 migration, serialized durable modes, commit/activation separation, exact snapshots and rollback. Reuse Phase 3 core; synthetic aggregate parity.
4. Authenticated PHP administrative transport, finalization credential, dependency status and serving pointer integration. Preserve existing POST recommendation contract.
5. Architecture, environment/PHP contracts, focused/related/full checks, protected SHA-256 comparison, graphify AST update and final review.

Pre-flight: core store consumes existing FrozenHistoryManager publication; HTTP layer consumes store operations and existing ApiError diagnostics. No need to change TwoStagePlanRecommender type checks: use a FrozenHistoryManager-compatible serving proxy.

Ruling: work in the current repository and do not create commits, as explicitly requested; keep this ledger and all verification evidence instead of a commit-based skill ledger. Cost if wrong: later integration must review the uncommitted diff explicitly.
Ruling: initialize/migrate real cumulative history only through the new authenticated workflow with an approved source fingerprint and confirmation. Implement and test the procedure without activating a real bundle in this task. Cost if wrong: incorrect provenance could contaminate serving; exact source verification and compatibility gates remain mandatory.

Tasks 1–4: complete. Client 19, academic 41, admin 12, synthetic HTTP integration 6, history 29: final focused 107 PASS. RED was observed before implementation and review fixes; no actual university fetch or real history migration.
Review: an independent reviewer with fresh context identified four Important issues (pre-migration worker refresh, serving never-activated versions, baseline control failure recovery, and skipped-semester validation). All were reproduced, fixed and re-reviewed with no remaining Critical/Important finding.
Task 5: complete. Architecture, contracts, semantic audit and AST graph updated. Final related: 503 PASS plus 6 subtests; final full suite: 1369 PASS plus 6 subtests. Protected SHA-256: 1230 unchanged, no additions/deletions; no real incremental directory. HEAD unchanged, no commit. CLI help passed. Operational university dependencies are documented as PARTIAL/BLOCKED in the final report.
