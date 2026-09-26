"""The project runner selects and reports work without running it in tests."""

import subprocess
import sys

import pytest

from src import main as runner


def _record_processes(monkeypatch, *, failure_at=None):
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 7 if len(calls) == failure_at else 0)

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    return calls


def test_registry_has_dependency_order_and_named_optional_steps():
    assert runner.STANDARD_SECTIONS == (
        "data", "features", "modeling", "evaluation", "experiments",
    )
    assert [step.name for step in runner.PIPELINE["data"]] == [
        "clean_degree_course", "clean_student_course", "clean_student_status",
        "filter_common_students", "build_student_course_enriched",
        "clean_student_diploma", "clean_outliers", "build_temporal_split",
        "build_registration_roster",
    ]
    assert [step.name for step in runner.PIPELINE["features"]] == [
        "build_temporal_features", "build_frozen_history",
    ]
    assert [step.name for step in runner.PIPELINE["evaluation"]] == [
        "evaluate_plan_gpa", "analyze_model_errors", "evaluate_xml_recommendations",
    ]
    assert runner.STEPS["build_frozen_history"].request_specific
    assert runner.STEPS["evaluate_xml_recommendations"].request_specific
    assert runner.STEPS["recommend"].request_specific


def test_list_displays_standard_and_optional_work_without_execution(monkeypatch, capsys):
    def forbidden(*args, **kwargs):
        raise AssertionError("--list executed a pipeline step")

    monkeypatch.setattr(runner.subprocess, "run", forbidden)
    assert runner.main(["--list"]) == 0
    output = capsys.readouterr().out
    for item in ["data", "features", "modeling", "evaluation", "experiments",
                 "diagnostics", "recommendation", "train_models", "recommend",
                 "evaluate_xml_recommendations", "V2"]:
        assert item in output


def test_all_standard_stages_are_v2_and_request_workflows_keep_their_labels(monkeypatch, capsys):
    def forbidden(*args, **kwargs):
        raise AssertionError("Inspection executed a pipeline step")

    monkeypatch.setattr(runner.subprocess, "run", forbidden)
    assert runner.main(["--list"]) == 0
    output = capsys.readouterr().out
    for step, version in [("train_models", "V2"), ("evaluate_plan_gpa", "V2"),
                          ("analyze_model_errors", "V2"), ("degree_points", "V2")]:
        line = next(line for line in output.splitlines() if line.strip().startswith(step + " "))
        assert f"[{version}]" in line
    assert runner.STEPS["evaluate_xml_recommendations"].dataset == "request"
    assert runner.STEPS["recommend"].dataset == "request"
    assert runner.main(["--from", "data", "--to", "evaluation", "--dry-run"]) == 0
    assert "VERSION BOUNDARY" not in capsys.readouterr().out
    assert runner.main(["--all", "--dry-run"]) == 0
    assert "VERSION BOUNDARY" not in capsys.readouterr().out


def test_all_dry_run_shows_v2_commands_without_execution(monkeypatch, capsys):
    def forbidden(*args, **kwargs):
        raise AssertionError("dry-run executed a pipeline step")

    monkeypatch.setattr(runner.subprocess, "run", forbidden)
    assert runner.main(["--all", "--dry-run"]) == 0
    output = capsys.readouterr().out
    assert "src.data.clean_degree_course" in output
    assert "src.experiments.degree_points" in output
    assert "VERSION BOUNDARY" not in output
    assert "V2" in output and "V1" not in output
    assert "src.recommendation.local_cli" not in output
    assert "src.evaluation.evaluate_xml_recommendations" not in output
    assert "src.features.build_frozen_history" not in output


def test_section_and_step_selection_use_only_requested_modules(monkeypatch):
    calls = _record_processes(monkeypatch)
    assert runner.main(["--section", "data"]) == 0
    assert [command[2] for command, _ in calls] == [
        step.module for step in runner.PIPELINE["data"]
    ]
    assert all(command[:2] == [sys.executable, "-m"] for command, _ in calls)

    calls.clear()
    assert runner.main(["--section", "modeling"]) == 0
    assert [command[2] for command, _ in calls] == ["src.modeling.train_models"]

    calls.clear()
    assert runner.main(["--step", "train_models"]) == 0
    assert [command[2] for command, _ in calls] == ["src.modeling.train_models"]


def test_failure_stops_later_steps_and_returns_nonzero(monkeypatch, capsys):
    calls = _record_processes(monkeypatch, failure_at=2)
    assert runner.main(["--section", "data"]) == 7
    assert len(calls) == 2
    assert "FAIL clean_student_course" in capsys.readouterr().out


def test_all_excludes_optional_work_and_delegates_request_arguments(monkeypatch, capsys):
    calls = _record_processes(monkeypatch)
    assert runner.main(["--all"]) == 0
    assert "VERSION BOUNDARY" not in capsys.readouterr().out
    modules = [command[2] for command, _ in calls]
    assert modules[-1] == "src.experiments.degree_points"
    for excluded in [
        "src.features.build_frozen_history",
        "src.evaluation.evaluate_xml_recommendations",
        "src.recommendation.local_cli",
        "src.recommendation.benchmark",
        "src.diagnostics.compare_student_status_course",
        "src.diagnostics.analyze_course_plan_changes",
    ]:
        assert excluded not in modules

    calls.clear()
    assert runner.main(["--step", "recommend", "--", "--candidates", "candidate.parquet"]) == 0
    assert calls[0][0] == [
        sys.executable, "-m", "src.recommendation.local_cli",
        "--candidates", "candidate.parquet",
    ]

    calls.clear()
    assert runner.main(["--step", "evaluate_xml_recommendations", "--", "--help"]) == 0
    assert calls[0][0] == [
        sys.executable, "-m", "src.evaluation.evaluate_xml_recommendations", "--help",
    ]

    calls.clear()
    assert runner.main(["--step", "build_frozen_history", "--", "--as-of-part", "20243"]) == 0
    assert calls[0][0] == [
        sys.executable, "-m", "src.features.build_frozen_history", "--as-of-part", "20243",
    ]

    calls.clear()
    assert runner.main(["--section", "recommendation", "--", "--help"]) == 0
    assert calls[0][0] == [sys.executable, "-m", "src.recommendation.local_cli", "--help"]

    calls.clear()
    assert runner.main(["--section", "diagnostics"]) == 0
    assert [command[2] for command, _ in calls] == [
        "src.diagnostics.compare_student_status_course",
        "src.diagnostics.analyze_course_plan_changes",
    ]


def test_range_selects_inclusive_standard_sections(monkeypatch):
    calls = _record_processes(monkeypatch)
    assert runner.main(["--from", "data", "--to", "modeling"]) == 0
    modules = [command[2] for command, _ in calls]
    assert modules[-1] == "src.modeling.train_models"
    assert "src.evaluation.evaluate_plan_gpa" not in modules
    assert "src.features.build_frozen_history" not in modules


def test_process_launch_exception_is_reported_and_stops(monkeypatch, capsys):
    calls = []

    def fail_to_launch(command, **kwargs):
        calls.append(command)
        raise OSError("cannot start child")

    monkeypatch.setattr(runner.subprocess, "run", fail_to_launch)
    assert runner.main(["--section", "data"]) == 1
    assert len(calls) == 1
    assert "FAIL clean_degree_course" in capsys.readouterr().out


def test_arguments_are_not_broadcast_across_multiple_steps(monkeypatch):
    calls = _record_processes(monkeypatch)
    with pytest.raises(SystemExit, match="2"):
        runner.main(["--section", "data", "--", "--unexpected"])
    assert not calls
