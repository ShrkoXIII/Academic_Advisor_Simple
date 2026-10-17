# Historical XML paired experiment — 2026-10-14

The user supplied the detailed design and explicitly authorized implementation,
real model inference, tests and local reports. All targets were subsequently
confirmed as **20251**, with immutable V2 history **20243**. No training,
production recommendation changes, commits, history rebuilding or publication.

1. Audit actual 33/47 booster names, categories, metadata, hashes and cutoffs.
2. Use natural numeric XML order, first non-null identity, exactly ten distinct
   input-valid students. Record failed files and duplicates; retain no-plan cases.
3. Add isolated grade-only batched exhaustive search and global top-50 selection;
   rank cumulative GPA, semester GPA, canonical course IDs. Retain bounded results.
4. Build shared candidates/snapshot/history once and save hashed prepared inputs.
   Read all observed R/E registrations independently under student+degree+part.
5. Run `experiment_01_exhaustive_47`, then `experiment_02_two_stage` against the
   same saved prepared rows. Score the observed full roster in both runs.
6. Save summaries, audit manifests, per-student top3/shortlist/per-course errors
   and standalone Arabic HTML. Report nonfeasible, excluded and incomplete cases.
7. Verify synthetic exhaustive oracle, top50 membership, context, temporal
   isolation, observed GPA policy, parity, real-run invariants, full suite and
   protected file hashes; update Graphify after code is finalized.

Interfaces: `xml_two_stage_search.py` owns pure scoring/search/metrics;
`xml_two_stage_data.py` owns read-only adapters/outcome audit;
`xml_two_stage_run.py` owns CLI/artifact persistence and run verification;
`xml_two_stage_reports.py` owns offline presentation. Independent agents own
search and reports; the primary agent owns data/orchestration and integration.

The data/search/run helpers live in `src/recommendation_experiments/` to keep
serving dependencies downstream. The two required execution entry points and
the pure HTML report builder stay in `src/experiments/`. Existing dependency
direction tests remain intact.

Review focus: XML corruption and mixed identities; missing target or snapshots;
raw versus clean withdrawals/D outcomes; registered-credit denominator versus
official university GPA policy; predictions near discrete GradeScale thresholds.

Selection preflight: malformed file2; repeated identity file12; selected files
3,4,5,6,7,8,9,10,11,13. Four lack an exact18 subset and remain in both experiments.
The university's authoritative GPA/repeat/prerequisite policy is not inferred.
