"""Offline AppTest coverage: fake service and HTTP transport forbid real scoring/network."""
from __future__ import annotations

from pathlib import Path
import sys

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

UI_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(UI_ROOT))


class FakePilotService:
    def __init__(self):
        self.starts = []
        self.complete = True
        self.loaded = []
        self.rows = [{"sample_id": f"S{i:02}", "role": "primary"} for i in range(1, 31)]

    def cohort(self, include_reserve=False):
        return self.rows + ([{"sample_id": "R01", "role": "reserve"}] if include_reserve else [])

    def completeness(self, snapshot_id="after_backend_fix", include_reserve=False):
        rows = self.cohort(include_reserve)
        ready = rows if self.complete else rows[:2]
        return dict(snapshot_id=snapshot_id, student_saved=len(rows), courses_saved=len(ready),
                    history_saved=15, history_total=15, primary_count=30,
                    ready_sample_ids=[r["sample_id"] for r in ready],
                    blocked=[] if self.complete else [{"sample_id": "S03", "field": "Courses", "reason": "MISSING"}],
                    records=[])

    def preview(self, sample_id, snapshot_id="after_backend_fix"):
        return {"sample_id": sample_id, "previous_gpa": 2.1, "available_course_count": 8}

    def start(self, sample_ids, **kwargs):
        self.starts.append((list(sample_ids), kwargs))
        return "new-run"

    def progress(self, run_id):
        return {"run_id": run_id, "status": "running", "completed": 1, "total": 30,
                "sample_statuses": [{"sample_id": "S01", "status": "completed"}]}

    def list_runs(self):
        return [{"run_id": "old-run", "family": "comparison", "snapshot_id": "before_backend_fix", "status": "completed"},
                {"run_id": "diagnostic", "family": "actual_candidate_injection", "snapshot_id": "before_backend_fix", "status": "completed"}]

    def load_run(self, run_id, family="comparison"):
        self.loaded.append((run_id, family))
        return {"run_manifest": {"snapshot_id": "before_backend_fix", "selected_models": ["B"], "sample_ids": ["S01"]},
                "student_results": [{"sample_id": "S01"}]}

    def presentation(self, saved_run, sample_id):
        return {"sample_id": sample_id, "snapshot_id": "before_backend_fix",
                "student_summary": {"previous_gpa": 2.1},
                "summary_rows": [{"model": "B", "predicted_gpa": 2.5, "best_predicted_plan_gpa": 2.5,
                    "status": "PARTIAL", "reason": "SYNTHETIC_SAVED_PARTIAL",
                    "actual_plan_gpa_absolute_error": 0.2, "evaluated_plans": None,
                    "evaluated_plans_reason": "LEGACY_COUNT_UNAVAILABLE", "top1_actual_overlap_fraction": 0.5}],
                "plans_by_model": {"B": [{"rank": 1, "predicted_gpa": 2.5,
                    "overlap_fraction": 0.5, "plan_difficulty_balance": {"max_fail_probability": 0.125},
                    "course_rows": [{"course_id": 1, "predicted_mark": 80, "is_actual_course": False,
                                     "actual_mark": None, "actual_mark_reason": "NOT_ACTUAL_COURSE"}]}]},
                "actual_course_rows": [{"course_id": 2, "actual_mark": 60, "B_predicted_mark": 65, "B_error": 5}],
                "actual_summary": {"descriptive_gpa": None, "descriptive_gpa_reason": "PARTIAL_GRADES",
                    "models": {name: {"predicted_actual_plan_gpa": 2.2, "mae": 5, "rmse": 5, "bias": 5}
                               for name in ("B", "C")}},
                "execution": {"total_wall_seconds": 3.25, "provenance": "saved_measured_wall_clock",
                    "observed_prediction_cache_status": "cache_hit", "presentation_load_cache_status": "projection_hit",
                    "result_source": "saved_run"},
                "search": {"visited_search_states": 123, "state_budget": 200, "search_budget_exhausted": True,
                    "truncated": True},
                "timing_rows": [{"model": "B", "stage": "inference", "seconds": None,
                    "provenance": "saved_run", "measurement_scope": "model_inference",
                    "reason": "HISTORICAL_TIMING_UNAVAILABLE"}],
                "warnings": ["PROVISIONAL"]}


