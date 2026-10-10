# Phase 7 Result

Date: 2026-10-08. Scope: **Phase 7 only**. Human approval: **Stage1 pareto v1 -> Final pareto v1**, with a separate explicit approval of that combination. No commit was created.

## 1. Phase Status

**PASS / COMPLETE.** The approvals are persisted, actual production Core loading succeeds, focused and related tests pass, and the full suite has exactly the documented pre-existing failure. This is policy/Core activation, without approval of service performance or deployment.

Machine-readable evidence: [verification.json](verification.json). Human decision snapshot: [human_approval.json](human_approval.json). The corrected Phase 6 evidence remains unchanged and retains its historical `RECOMMENDED` labels; the new human decision is recorded here and in Manifest.

## 2. What Changed — Conceptually

Previously the model assets could load for evaluation, but production activation was permanently closed. Human approval now selects the two ranking policies independently and authorizes their combination. Manifest records those choices, versions, exact existing Balance scope/parameters, corrected-evidence hashes, rationale and limitations. The loader verifies this record alongside the existing artifact contracts.

Production activation loads the approved choices and latest valid history once. A request captures both immutable strategy references, validates them against the approval snapshot, and uses those same references throughout both stages. A mid-request replacement cannot silently change ranking under approved metadata; a later request rejects the replacement before inference.

Evaluation remains explicit and unapproved even when the asset Manifest is approved. The shared ranking candidates and algorithms have not acquired global approval. Approval belongs to the verified engine activation and its result metadata.

## 3. Data Flow After This Phase

```text
Human: Stage1 approval + Final approval + combination approval
  -> Manifest: independent name/version records, exact Balance scope, evidence hashes
  -> Validate policies + existing model/feature/category/GradeScale contracts
  -> Load four 33/47 models, GradeScale and latest valid Frozen History once

Ready student/request payloads
  -> Normalize/validate and pin approved strategies + history snapshot
  -> Apply seven history features
  -> Stage1: N candidate rows x 33 features, one prediction per candidate per model
  -> Existing exact-credit feasible-plan enumeration
  -> Pareto v1 Stage1 ranking -> at most 50 plans
  -> Add 14 plan/peer features -> course-in-plan rows x 47 features
  -> Stage2 Grade/Fail predictions -> Pareto v1 Final ranking
  -> Top K inside shortlist + APPROVED/production_core metadata + policy SHA-256
```

Input is the ready Core payload, not a new Backend transport. The output goes to its caller. The 14 context features are added only after shortlisting. `global_top_k_guaranteed=false` remains explicit.

## 4. Code Changes

**Persist independent human decisions.** File: `models/shortlist_v2/manifest.json`. Before: three `UNAPPROVED` statuses. After: three `APPROVED` statuses plus `ranking_policy.schema_version=1`, independent identities, their exact combination, Balance contract, human rationale/limitations/evidence hashes, and unresolved operational contracts. Why: make the approved policy traceable without changing model artifacts. Every other existing Manifest value remains identical; `manifest_version=1` remains the artifact contract version.

**Validate approved policy.** File: `src/recommendation/ranking_policy.py`. Functions: `balance_policy_contract()` and `validate_ranking_policy()`. Before: no approved policy contract. After: require supported strategy names/versions, three independent approvals, matching combination, exact existing fractional Balance bounds/scope, and explicit human provenance based on corrected evidence. Legacy unapproved manifests remain loadable for evaluation. Why: a bare edited approval string or incomplete record must not activate production. This helper performs no report, experiment or training I/O.

**Integrate artifact validation.** File: `src/recommendation/two_stage_artifacts.py`. Function: `validate_artifact_manifest()`. Before: reject any status change from Phase 1. After: delegate approval validation to the shared helper and retain every existing model/hash/feature/category/cutoff/provenance check. `UNAPPROVED_RANKING` moved into the shared policy module and remains import-compatible through the existing module.

**Activate from Manifest.** File: `src/recommendation/two_stage_engine.py`. Function: `TwoStagePlanRecommender.load()`. Before: always raise after loading assets. After: verify complete approval, select each policy independently from Manifest, load history once, and retain a detached approval snapshot. Why: production has an approved configuration with no request-side strategy override.

