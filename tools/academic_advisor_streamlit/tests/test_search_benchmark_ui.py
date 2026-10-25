"""Offline UI checks: rerenders and saved browsing cannot launch model scoring."""
from __future__ import annotations

from pathlib import Path
import sys

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

UI_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(UI_ROOT))


def test_search_benchmark_is_available_in_the_existing_console():
    app = AppTest.from_string(
        "from search_benchmark_ui import render_search_benchmark\n"
        "assert callable(render_search_benchmark)"
    ).run()
    assert not app.exception


class FakeSearchService:
    def __init__(self):
        self.starts = []
        self.inspections = []
        self.loaded = []
        self.unresolved = False

    def cohort(self):
        return [{"sample_id": f"S{i:02}", "role": "primary"} for i in range(1, 31)]

    def inspect(self, sample_ids):
        self.inspections.append(list(sample_ids))
        return [{"sample_id": sample, "status": "READY", "reason": None,
            "target_resolution": {"status": "UNRESOLVED" if self.unresolved else "RESOLVED",
                "reason": "MISSING_API_CREDIT_MAXIMUM" if self.unresolved else None,
                "target_credits": None if self.unresolved else 12 if sample == "S02" else 18,
                "target_credits_source": "API", "minimum_credits": 9,
                "maximum_credits": None if self.unresolved else 12 if sample == "S02" else 18},
            "candidate_count": 14, "feasible_plan_count": 4321, "previous_gpa": 2.1}
            for sample in sample_ids]

    def start(self, sample_ids, **kwargs):
        self.starts.append((list(sample_ids), kwargs))
        return "new-search-run"

    def progress(self, run_id):
        return {"status": "running", "completed": 1, "total": 2,
                "current_sample": "S01", "details": [{"sample_id": "S01", "status": "running"}]}

    def list_runs(self):
        return [{"run_id": "saved-complete", "status": "COMPLETED", "created_at": "2026-10-24"},
                {"run_id": "saved-incomplete", "status": "EXHAUSTIVE_INCOMPLETE", "created_at": "2026-10-24"}]

    def load_run(self, run_id):
        self.loaded.append(run_id)
        return {"run_manifest": {"run_id": run_id, "sample_ids": ["S01"],
                "snapshot_id": "after_backend_fix", "status": "EXHAUSTIVE_INCOMPLETE"},
            "student_results": [{"sample_id": "S01", "status": "EXHAUSTIVE_INCOMPLETE",
                "reason": "MAX_SECONDS", "experiments": [{"model": "B", "strategy": "FIRST_N",
                    "scope": "FULL_SPACE", "budget": 200, "target_credits": 18,
                    "evaluated_plans": 200, "best_gpa": 2.7, "oracle_gpa": None,
                    "gpa_gap": None, "top3_recall": None, "diversity": {"mean_jaccard": 0.75},
                    "runtime_seconds": 1.25, "status": "EXHAUSTIVE_INCOMPLETE", "reason": "MAX_SECONDS",
                    "top_plans": [{"canonical_id": "1,2", "plan_id": 11, "total_credits": 18,
                        "expected_plan_gpa": 2.7, "expected_failed_credits": 0.25,
                        "plan_difficulty_balance": {"max_fail_probability": 0.1},
                        "courses": [{"course_id": 1, "course_name": "Synthetic course",
                            "credits": 3, "predicted_mark": 78, "expected_points": 3.0}]}]}]}]}


@pytest.fixture
def search_ui(monkeypatch):
    import requests
    import search_benchmark_ui

    def forbidden(*args, **kwargs):
        raise AssertionError("Unexpected HTTP request from offline search UI")

    monkeypatch.setattr(requests.Session, "request", forbidden)
    fake = FakeSearchService()
    monkeypatch.setattr(search_benchmark_ui, "get_search_service", lambda: fake)
    app = AppTest.from_string("from search_benchmark_ui import render_search_benchmark\nrender_search_benchmark()",
                              default_timeout=20)
    return app, fake


def test_default_is_offline_after_api_target_and_selected_preview_only(search_ui):
    app, fake = search_ui
    app.run()
    assert not app.exception
    assert app.selectbox(key="search_benchmark_student").value == "S01"
    assert app.multiselect(key="search_benchmark_models").value == ["B", "C"]
    assert app.multiselect(key="search_benchmark_budgets").value == [200, 1000, 2000]
    assert any(metric.label == "Automatic Target Credits · API" and metric.value == "18" for metric in app.metric)
    assert fake.inspections == [["S01"]]
    assert not fake.starts
    assert any("after_backend_fix" in item.value for item in app.info)


def test_explicit_execution_passes_controls_and_rerenders_never_restart(search_ui):
    app, fake = search_ui
    app.run().multiselect(key="search_benchmark_models").set_value(["C"])
    app.multiselect(key="search_benchmark_budgets").set_value([200])
    app.multiselect(key="search_benchmark_strategies").set_value(["DIVERSE_N"])
    app.button(key="search_benchmark_run").click().run()
    assert not app.exception
    assert fake.starts == [(["S01"], {"models": ["C"], "strategies": ["DIVERSE_N"],
        "budgets": [200], "scopes": ["FIXED_POOL", "FULL_SPACE"], "seed": 42,
        "manual_target": None, "diagnostic_override": False,
        "limits": {"max_seconds": 300, "max_oracle_plans": 50000, "chunk_size": 128,
                   "max_space_states": 2000000, "max_disk_mb": 512}})]
    app.button(key="search_benchmark_refresh").click().run()
    app.run()
    assert len(fake.starts) == 1