@pytest.fixture
def offline_config(monkeypatch):
    """The real .env and cached resources must never affect offline UI tests."""
    import ui_client
    config = ui_client.Config(
        fastapi_base="http://127.0.0.1:8000", student_url="https://university.example/student",
        courses_url="https://university.example/courses", history_url="https://university.example/history",
        student_params={"student_id": "studentId", "part_id": "semesterId"},
        courses_params={"student_id": "studentId", "degree_id": "degreeId", "part_id": "semesterId"},
        history_params={"part_id": "part_id"}, history_method="GET", service_key="", admin_key="",
        upstream_bearer="", timeout=1, context_file=None,
    )
    st.cache_resource.clear()
    monkeypatch.setattr(ui_client.Config, "from_env", classmethod(lambda cls, env_path=None: config))
    yield config
    st.cache_resource.clear()


@pytest.fixture
def ui(monkeypatch, offline_config):
    # Import only the presentation module; PilotService itself is created lazily.
    import pilot_ui
    fake = FakePilotService()
    monkeypatch.setattr(pilot_ui, "get_pilot_service", lambda: fake)
    app = AppTest.from_string("from pilot_ui import render_pilot\nrender_pilot()", default_timeout=20)
    return app, fake


def test_defaults_are_offline_after_bc_primary_thirty(ui):
    app, fake = ui
    app.run()
    assert not app.exception
    assert app.selectbox(key="pilot_compare_snapshot").value == "after_backend_fix"
    assert app.multiselect(key="pilot_compare_models").value == ["B", "C"]
    assert len(app.selectbox(key="pilot_compare_student").options) == 30
    assert not fake.starts


def test_single_run_passes_selected_models_and_exact_controls(ui):
    app, fake = ui
    app.run()
    app.multiselect(key="pilot_compare_models").set_value(["C"])
    app.selectbox(key="pilot_compare_max_plans").select(1000)
    app.button(key="pilot_compare_one").click().run()
    assert not app.exception
    assert fake.starts == [(["S01"], {"models": ["C"], "snapshot_id": "after_backend_fix",
        "target_credits": 18, "max_plans": 1000, "include_reserve": False})]
    app.run()
    assert len(fake.starts) == 1


def test_batch_progress_rerender_never_restarts(ui):
    app, fake = ui
    app.run().button(key="pilot_compare_batch").click().run()
    assert not app.exception
    assert len(fake.starts[0][0]) == 30
    app.button(key="pilot_compare_refresh").click().run()
    app.run()
    assert len(fake.starts) == 1
    assert any("new-run" in c.value for c in app.caption)


def test_before_snapshot_browses_only_and_loads_saved_without_start(ui):
    app, fake = ui
    app.run().selectbox(key="pilot_compare_snapshot").select("before_backend_fix").run()
    assert app.button(key="pilot_compare_one").disabled
    assert app.button(key="pilot_compare_batch").disabled
    app.selectbox(key="pilot_compare_saved_run").select("old-run")
    app.button(key="pilot_compare_load").click().run()
    assert not app.exception
    assert fake.loaded[-1] == ("old-run", "comparison")
    assert not fake.starts
    assert any("نتائج الطالب الفعلية" in h.value for h in app.subheader)
    assert any("PARTIAL_GRADES" in c.value for c in app.caption)


def test_incomplete_batch_requires_explicit_valid_subset(ui):
    app, fake = ui
    fake.complete = False
    app.run()
    assert app.button(key="pilot_compare_batch").disabled
    app.button(key="pilot_compare_subset").click().run()
    assert not app.exception
    assert fake.starts[0][0] == ["S01", "S02"]


def test_saved_diagnostic_label_keeps_normal_start_ordinary(ui):
    app, fake = ui
    app.run().selectbox(key="pilot_compare_saved_run").select("diagnostic")
    app.button(key="pilot_compare_load").click().run()
    assert fake.loaded[-1] == ("diagnostic", "actual_candidate_injection")
    app.button(key="pilot_compare_one").click().run()
    assert "injection" not in str(fake.starts[-1][1])


def test_existing_console_keeps_production_form_history_and_collection(monkeypatch, offline_config):
    import ui_client
    calls = []
    def forbidden(*args, **kwargs):
        raise AssertionError("Unexpected network request")
    monkeypatch.setattr(ui_client.HttpClient, "health", forbidden)
    monkeypatch.setattr(ui_client.HttpClient, "student", lambda self, sid, term: calls.append((sid, term)) or
        {"data": {"studentDegreeInfo": {"STUDENT_ID": sid, "DEGREE_ID": "D", "STATUS_SEMESTER_ID": str(term)}}})
    monkeypatch.setattr(ui_client.HttpClient, "courses", lambda *args: {"data": {"availableCourses": [], "registserRule": {}}})
    app = AppTest.from_file(str(UI_ROOT / "streamlit_app.py"), default_timeout=30).run()
    assert not app.exception
    assert len(app.tabs) == 3
    assert app.radio(key="advisor_operating_mode").value == "Production FastAPI"
    assert any(x.label == "Student ID" for x in app.text_input)
    assert any(x.label == "الفصل المُعتمد الذي نريد جلب Delta له" for x in app.text_input)
    assert any(x.label == "نسخة البيانات" for x in app.selectbox)
    next(x for x in app.text_input if x.label == "Student ID").set_value("S")
    next(x for x in app.text_input if x.label == "الفصل المطلوب (part_id)").set_value("20262")
    next(x for x in app.button if x.label == "1 · جلب وعرض JSON فقط").click().run()
    assert not app.exception
    assert calls == [("S", 20262)]