**Pin and label actual choices.** Same file. Functions: `__init__()`, `_ranking_metadata()` and `recommend_from_payloads()`. Before: evaluation metadata and repeated reads of public strategy fields. After: explicit injected/evaluation engines remain unapproved; the activated engine reports approved identities and a deterministic policy hash. Each request uses the exact captured references that were validated, and rejects wrong/missing/replaced identities before inference. Why: prevent approved metadata from describing an unapproved ranking choice.

## 5. File Change Map

Only Phase 7 changes are listed; the pre-existing Phase 6 worktree changes were preserved.

| File | Action | Responsibility after change |
|---|---|---|
| `models/shortlist_v2/manifest.json` | MODIFY | Persist three human approvals, policy contract and limitations. |
| `src/recommendation/ranking_policy.py` | ADD | Shared production-safe policy validation and exact Balance contract. |
| `src/recommendation/two_stage_artifacts.py` | MODIFY | Validate policy alongside unchanged artifact contracts. |
| `src/recommendation/two_stage_engine.py` | MODIFY | Manifest activation, request choice pinning, approved provenance. |
| `tests/test_two_stage_activation.py` | ADD | Approval rejection/activation/parity/immutability regressions. |
| `docs/architecture/RECOMMENDATION_TWO_STAGE_IMPLEMENTATION_PLAN.md` | MODIFY | Phase 7 subsection inside Implementation Progress only for this task. |
| `plan_explanation/PHASE_07_MANIFEST_POLICIES_REVALIDATION.md` | MODIFY | Explain actual Core activation, flow and unresolved operations. |
| `reports/two_stage_phase7/RESULT.md`, `verification.json` | ADD | Reviewed outcome and final machine-readable evidence. |
| `reports/two_stage_phase7/human_approval.json` | ADD | Copy of the persisted decision and its evidence provenance. |
| `reports/two_stage_phase7/manifest_before.json`, `protected_before.json`, `baseline_status.txt` | ADD | Before snapshots for artifact protection and Git scope. |
| `reports/two_stage_phase7/production_activation.json`, `protection.json`, `plan_progress_verification.json` | ADD | Actual load-only check, hashes and unchanged plan-prefix proof. |
| `reports/two_stage_phase7/focused.xml`, `related.xml`, `full.xml`, `activation.xml` | ADD | Pytest evidence; activation.xml is the earlier 24-test run, final focused evidence has all 25 new tests. |
| `graphify-out/graph.json`, `graph.html`, `GRAPH_REPORT.md`, `manifest.json`, labels/signature/cache files and new `2026-10-08/` backup | GENERATED/MODIFY/ADD | Updated AST relationships and retained graph backup/cache. |

## 6. Function/Class Change Map

| Function/Class | File | Kind | Role |
|---|---|---|---|
| `balance_policy_contract()` | `ranking_policy.py` | new, shared | Serialize exact current Balance scope/parameters. |
| `validate_ranking_policy()` | `ranking_policy.py` | new, shared | Legacy evaluation compatibility or complete approved snapshot. |
| `UNAPPROVED_RANKING` | `ranking_policy.py` / `two_stage_artifacts.py` | moved, compatibility re-export | Preserve existing imports and unapproved promotion behavior. |
| `validate_artifact_manifest()` | `two_stage_artifacts.py` | modified | Integrate policy validation without weakening asset checks. |
| `TwoStagePlanRecommender.__init__()` | `two_stage_engine.py` | modified | Default injected engines to evaluation, no implicit approval. |
| `TwoStagePlanRecommender.load()` | `two_stage_engine.py` | modified | Activate independently approved policies and load history once. |
| `TwoStagePlanRecommender._ranking_metadata()` | `two_stage_engine.py` | new | Check pinned choices and produce approved/evaluation provenance. |
| `TwoStagePlanRecommender.recommend_from_payloads()` | `two_stage_engine.py` | modified | Pin both choices throughout the existing recommendation flow. |

No ranking function moved or algorithm replaced; no new legacy wrapper was added.

## 7. Tests and What They Prove

