# Academic Advisor — Pilot API Capture tab

This patch adds **📥 جمع وحفظ بيانات التجربة** as a third tab in your existing `tools/academic_advisor_streamlit/streamlit_app.py`. It does not change the existing Student/History interaction, model, FastAPI, history commit/activate, or `.env` settings.

## Installation

1. Back up the current `tools/academic_advisor_streamlit/streamlit_app.py` and `ui_client.py` files, or use a Git branch.
2. Copy the files from this patch archive to the repository root, preserving directory names. Only the Streamlit app and client are replacements; the collection store and test are new.
3. Ensure `data/evaluation/recommendation_pilot_20251/students.csv` exists, with `sample_id`, `role` (`primary`/`reserve`), `student_id`, `degree_id`, `part_id=20251`.
4. Start the Streamlit app using the same command as before:

```powershell
python -m streamlit run tools/academic_advisor_streamlit/streamlit_app.py
```

5. Open the third tab. Use the single-student/single-history buttons first. Then use the batch buttons for 30 primary students and 15 historical terms.

## Archive layout

```text
data/evaluation/recommendation_pilot_20251/
├── students.csv
└── api_data/
    ├── .gitignore                   # automatically created; excludes all captures
    ├── students/
    │   └── S001/
    │       ├── student_response.json
    │       ├── student_response.meta.json
    │       ├── courses_response.json
    │       └── courses_response.meta.json
    └── frozen_history/
        ├── 20201.json
        ├── 20201.meta.json
        └── ... through 20243.json
```

Each `.json` preserves the **exact original HTTP response body bytes**. No feature engineering or history aggregation is performed. `.meta.json` records source API kind, pilot identifiers, UTC capture time, byte count, and SHA-256. No authorization headers or tokens are stored.

A successful capture is **immutable**: reruns skip a previously verified file; checksum mismatches stop that item rather than overwrite it. This makes Experiment 1 and Experiment 2 use the same archived inputs.

## Important limitations

- The collector reuses the existing configured API endpoints and authentication; it never calls the recommendation engine or history administrative commit/activate endpoints.
- All dates are fixed to the 20251 pilot; history fetching is limited to the 15 parts `20201` through `20243`. It validates that historic rows, when they specify `PART_ID`, match the requested period.
- Historical API capture accepts a response with either `rows` or `CoursesStatistsic`, including the usual `data` envelope. The existing production update flow is unchanged.
- The existing client enforces an **8 MiB maximum per API response**. If a single term exceeds that size, the collector will fail that term visibly rather than silently truncate it. Have Codex adjust the size policy with bounded streaming if necessary.
- The app verifies student identity and the degree in `students.csv` against the university student response. An outdated or mismatched sample is not saved.
- `students.csv` is sensitive too. Ensure it is excluded from Git (and remove it from the index if it is already tracked); the patch automatically ignores only `api_data/`.
- This implementation has **not been tested against your live university endpoints**. All seven local unit tests for the capture/store pass. Streamlit is not installed in the artifact-building environment, so the graphical UI itself was syntax-checked, not run here.

## Local tests

```powershell
python -m unittest discover -s tools/academic_advisor_streamlit/tests -p 'test_pilot_*.py'
```

For additional security, keep pilot data on an encrypted local drive with appropriate access restrictions; raw student and course responses can contain personal information.