def test_pilot_mode_inside_existing_tab_has_no_http_requests(ui, monkeypatch):
    import requests
    app, fake = ui
    def forbidden(*args, **kwargs):
        raise AssertionError("Unexpected HTTP request in Pilot mode")
    monkeypatch.setattr(requests.Session, "request", forbidden)
    app = AppTest.from_file(str(UI_ROOT / "streamlit_app.py"), default_timeout=30).run()
    app.radio(key="advisor_operating_mode").set_value("Pilot 20251 — Model Comparison").run()
    assert not app.exception
    assert len(app.tabs) == 3
    assert app.multiselect(key="pilot_compare_models").value == ["B", "C"]
    assert not fake.starts


def test_invalid_production_config_keeps_offline_pilot_available(ui, monkeypatch):
    import requests
    import ui_client
    _, fake = ui
    def invalid_config(cls, env_path=None):
        raise ui_client.ClientError("SYNTHETIC_PRODUCTION_CONFIG_UNAVAILABLE")
    def forbidden(*args, **kwargs):
        raise AssertionError("Unexpected HTTP request with invalid production configuration")
    st.cache_resource.clear()
    monkeypatch.setattr(ui_client.Config, "from_env", classmethod(invalid_config))
    monkeypatch.setattr(requests.Session, "request", forbidden)
    app = AppTest.from_file(str(UI_ROOT / "streamlit_app.py"), default_timeout=30).run()
    assert not app.exception
    assert len(app.tabs) == 3
    assert app.radio(key="advisor_operating_mode").value == "Production FastAPI"
    assert not app.text_input
    app.radio(key="advisor_operating_mode").set_value("Pilot 20251 — Model Comparison").run()
    assert not app.exception
    assert app.multiselect(key="pilot_compare_models").value == ["B", "C"]
    assert not fake.starts
    app.radio(key="advisor_operating_mode").set_value("Production FastAPI").run()
    assert not app.exception
    assert not app.text_input
    assert any("SYNTHETIC_PRODUCTION_CONFIG_UNAVAILABLE" in item.value for item in app.error)


def test_completed_job_does_not_replace_saved_browsing_on_rerender(ui):
    app, fake = ui
    fake.progress = lambda run_id: {"status": "completed", "total": 1, "completed": 1}
    app.run().button(key="pilot_compare_one").click().run()
    app.selectbox(key="pilot_compare_saved_run").select("old-run")
    app.button(key="pilot_compare_load").click().run()
    app.run()
    assert not app.exception
    assert fake.loaded[-1] == ("old-run", "comparison")
    assert len(fake.starts) == 1


def test_reserve_is_opt_in_and_empty_models_disable_new_runs(ui):
    app, fake = ui
    app.run().checkbox(key="pilot_compare_reserve").check().run()
    assert len(app.selectbox(key="pilot_compare_student").options) == 31
    app.multiselect(key="pilot_compare_models").set_value([]).run()
    assert app.button(key="pilot_compare_one").disabled
    assert app.button(key="pilot_compare_batch").disabled
    assert not fake.starts


def test_missing_courses_preview_keeps_blocked_controls_and_saved_browser(ui):
    app, fake = ui
    fake.complete = False
    def missing(*args, **kwargs):
        raise ValueError("MISSING_SNAPSHOT_RESPONSE: courses_response")
    fake.preview = missing
    app.run()
    assert not app.exception
    assert app.button(key="pilot_compare_one")
    assert app.button(key="pilot_compare_batch").disabled
    assert app.selectbox(key="pilot_compare_saved_run")


def test_fractional_exact_credit_target_is_selectable_and_preserved(ui):
    app, fake = ui
    app.run().number_input(key="pilot_compare_credits").set_value(19.5)
    app.button(key="pilot_compare_one").click().run()
    assert not app.exception
    assert fake.starts[0][1]["target_credits"] == 19.5