| Test | Proves |
|---|---|
| Complete approval through actual artifact loader on temporary assets | Structured approvals are accepted with all existing artifact contracts, without report files at runtime. |
| 14 malformed/partial approval cases | Missing approval, wrong version/name/schema, inconsistent combination, changed Balance scope/bands, absent human/corrected provenance, bad evidence hash/path and invented candidate limits are rejected. |
| Approved Manifest plus tampered model bytes | Human approval cannot bypass SHA-256 protection. |
| Production versus Pareto/Pareto evaluation | Same shortlisted plans and recommendations; only approved activation gets `APPROVED/production_core`. |
| Reused engine and detached metadata/Manifest | Requests do not reload models/history; returned metadata or original mutable Manifest cannot change the retained approval snapshot. |
| Missing, wrong-stage or replaced strategy | Reject before any inference. |
| Mid-request replacement | The validated Pareto references drive both real ranking stages; the next request rejects the replacement. RED initially observed Balance/Balance under Pareto metadata; GREEN now pins both choices. |
| Independent synthetic Stage1/Final identities | Loading does not assume both policies must match; actual approved Manifest remains Pareto/Pareto only. |
| Pinned real models with known GradeVersion 2.111 | Exact production/evaluation parity on fake IDs and temporary history: 8 Stage1 rows, 200 Stage2 rows, ordered 33/47 features. |

Final results: **focused 160 passed; related 646 passed; full 1144 passed, 1 failed, 6 subtests passed; skipped 0**. **NEW REGRESSION: 0. UNRELATED EXISTING FAILURE: 0.** Full pytest is not green: the sole **KNOWN BASELINE FAILURE** is `tests/test_train_models.py::test_tune_model_evaluates_every_candidate_fold_and_selects_mean_metric[grade-capacity_63-mae]`, where the source returns `capaciy_63` and the test expects `capacity_63`. It was not changed in this phase.

Initial red tests intentionally established missing activation. One intermediate compatibility regression in an error message was fixed before the final runs. Independent read-only review found no remaining important issue after the request-pinning fix.

Actual load-only production verification: four pinned models with 33/47 feature counts and latest valid Frozen History **20251**; **no inference and no real student recommendation** in that check. SHA-256 verification after the full suite: **877 Models/Data files, 876 unchanged, only Manifest intentionally modified, no addition/deletion**; **21 Phase 6 evidence files unchanged**. All non-approval Manifest contracts remain equal. Only two existing production source modules changed and one shared policy module was added. The plan prefix before Phase 7 remained byte-identical for this update.

## 8. Before vs After

| Area | Before | After |
|---|---|---|
| Approval record | Three UNAPPROVED statuses | Three explicit APPROVED statuses and versioned policy provenance. |
| Core activation | Always rejected | Verified Manifest choices activate Pareto v1 -> Pareto v1. |
| Request choice consistency | Public fields reread during ranking | Same validated immutable references retained through both stages. |
| Provenance | Evaluation-only identity | Approved production identity + policy SHA-256; evaluation remains unapproved. |

## 9. What Was NOT Changed

No model training, model-byte changes, data changes, historical bundle rewrites, experiment artifact changes, Phase 6 evidence rewrites, new features/targets/weights, search replacement, ranking algorithm changes, Local/Backtesting behavior changes, real student recommendations, Backend/PHP/FastAPI startup, deployment or later phase.

## 10. Risks / Remaining Issues

`backend_max_candidate_count`, `recommendation_latency_sla`, and `memory_budget_per_request` remain **UNRESOLVED** in Manifest and result metadata. The human decision does not approve current exhaustive/Pareto performance, global optimality or improved student outcomes. Optimization is separate work. Current artifact byte transport must still preserve pinned hashes. The known full-suite typo remains unresolved.

Graphify AST update succeeded: **3026 nodes, 7282 edges, 173 communities**. Changed community names were derived from hubs by the tool; no LLM label or document-semantic refresh was run. This is the prescribed AST update, not a claim of newly extracted documentation semantics.

## 11. Git Status

Phase 7 changes are uncommitted and unstaged. Existing Phase 6 scripts/tests/reports and graph dirtiness predate this task and were preserved; do not include them accidentally in a Phase 7 commit. `baseline_status.txt` records the initial state. No commit, push or deployment occurred.

## 12. Suggested Commit

`feat(recommendation): activate approved pareto v1 policies from manifest`

Stage only Phase 7 source/tests/Manifest/documentation/evidence and relevant graph updates. The shared plan and graph already contained earlier changes, so review their scope when preparing a commit.

## 13. Next Phase

There is no Phase 8 in the approved seven-step plan. Work stops here. Core policy activation is complete; service deployment is not cleared while the three operational contracts remain unresolved. Search/ranking optimization and operational decisions require a separate explicit task.
