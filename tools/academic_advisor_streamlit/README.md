# Academic Advisor — Streamlit local test console

A small standalone test interface to **the existing** FastAPI service. It does not import/retrain models or alter your Python engine.

## 1. Place files in the repository

Copy the whole `academic_advisor_streamlit/` directory to:

```text
Academic_Advisor_Simple/
├── .env                          # secret config, do NOT commit
├── src/api/                      # existing FastAPI app (unchanged)
└── tools/academic_advisor_streamlit/
    ├── streamlit_app.py
    ├── ui_client.py
    ├── requirements-streamlit.txt
    ├── integration_context.example.json
    └── tests/
```

Copy `.env.example` to **the repository root** as `.env` and replace the placeholder URL, token and query-parameter names. Do not overwrite an existing `.env`; merge the new `ADVISOR_UI_*` keys into it. Never commit `.env`, private JSON, user records or credentials.

Make sure the FastAPI process also has its **own** `ADVISOR_API_KEY` or `ADVISOR_SERVICE_KEYS` configured, matching `ADVISOR_UI_SERVICE_KEY`. The history administrative API uses `ADVISOR_ADMIN_API_KEY`, matching `ADVISOR_UI_ADMIN_KEY`.

**Upstream URL query parameters are configured in `.env`.** The defaults for Student are `studentId` and `semesterId`, matching the project's optional `BackendClient`; Courses query keys are examples only and must match PHP's actual contract.

## 2. Install + start (PowerShell)

From your repository root, in your existing virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r tools/academic_advisor_streamlit/requirements-streamlit.txt
```

Start the existing FastAPI app **in a separate terminal**, using the startup command already documented in your `src/api/README.md`:

```powershell
python -m uvicorn src.api.app:create_app --factory --host 127.0.0.1 --port 8000 --env-file .env
```

`--env-file .env` is important: the FastAPI process must receive the service/admin credentials from the same environment configuration. If your installation already loads `.env` using another mechanism, keep that repo convention.

Then start the Streamlit GUI:

```powershell
python -m streamlit run tools/academic_advisor_streamlit/streamlit_app.py
```

You can open `http://localhost:8501` in a browser. Do not expose this developer console on a public network: the JSON panel contains student PII.

## 3. Recommendation (normal use)

1. Enter `student_id` and the target semester `part_id`.
2. Press **1 · Fetch JSON only** to inspect the raw two university responses, **or** **2 · Fetch + submit + recommend** to execute the model.
3. The GUI gets Student API first, **reads `DEGREE_ID`** from `data.studentDegreeInfo`, then fetches Courses API using that degree ID. You need not type `degree_id`.
4. `history_as_of_part` is derived using the project's term numbering: for example `20262 → 20261`, `20261 → 20253`.
5. With the Run button, the GUI generates a fresh `request_id` and sends two **independent FastAPI HTTP requests**:
   - `POST /api/v1/recommendation-inputs/student`: includes the student response, source context and recommendation settings.
   - `POST /api/v1/recommendation-inputs/courses`: includes the courses response and course source context.
6. The second submission triggers the **existing** `ApiService.recommend()`. Inspect both JSON HTTP results. A saved `request_id` can be queried using `GET /api/v1/recommendation-requests/{request_id}`.

The GUI keeps only transient results in the active Streamlit session; the existing FastAPI RequestStore owns durable correlation and retention.

### Academic evidence is not invented

Your historical student API samples **do not include all required academic provenance**. Your current validators require additional fields such as diploma aliases, official registered-credit timing, previous-course statuses and registration policies. Missing `integration_context` / required direct source fields may trigger `INVALID_INPUTS`. This is intentional. A developer must supply **real** university-attested evidence via a JSON file:

```json
{
  "student": {
    "student_values": {},
    "total_reg_credits_source": null
  },
  "courses": {
    "previous_course_statuses": {},
    "registration_policy": null
  }
}
```

