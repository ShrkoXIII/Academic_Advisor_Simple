# Pilot 20251 implementation plan

Follow-up (2026-10-19): audit true BLOCKED causes; separate prediction, provisional registration and cumulative projection states; simplify this existing UI to one searchable student picker with a separate batch section; complete isolated B/C training with audited row quarantine, full registration-roster context, historical validation and exact bundle provenance. Retire invalid research versions without overwriting earlier files. The initial phase record below is historical.

The user-supplied specification is the design brief and authorizes sequential execution. This is an isolated local experiment, with new code under `tools/recommendation_pilot_20251/`, synthetic tests under `tests/test_pilot_20251_*.py`, and private generated artifacts under the ignored `data/evaluation/recommendation_pilot_20251/experiments/` directory. No production source, model, archived input, history commit, activation, or remote university request is permitted.

1. Phase 1: test then implement a strict five-field Student API adapter and local input identity/hash validation. Values come directly from the five approved uppercase fields; no temporal correction is permitted. Record the unresolved timing limitation.
2. Phase 2: validate and isolate the fifteen university history responses; aggregate sums with prior-only temporal weighting, smoothing and fallback 1/2/6. Preserve the original A bundle.
3. Phase 3: audit individual historical data, build compatible isolated B/C contracts and train only where semantics and provenance support it. Evaluate feature additions individually. Unsupported features are `NOT_AVAILABLE`; incompatible experiments are `BLOCKED`.
4. Phase 4: reuse existing candidate/plan primitives, bind one candidate set and deterministic exact-credit plan set to every experiment. Explicit unsupported essential registration rules block validity.
5. Phase 5: score identical plans, preserve A predictions/ranking, add measured C plan-risk assessment, and keep cumulative improvement unavailable where denominator/repeat policy is unproven.
6. Phase 6: implement an Arabic RTL HTML/CSS/JS dashboard with a loopback FastAPI backend, CSV multi-select, progress, saved runs, course/plan comparisons and explicit blocked states.
7. Phase 7: immutable unique run directories containing manifest, student results, plan/course CSVs and diagnostics, with input/model/contract/history hashes and reproducible settings.
8. Phase 8: run focused tests at each gate, then the full suite and browser workflow, verify protected hashes, update graphify, write a runnable README and actual findings report.

Shared interfaces will be fixed after inspecting current schemas. Tests use synthetic records; student data stays in ignored local outputs. Existing workspace changes belong to the user and must be preserved. No automatic commit.

Review focus: missing/nonfinite five-field values; identity/hash mismatches; future history/training rows; unknown registration semantics; GPA denominator and replacement ambiguity; unavailable per-student peer evidence; partial batch failure; immutable saved-run paths; identical plan fingerprints across A/B/C.
