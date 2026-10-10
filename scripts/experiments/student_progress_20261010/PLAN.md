# Student progress audit and ablation plan

Scope: the attached eight-phase request, 2026-10-10. All production sources, existing datasets, model manifests, selected models and frozen histories are protected. No commit or feature promotion.

- [x] Read-only lineage/temporal/backend audit with exact source references.
- [x] Execute descriptive statistics and empirical source identities; pseudonymize examples.
- [x] Test experimental safeguards before training: nine feature subsets, inner/outer temporal isolation, plan aggregation, zero-credit handling and signatures.
- [x] Fit A/B/C/D/E and four leave-one-out variants using existing V2 tables. For each outer 2023/2024 fold, baseline-only inner training validation selects configurations from the existing three-candidate grid; freeze those parameters and tree counts across variants. Categories and training weights are identical. No 2025 target loading or evaluation.
- [x] Evaluate official 47 and stage-1 33 grade/fail models, direct points research, and selected degree-history grade profile. Paired metrics, Plan GPA, student-cluster intervals, degree/progress groups, gain and validation permutation importance.
- [x] Run isolated fixed-candidate ranking sensitivity, with explicit counterfactual-quality limitation.
- [x] Create reports/student_progress_feature_ablation.md with decision and exact adoption follow-ups.
- [x] Run focused/related/full tests, graphify AST update, protected SHA-256 comparison, and independent review. Existing capacity_63/capaciy_63 failure is not part of this change.

Shared interfaces: audit evidence and training results feed the final report; all workers own separate files. Descriptive evidence cannot select experimental hyperparameters. Outer validation cannot select an inner configuration. Existing official configurations selected on 2023/2024 are unsuitable for an unbiased assessment of those same years, so the experiment uses nested baseline-only selection instead. Official artifact gain is descriptive only.

Review focus: holdout target isolation; cache feature/signature mismatch; zero-credit plan denominators; dropped fields still retained in ratio and GPA policies; temporal rows/history unchanged; denominator semantics and DB mutability remain explicitly unverified.

Completed: 144 fits (36 inner + 108 outer), all nine configurations; 24 fixed candidate pools; complete-plan permutation; matched-registration coverage/metrics; 1,000-draw student paired intervals. Audit PARTIAL because authoritative SQL/snapshot/GPA definitions are unavailable; experiment COMPLETE; decision KEEP_ALL pending independently approved simplification.

Verification: related 110 passed; combined full 1,185 passed, one known baseline failure, six subtests; final focused 22 passed after cache-context hardening. All 108 models authenticated; 1,159 protected files unchanged. Numerical fits used the archived executed runner; later cache/completion/namespace/permutation safeguards were tested separately and did not rerun or migrate original results. Three independent audit/review tasks completed. Temporary pytest fixture copies were cleaned after logging; graphify was refreshed. No production feature change or commit.
