# Official Recommendation V2 migration — 2026-09-27

Recommendation V2 ready for first controlled run: **YES**. The existing
official models and both serving histories loaded successfully without
prediction. No real student recommendation, XML evaluation, large benchmark,
training, experiment or actual `--all` execution was performed. The full suite
retains one previously documented trainer-label failure, explicitly excluded
from this task. This report does not establish recommendation quality on real
students or update historical evaluation metrics.

## Official serving contract

| Requirement | Verified result |
| --- | --- |
| Official Recommendation V2 grade model | `GRADE_MODEL_PATH_V2`: `models/grade_regressor_v2.txt`; `capacity_63` |
| Official Recommendation V2 fail model | `FAIL_MODEL_PATH_V2`: `models/fail_risk_classifier_v2.txt`; `balanced_31` |
| Official metadata/categories | `MODEL_METADATA_PATH_V2`, `CATEGORY_LEVELS_PATH_V2` |
| Grade target | `final_mark` |
| Features | Exact ordered 47 `BASE_FEATURES`; numeric/categorical metadata and model headers validated |
| Expected points conversion | Finite predicted mark → clip `[0,100]` → shared `GRADE_SCALE_PATH` / `GradeScale.convert(mark, grade_version_id)` → points and grade |
| Fail scoring | Same prepared matrix as grade; finite probability → clip `[0,1]` |
| Recommendation imports `src.experiments` | **NO** |
| Uses specialty history | **NO** |
| Reads `DEGREE_POINTS_*`, V1 or experimental models | **NO** |
| Missing V2 artifact behavior | Explicit failure; no fallback |
| Single-value credits | Exact value |
| Range credits | Exact upper bound; `12–18` means exactly `18` |
| Automatic lower-credit fallback | **NO**; empty typed outputs and reason when no exact plan exists |
| Requested bounds provenance | `requested_min_credits`, `requested_max_credits`, `target_credits`, `credit_policy=upper_bound_exact` |
| Ranking | 1. projected cumulative GPA DESC; 2. expected failed credits ASC; 3. expected plan GPA DESC; 4. plan ID ASC |
| Top N default | **3**; returns one/two if only one/two exist |
| All exact-credit plans scored/saved | **YES**; exhaustive Decimal enumeration, variable course count |
| Plans below current GPA preserved | **YES**; improvement is descriptive only |
| Repeated-course grade replacement implemented | **NO**; repeat warning only |
| V1 artifacts preserved | **YES**, verified by hashes |
| Real recommendation executed | **NO** |

The cumulative formula remains `(G*C + Q)/(C+L)`, where `Q` is the sum of
course credits times expected points and `L` is proposed plan credits. The
default `C` remains `snapshot.prior_total_reg_credits`; explicit caller
overrides retain their existing precedence. Fail probability does not multiply
expected points again. Existing repeat detection and its limitations remain.

## V2 local inputs and temporal integrity

| Central constant | Input |
| --- | --- |
| `CLEAN_DEGREE_COURSE_PATH_V2` | `data/clean/degree_course_v2.parquet` |
| `CLEAN_STUDENT_COURSE_PATH_V2` | `data/clean/student_course_v2.parquet` |
| `CLEAN_STUDENT_STATUS_PATH_V2` | `data/clean/student_status_v2.parquet` |
| `CLEAN_STUDENT_DIPLOMA_PATH_V2` | `data/clean/student_diploma_v2.parquet` |

The course/status inputs are the cleaned common-student cohort used by the V2
feature pipeline. The course cleaner numbers attempts across degrees before
retaining GPA-bearing finalized attempts; the common-student filter preserves
these numbers. Recommendation therefore takes the prior retained maximum plus
one, rather than recomputing attempts from an outlier-filtered training subset.
The cleaned status table retains semester records for this cohort and supports
the same shifted student-history builder. Raw status is no longer recleaned
inside the serving adapter.