def test_diagnostic_target_is_scoped_to_each_student(search_ui):
    app, fake = search_ui
    app.run().checkbox(key="search_benchmark_override_S01").check().run()
    app.number_input(key="search_benchmark_manual_S01").set_value(16).run()
    app.selectbox(key="search_benchmark_student").select("S02").run()
    assert not app.exception
    assert not app.checkbox(key="search_benchmark_override_S02").value
    assert any(metric.label == "Automatic Target Credits · API" and metric.value == "12" for metric in app.metric)
    app.button(key="search_benchmark_run").click().run()
    assert fake.starts[-1][1]["manual_target"] is None
    assert fake.starts[-1][1]["diagnostic_override"] is False


def test_missing_api_maximum_blocks_until_explicit_diagnostic_override(search_ui):
    app, fake = search_ui
    fake.unresolved = True
    app.run()
    assert app.button(key="search_benchmark_run").disabled
    assert any("MISSING_API_CREDIT_MAXIMUM" in item.value for item in app.warning)
    app.checkbox(key="search_benchmark_override_S01").check().run()
    app.number_input(key="search_benchmark_manual_S01").set_value(12).run()
    app.button(key="search_benchmark_run").click().run()
    assert not app.exception
    assert fake.starts[-1][1]["manual_target"] == 12
    assert fake.starts[-1][1]["diagnostic_override"] is True


def test_manual_target_cannot_exceed_visible_api_maximum(search_ui):
    app, fake = search_ui
    app.run().selectbox(key="search_benchmark_student").select("S02").run()
    app.checkbox(key="search_benchmark_override_S02").check().run()
    app.number_input(key="search_benchmark_manual_S02").set_value(18).run()
    assert app.button(key="search_benchmark_run").disabled
    assert not fake.starts


def test_saved_results_show_comparison_and_complete_course_details_without_scoring(search_ui):
    app, fake = search_ui
    app.run().button(key="search_benchmark_load").click().run()
    app.run()
    assert not app.exception
    tables = [item.value for item in app.dataframe]
    comparison = next(table for table in tables if "Student" in table.columns)
    assert list(comparison.columns) == ["Student", "Model", "Strategy", "Budget", "Target Credits",
        "Evaluated Plans", "Best GPA", "Oracle GPA", "GPA Gap", "Top-3 Recall", "Diversity", "Runtime", "Status", "Scope"]
    assert comparison.iloc[0]["Best GPA"] == 2.7
    assert "N/A" in comparison.iloc[0]["Oracle GPA"]
    assert any("course_id" in table.columns and "predicted_mark" in table.columns and "expected_points" in table.columns for table in tables)
    assert any("EXHAUSTIVE_INCOMPLETE" in item.value for item in app.warning)
    assert not fake.starts


def test_comparison_runtime_includes_saved_context_preparation(search_ui):
    app, fake = search_ui
    original_load = fake.load_run

    def saved_with_preparation(run_id):
        saved = original_load(run_id)
        saved["student_results"][0]["experiments"][0]["standalone_runtime_seconds"] = 2.5
        return saved

    fake.load_run = saved_with_preparation
    app.run().button(key="search_benchmark_load").click().run()
    assert not app.exception
    comparison = next(item.value for item in app.dataframe if "Student" in item.value.columns)
    assert comparison.iloc[0]["Runtime"] == 2.5
    assert not fake.starts


def test_resume_is_explicit_and_uses_saved_config_without_current_controls(search_ui):
    app, fake = search_ui
    app.run().selectbox(key="search_benchmark_saved_run").select("saved-incomplete").run()
    app.button(key="search_benchmark_resume").click().run()
    app.run()
    assert not app.exception
    assert fake.starts == [([], {"resume_run_id": "saved-incomplete", "limits": {
        "max_seconds": 300, "max_oracle_plans": 50000, "chunk_size": 128,
        "max_space_states": 2000000, "max_disk_mb": 512}})]


def test_optional_small_batch_is_explicit_and_cannot_exceed_five(search_ui):
    app, fake = search_ui
    app.run().checkbox(key="search_benchmark_batch_enabled").check().run()
    app.multiselect(key="search_benchmark_batch_students").set_value(["S01", "S02", "S03"])
    app.multiselect(key="search_benchmark_scopes").set_value(["EXHAUSTIVE"])
    app.button(key="search_benchmark_run").click().run()
    assert not app.exception
    assert fake.starts[-1][0] == ["S01", "S02", "S03"]
    assert fake.starts[-1][1]["scopes"] == ["EXHAUSTIVE"]


@pytest.mark.parametrize("valid_config", [True, False])
def test_search_mode_is_available_with_or_without_production_config(search_ui, monkeypatch, valid_config):
    import ui_client
    _, fake = search_ui
    st.cache_resource.clear()
    if valid_config:
        config = ui_client.Config(fastapi_base="http://127.0.0.1:8000", student_url="https://example.test/student",
            courses_url="https://example.test/courses", history_url="https://example.test/history",
            student_params={}, courses_params={}, history_params={}, history_method="GET", service_key="",
            admin_key="", upstream_bearer="", timeout=1, context_file=None)
        monkeypatch.setattr(ui_client.Config, "from_env", classmethod(lambda cls, env_path=None: config))
    else:
        def invalid(cls, env_path=None):
            raise ui_client.ClientError("SYNTHETIC_CONFIG_UNAVAILABLE")
        monkeypatch.setattr(ui_client.Config, "from_env", classmethod(invalid))
    app = AppTest.from_file(str(UI_ROOT / "streamlit_app.py"), default_timeout=30).run()
    app.radio(key="advisor_operating_mode").set_value("🔎 Search Benchmark").run()
    assert not app.exception
    assert len(app.tabs) == 3
    assert app.selectbox(key="search_benchmark_student").value == "S01"
    assert not fake.starts
    st.cache_resource.clear()