def test_failed_job_shows_error_without_loading_nonexistent_result(ui):
    app, fake = ui
    fake.progress = lambda run_id: {"status": "failed", "total": 1, "completed": 0,
        "error": "SyntheticWorkerError", "sample_statuses": [{"sample_id": "S01", "status": "failed"}]}
    app.run().button(key="pilot_compare_one").click().run()
    app.run()
    assert not app.exception
    assert not fake.loaded
    assert len(fake.starts) == 1
    assert any("SyntheticWorkerError" in item.value for item in app.error)


def test_partial_job_preserves_student_failures_without_loading_missing_run(ui):
    app, fake = ui
    fake.progress = lambda run_id: {"status": "partial", "total": 2, "completed": 2,
        "sample_statuses": [{"sample_id": "S01", "status": "completed"},
                            {"sample_id": "S02", "status": "failed", "reason": "SYNTHETIC_INPUT_MISSING"}]}
    app.run().button(key="pilot_compare_one").click().run()
    assert not app.exception
    assert not fake.loaded
    assert any("جزئي" in item.value for item in app.warning)
    assert any("SYNTHETIC_INPUT_MISSING" in table.value.astype(str).to_string() for table in app.dataframe)


def test_zero_credits_blocks_new_runs(ui):
    app, fake = ui
    app.run().number_input(key="pilot_compare_credits").set_value(0.0).run()
    assert not app.exception
    assert app.button(key="pilot_compare_one").disabled
    assert app.button(key="pilot_compare_batch").disabled
    assert not fake.starts


def test_saved_fields_cards_search_context_and_percentage_are_visible(ui):
    app, fake = ui
    app.run().button(key="pilot_compare_load").click().run()
    assert not app.exception
    tables = [item.value for item in app.dataframe]
    assert any("max_fail_probability" in table.columns for table in tables)
    assert any("50.0%" in table.astype(str).to_string() for table in tables)
    assert any("actual_plan_gpa_absolute_error" in table.columns for table in tables)
    assert any("state_budget" in table.columns and table.iloc[0]["state_budget"] == 200 for table in tables)
    assert any("measurement_scope" in table.columns for table in tables)
    captions = " ".join(item.value for item in app.caption)
    assert "cache_hit" in captions and "saved_run" in captions
    assert "سياق بديل" in captions
    assert sum("MAE" in item.label for item in app.metric) == 2


def test_saved_recommendation_cards_show_alternative_gpa_status_and_cache(ui):
    app, fake = ui
    app.run().button(key="pilot_compare_load").click().run()
    assert not app.exception
    best = next(item for item in app.metric if "خطة بديلة" in item.label)
    assert best.value == "2.500"
    evaluated = next(item for item in app.metric if "الخطط المفحوصة" in item.label)
    assert "LEGACY_COUNT_UNAVAILABLE" in evaluated.value
    captions = " ".join(item.value for item in app.caption)
    assert "PARTIAL" in captions and "SYNTHETIC_SAVED_PARTIAL" in captions
    assert "projection_hit" in captions


def test_legacy_none_table_values_always_show_an_unavailable_reason(offline_config):
    app = AppTest.from_string("from pilot_ui import _table\n_table([{'legacy_field': None}])").run()
    assert not app.exception
    assert app.dataframe[0].value.iloc[0]["legacy_field"] == "N/A — SAVED_VALUE_UNAVAILABLE"


def test_diagnostic_scenarios_have_unique_students_and_explicit_context(ui):
    app, fake = ui
    original_presentation = fake.presentation
    selected_scenarios = []
    fake.load_run = lambda *args, **kwargs: {"student_results": [
        {"sample_id": "S01", "candidate_mode": "ordinary", "credit_experiment": "fixed_18", "status": "completed"},
        {"sample_id": "S01", "candidate_mode": "injected", "credit_experiment": "actual_load", "status": "partial"}]}
    def present(saved, sample_id, scenario=None):
        selected_scenarios.append(scenario)
        return original_presentation(saved, sample_id)
    fake.presentation = present
    app.run().selectbox(key="pilot_compare_saved_run").select("diagnostic")
    app.button(key="pilot_compare_load").click().run()
    assert not app.exception
    assert app.selectbox(key="pilot_compare_saved_student").options == ["S01"]
    app.selectbox(key="pilot_compare_saved_scenario").select(("injected", "actual_load")).run()
    assert selected_scenarios[-1] == ("injected", "actual_load")
    assert any("candidate_mode" in table.value.columns and "credit_experiment" in table.value.columns for table in app.dataframe)