Snapshots use the exact requested semester's start fields and earlier history.
Target/future outcomes cannot alter the snapshot or frozen prefix. Supplied
snapshots retain strict key/schema validation; supplied candidate history or
outcome columns cannot override model history. Both local and XML paths use
these V2 inputs, with explicit `--allow-older-history` opt-in. XML parsing,
observed-plan and actual-GPA calculations remain unchanged; its report now
distinguishes the requested range from the exact upper-bound target.

## New immutable histories

V2 frozen history root: **`data/artifacts/history_v2/`**. Each bundle contains
only `course_history_state.pkl` and `metadata.json`. Generic history APIs retain
legacy compatibility, but the official loader requires V2 metadata and rejects
specialty bundles before unpickling. Existing `history/` bundles remain intact.

| Required request | Frozen snapshot | Finalized prefix | Rows |
| --- | --- | --- | ---: |
| `20251 <- 20243` | `as_of_20243` | V2 training outcomes `20201..20243` | 356,816 |
| `20252 <- 20251` | `as_of_20251` | V2 train plus V2 test outcomes through `20251` | 391,224 |

The latter adds **34,408** finalized `20251` outcomes. Neither snapshot includes
`20252` outcomes. Metadata records `dataset_version=V2`, feature engineering
version 2, cutoff, finalization attestation, source paths/hashes, selected-prefix
fingerprint, row counts, per-part counts and state hash. Finalization was supplied
by the task's explicit cutoff requirement; no source export alone proves the
university's historical approval timestamp. Saving is exclusive and immutable.

Commands actually executed:

```powershell
.\.venv\Scripts\python.exe -m src.features.build_frozen_history --as-of-part 20243 --finalized-through-part 20243
.\.venv\Scripts\python.exe -m src.features.build_frozen_history --as-of-part 20251 --finalized-through-part 20251
```

The default CLI selects centralized official V2 source paths and validates
feature-version metadata, including their existing schema where dataset-version
attrs are absent. Custom sources require both a `_v2` name and explicit V2 attrs.
Hashes are checked before/after reading; future rows are excluded before state
building and fingerprinting. No feature files or official metadata were rewritten.
Model training cutoff remains `20243`, recorded separately from serving cutoff,
using `course_history.initial_history_cutoff` in existing official metadata.

## Artifact hashes and preservation

| Artifact | SHA-256 |
| --- | --- |
| Official grade model | `3794be06899046e15e854129bdd3a16437f791f3e4b72a7b0a99bf656bdebf8a` |
| Official fail model | `28bd34fb756c7670157a1748a0469e2b066b711d5decb9064fd433190a96d1e2` |
| Official categories | `4fb4f3dff5f1d1bf70972ad9d02384a01f73e4689fb514937f2d70eb966982f6` |
| Official metadata | `8af46218a697eebc9873349a2a8ae9a2d8488278b56909cd5fc6b4a7ef82c83a` |
| Shared GradeScale | `557e1cb7b03b09d690d639c8d61c50e5e537360d0dec0684e6a283047111aad2` |
| V2 train features | `026faac5933709c0903dac1b0ea2ca88be71d55c1bb6f805eb265d0f4cbe204f` |
| V2 test features | `6d2c8dd0f8aa44d68812d66a21480cc328ca51beb482c0431c3d304c1a14bf05` |
| New `20243` course state | `7df5ad133f816d641d5bf89820b572010350b70270b0739e58af6b90ce4949d4` |
| New `20251` course state | `856251a1faf23e0a3197d6a1ff09f01566c3f179d0c873fc30442604cf5b895e` |

All **563 pre-existing protected files** match their before-task SHA-256 hashes:
all `data/`, all `models/`, experiment/trainer source and the feature contract,
excluding bytecode. **Zero changed or deleted files**. The only additions within
those trees are the four files in the two new V2 bundles. Raw data, V1 models,
official models, experimental winners/results, old histories and old serving
runs are unchanged. Recommendation provenance captures absolute paths and hashes
for all five consumed official/shared artifacts, metadata identity and history.

## Validation