The above illustrates the shape **but is not valid academic evidence**. Do not fill values by guessing from missing history. Set `ADVISOR_UI_INTEGRATION_CONTEXT_FILE` in `.env` to a path containing real source-attested data, or arrange for PHP to expose it in an authorized source. The file is deliberately not populated automatically from ambiguous or future-semester values. Existing API validators remain authoritative.

`target_credits` defaults to **18 only as a UI input choice**, not an academic policy override. The service still enforces actual registration bounds and requirement group policies.

## 4. Frozen History — one `part_id` to fetch

Switch to the **Frozen History** tab and enter only the completed semester's `part_id` (e.g. `20261`). The GUI calls the configured PHP history endpoint with the configured GET query or POST JSON **once**, and expects:

```json
{
  "part_id": 20261,
  "rows": [
    {
      "degree_id": "D1",
      "course_id": "C1",
      "faculty_id": "F1",
      "plan_requirement_type_id": "R1",
      "course_credits": 3,
      "count": 20,
      "mark_sum": 1420,
      "fail_count": 3,
      "attempt_sum": 24,
      "retake_count": 4
    }
  ]
}
```

Or `{"success": true, "data": {"part_id": ..., "rows": [...]}}`.

The GUI displays the JSON, then calls the existing **read-only** history validation endpoint and preview endpoint using the admin key (when configured). It **does not update cumulative history automatically**.

Your existing history service requires more than a part ID to **commit** and **activate**. Specifically:
- Commit needs an authoritative `finalization` record containing `finalized_part_id` and `approval_reference`, a `preview_token`, plus explicit confirmation.
- Activate needs the committed version's `expected_history_sha256` and explicit confirmation.
- If PHP only returns `part_id` and `rows`, the GUI cannot legitimately invent finalization proof. It displays a warning and will stop before committing.
- The underlying history subsystem accumulates the new semester's delta into an immutable cumulative version; this GUI does not perform its own summation.

If your university history API uses a different envelope or parameter name, **adjust the `.env` mappings**, or the small `frozen_history` adapter in `ui_client.py` if the shape differs; do not relax validation.

## 5. Troubleshooting

| Symptom | Likely cause |
|---|---|
| Missing URL | Check `.env` in project root and restart Streamlit |
| Student identity mismatch | Student API response belongs to another student or semester |
| `422 INVALID_REQUEST_SCHEMA` | Missing request fields / incorrect `integration_context` contract |
| `422 INVALID_INPUTS` | Required student/courses evidence missing or conflicting |
| `503 DEPENDENCY_UNAVAILABLE` | FastAPI artifacts, approved history, catalog, or grade scale not ready |
| `409` while retrying | `request_id` reused with a different payload |
| `503 INFERENCE_BUSY` | Existing inference worker lock was busy |
| History manual commit disabled | `finalization`/preview token/admin authorization missing |

This client is intended for **local testing only**, not as a publicly exposed student portal.

## 6. Tests

```powershell
python -m pytest tools/academic_advisor_streamlit/tests -q
```

These are isolated tests of URL mapping, identity, payload assembly and client behavior. Live PHP/FastAPI end-to-end tests require your deployed endpoints and original model artifacts.

### Custom upstream headers (token/user)

If the university endpoints require HTTP headers named `token` and `user`, add the following **single line** to the repository-root `.env`:

```dotenv
ADVISOR_UI_BACKEND_HEADERS={"token":"YOUR_TOKEN","user":"YOUR_USERNAME"}
ADVISOR_UI_BACKEND_TOKEN=
```

Header names are exact and may vary across backends. The older `ADVISOR_UI_BACKEND_TOKEN` option specifically sends `Authorization: Bearer <token>`; it does **not** send a header named `token`. These custom headers are never forwarded to local FastAPI, which continues to use `ADVISOR_API_KEY` as `X-API-Key`. Restart Streamlit after editing `.env`. Keep `.env` out of Git.