- Focused serving/history/XML/runner/isolation suite: **157 passed, 6 subtests passed** (11.78s).
- Full `pytest -q`: **540 passed, 1 failed, 6 subtests passed** (26.22s).
- Sole failure: `tests/test_train_models.py::test_tune_model_evaluates_every_candidate_fold_and_selects_mean_metric[grade-capacity_63-mae]`: trainer returns `capaciy_63`, test expects `capacity_63`. Existing excluded issue; trainer, test expectation and artifacts were not changed to hide/fix it.
- `src.recommend_local --help`, XML evaluator `--help`, `src.main --list` and `src.main --all --dry-run`: exit 0. The dry-run executed zero pipeline steps. Recommendation, XML and benchmark remain request-specific and excluded from `--all`.
- Static AST/text audit: zero experimental imports, `DEGREE_POINTS_*`, specialty references or unsuffixed model/temporal constants in `src/recommendation/`.
- `git diff --check`: exit 0. New/modified Python files are exercised by the focused/full suites.
- Actual `AcademicPlanRecommender.load()` for both cutoffs: succeeded with 47 features and official candidate identities; no `predict()` or real recommendation was invoked.
- Independent read-only review found no material defects. Its minor XML credit-description finding was corrected.

The new/migrated tests use synthetic frames, mock models, temporary artifacts
and in-process CLI calls. They cover missing V2 with V1 present, metadata/header
incompatibility, grade-version conversion, shared matrix identity, unknown
categories, finite/clipped predictions, exact credits without fallback, variable
course count, all 20 poor plans retained, top-three/one/two outputs, deterministic
ranking and batching, cumulative/repeat rules, schema, poisoning, history
attestation/tampering/immutability and both required XML cutoff pairs. Benchmark
compatibility uses a tiny synthetic three-course request, not a real benchmark.

## Files changed and concise diff

| Files | Resulting change |
| --- | --- |
| `src/recommendation/artifacts.py` | Replace experiment/V1 loading with strict official V2 baseline loader; validate contract and capture provenance |
| `src/recommendation/engine.py` | Grade-to-points conversion; same matrix for grade/fail; base-only history; V2/credit result metadata |
| `src/recommendation/plan_generation.py` | Enumerate exact upper-bound credits while preserving requested bounds |
| `src/recommendation/plan_scoring.py`, `output.py` | Add predicted mark and grade to course outputs; retain scoring/ranking formulas |
| `src/recommendation/inputs.py` | V2 common-cohort cleaned inputs; remove raw-status recleaning |
| `src/recommendation/local_cli.py`, `benchmark.py` | Official V2/exact-credit help and benchmark source paths |
| `src/paths.py`, `src/features/frozen_history.py`, `build_frozen_history.py` | Isolated V2 root, base-only validation, attested immutable prefix construction |
| `src/evaluation/evaluate_xml_recommendations.py` | V2 inputs, explicit older-history option, exact-credit report wording |
| `src/main.py` | Official V2 request labels; preserve request exclusion |
| `tests/test_local_recommendation.py`, `test_projected_recommendation.py`, `test_frozen_history.py`, `test_main_runner.py` | Migrate serving tests to synthetic V2 and update request labels |
| `tests/recommendation_fixtures.py`, `test_recommendation_v2.py`, `test_recommendation_inputs_v2.py`, `test_frozen_history_v2.py` | New mock official fixtures and isolation/temporal/business-rule regressions |
| `tests/test_model_artifact_isolation.py` | Refresh the XML import comment; existing isolation assertions retained |
| `LOCAL_RECOMMENDATION.md`, `START_HERE.md`, `docs/MODEL_ARTIFACT_POLICY.md` | Document current official serving boundary, V2 histories and exact credits |
| `docs/superpowers/plans/2026-09-27-recommendation-v2.md`, this report | Execution checklist and fresh verification evidence |
| Four new `data/artifacts/history_v2/as_of_{20243,20251}/` files | Two base-only bundles; ignored local data, not committed |

Prior artifact-isolation report/test/plan and the user's experimental decision
report were preserved. No commit was created. No experimental model was promoted.
Work stops here before the first controlled student run, pending user review.
