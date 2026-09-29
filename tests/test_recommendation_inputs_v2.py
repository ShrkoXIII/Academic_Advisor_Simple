"""Serving input isolation and start-of-semester regression contracts."""

import json
from pathlib import Path
import sys

import pandas as pd
from pandas.testing import assert_frame_equal
import pytest

from src.recommendation import inputs
from src.evaluation import evaluate_xml_recommendations as xml_evaluation
from src.features.frozen_history import validate_history_selection


@pytest.fixture
def v2_inputs(tmp_path, monkeypatch):
    status = pd.DataFrame([
        {
            "student_status_id": f"status_{part}", "student_id": "s", "degree_id": "d",
            "part_id": part, "grade_version_id": "v", "gpa_points": gpa,
            "last_enrolled_gpa": previous, "semester_reg_courses": 1,
            "semester_reg_credits": 3., "total_reg_courses": count,
            "total_reg_credits": count * 3., "total_fail_courses": 1,
            "total_fail_credits": 3., "reg_total_semesters": count + 1,
            "start_agpa_points": 2.5, "start_total_in_courses": count,
            "start_total_in_credits": count * 3., "end_agpa_points": 3.,
            "end_total_in_courses": count + 1, "end_total_in_credits": (count + 1) * 3.,
            "semester_pass_courses": 1, "semester_pass_credits": 3.,
            "semester_fail_courses": 0, "semester_fail_credits": 0.,
            "observed_gap_semesters": 0, "degree_credits_count": 120.,
        }
        for part, gpa, previous, count in [
            (20232, 2.0, None, 3), (20243, 3.0, 2.0, 4),
            (20251, 4.0, 3.0, 5), (20252, 1.0, 4.0, 6),
        ]
    ])
    history = pd.DataFrame({
        "student_id": ["s"] * 4, "degree_id": ["old", "d", "d", "d"],
        "part_id": [20232, 20243, 20251, 20252], "course_id": ["c"] * 4,
        "attempt_number": [2, 3, 4, 5], "faculty_id": ["f"] * 4,
        "course_credits": [3.] * 4, "final_mark": [40, 60, 90, 30],
        "points": [0., 2., 4., 0.],
    })
    catalog = pd.DataFrame({
        "degree_id": ["d"], "course_id": ["c"], "course_credits": [3.],
        "course_name_sl": ["Course"], "course_type_id": ["t"],
        "requirement_type_id": ["r"], "year_order": [1], "semester_order": [1],
        "credits_count": [3.],
    })
    diplomas = pd.DataFrame({"student_id": ["s"], "diploma_gpa": [90.], "diploma_type_id": ["x"]})
    tables = {
        "CLEAN_STUDENT_COURSE_PATH": history, "CLEAN_STUDENT_STATUS_PATH": status,
        "CLEAN_DEGREE_COURSE_PATH": catalog, "CLEAN_STUDENT_DIPLOMA_PATH": diplomas,
    }
    paths = {}
    for name, table in tables.items():
        paths[name] = tmp_path / f"{name.lower()}_v2.parquet"
        table.to_parquet(paths[name], index=False)
        monkeypatch.setattr(inputs, f"{name}_V2", paths[name], raising=False)
        legacy = tmp_path / f"{name.lower()}.parquet"
        table.to_parquet(legacy, index=False)
        monkeypatch.setattr(inputs, name, legacy, raising=False)
    monkeypatch.setattr(inputs, "STUDENT_STATUS_PATH", tmp_path / "raw_v1_status.parquet", raising=False)
    status.to_parquet(inputs.STUDENT_STATUS_PATH, index=False)
    candidate_file = tmp_path / "candidates.json"
    candidate_file.write_text(json.dumps([{"course_id": "c", "course_credits": 3}]), encoding="utf-8")
    return candidate_file, paths, status, history, catalog, diplomas


def trace_v2_reads(monkeypatch, allowed):
    reads = []
    read_parquet = pd.read_parquet

    def traced(path, *args, **kwargs):
        path = Path(path)
        reads.append(path)
        assert path in allowed, f"Non-V2 input read attempted: {path}"
        return read_parquet(path, *args, **kwargs)

    monkeypatch.setattr(pd, "read_parquet", traced)
    return reads


def test_local_loader_reads_only_cleaned_v2_and_preserves_history(v2_inputs, monkeypatch):
    candidate_file, paths, *_ = v2_inputs
    reads = trace_v2_reads(monkeypatch, set(paths.values()))
    candidates, snapshot, report = inputs.load_local_inputs(candidate_file, "s", "d", 20251)

    assert set(reads) == set(paths.values())
    assert len(reads) == 4
    assert candidates.attempt_number.tolist() == [4]
    assert report["history_latest_part"] == 20243
    assert snapshot["gpa_prev_1"] == 3.
    assert snapshot["gpa_prev_2"] == 2.
    assert snapshot["prior_total_reg_credits"] == 15.
    assert snapshot["faculty_id"] == "f"
    assert "end_agpa_points" not in snapshot


@pytest.mark.parametrize("missing", [
    "CLEAN_STUDENT_COURSE_PATH", "CLEAN_STUDENT_STATUS_PATH",
    "CLEAN_DEGREE_COURSE_PATH", "CLEAN_STUDENT_DIPLOMA_PATH",
])
def test_local_missing_v2_fails_without_legacy_fallback(v2_inputs, monkeypatch, missing):
    candidate_file, paths, *_ = v2_inputs
    paths[missing].unlink()
    trace_v2_reads(monkeypatch, set(paths.values()))
    with pytest.raises(FileNotFoundError):
        inputs.load_local_inputs(candidate_file, "s", "d", 20251)


def test_local_supplied_snapshot_reads_only_v2_catalog_and_attempts(v2_inputs, monkeypatch, tmp_path):
    candidate_file, paths, status, history, _, diplomas = v2_inputs
    supplied = inputs.build_student_snapshot(status, history, diplomas, "s", "d", 20251)
    snapshot_file = tmp_path / "snapshot.json"
    snapshot_file.write_text(json.dumps(supplied), encoding="utf-8")
    allowed = {paths["CLEAN_STUDENT_COURSE_PATH"], paths["CLEAN_DEGREE_COURSE_PATH"]}
    reads = trace_v2_reads(monkeypatch, allowed)
    _, snapshot, _ = inputs.load_local_inputs(candidate_file, "s", "d", 20251, snapshot_file)
    assert set(reads) == allowed
    assert snapshot == supplied


def test_snapshot_and_attempts_ignore_target_and_future_outcomes(v2_inputs):
    _, _, status, history, catalog, diplomas = v2_inputs
    baseline = inputs.build_student_snapshot(status, history, diplomas, "s", "d", 20251)
    raw_candidates = pd.DataFrame({"course_id": ["c"], "course_credits": [3.]})
    candidates, _ = inputs.normalize_candidates(raw_candidates, catalog, history, "s", "d", 20251)
    changed_status = status.copy()
    outcome_columns = [
        "gpa_points", "end_agpa_points", "end_total_in_courses", "end_total_in_credits",
        "semester_pass_courses", "semester_pass_credits", "semester_fail_courses",
        "semester_fail_credits", "reg_total_semesters",
    ]
    changed_status.loc[changed_status.part_id.ge(20251), outcome_columns] = 999
    changed_history = history.copy()
    changed_history.loc[changed_history.part_id.ge(20251), ["final_mark", "points", "attempt_number"]] = 999
    changed_history.loc[changed_history.part_id.ge(20251), "faculty_id"] = "future_faculty"
    changed_snapshot = inputs.build_student_snapshot(changed_status, changed_history, diplomas, "s", "d", 20251)
    changed_candidates, _ = inputs.normalize_candidates(raw_candidates, catalog, changed_history, "s", "d", 20251)
    assert_frame_equal(pd.DataFrame([baseline]), pd.DataFrame([changed_snapshot]))
    assert_frame_equal(candidates, changed_candidates)


class SyntheticXmlEngine:
    """Keep model execution synthetic while exercising XML I/O and math."""

    def __init__(self, cutoff):
        self.cutoff = cutoff
        self.provenance = {"dataset_version": "V2", "history_as_of_part": cutoff}

    def prepare_candidates(self, snapshot, candidates, target, *, allow_older_history=False):
        validate_history_selection(target, self.cutoff, allow_older_history=allow_older_history)
        return candidates.copy()

    def score_rows(self, rows):
        return rows.assign(expected_points=2.8, fail_probability=.2)

    def recommend(self, snapshot, candidates, target, current_gpa, **kwargs):
        validate_history_selection(target, self.cutoff,
                                   allow_older_history=kwargs.get("allow_older_history", False))
        return pd.DataFrame(), {"recommendations": [], "matching_plan_count": 0}


@pytest.fixture
def xml_v2_run(v2_inputs, tmp_path, monkeypatch):
    _, paths, *_ = v2_inputs
    for name, path in paths.items():
        monkeypatch.setattr(xml_evaluation, f"{name}_V2", path, raising=False)
        monkeypatch.setattr(xml_evaluation, name, getattr(inputs, name), raising=False)
    monkeypatch.setattr(xml_evaluation, "STUDENT_STATUS_PATH", inputs.STUDENT_STATUS_PATH, raising=False)
    xml_dir = tmp_path / "xml"
    xml_dir.mkdir()
    headers, values = ["ROW", "STUDENT_ID", "COURSE_ID", "COURSE_CREDITS", "PART_ID"], ["1", "s", "c", "3", "20221"]
    rows = "".join(
        "<ss:Row>" + "".join(f'<ss:Cell><ss:Data ss:Type="String">{value}</ss:Data></ss:Cell>' for value in row) + "</ss:Row>"
        for row in [headers, values]
    )
    (xml_dir / "candidate.xml").write_text(
        '<ss:Workbook xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">'
        '<ss:Worksheet><ss:Table>' + rows + '</ss:Table></ss:Worksheet></ss:Workbook>',
        encoding="utf-8",
    )
    output = tmp_path / "run"
    monkeypatch.setattr(xml_evaluation.AcademicPlanRecommender, "load",
                        lambda **kwargs: SyntheticXmlEngine(kwargs["history_as_of_part"]))

    def configure(target=20251, cutoff=20243, older=False):
        arguments = ["xml-evaluation", "--xml-dir", str(xml_dir), "--target-part", str(target),
                     "--history-as-of-part", str(cutoff), "--output-dir", str(output)]
        if older:
            arguments.append("--allow-older-history")
        monkeypatch.setattr(sys, "argv", arguments)
        return trace_v2_reads(monkeypatch, set(paths.values()))

    return configure, output, paths


@pytest.mark.parametrize("target,cutoff,actual_gpa", [(20251, 20243, 2.75), (20252, 20251, 48 / 21)])
def test_xml_reads_only_v2_preserves_actual_math_and_explicit_target(xml_v2_run, target, cutoff, actual_gpa):
    configure, output, paths = xml_v2_run
    reads = configure(target, cutoff)
    xml_evaluation.main()
    assert set(reads) == set(paths.values())
    assert len(reads) == 4
    case = json.loads(next(output.glob("*/case.json")).read_text(encoding="utf-8"))
    assert case["target_part"] == target
    assert case["xml_part_values"] == ["20221"]
    assert case["metrics"]["actual_cumulative_gpa_formula"] == pytest.approx(actual_gpa)
    assert case["recommendations"] == []
    assert case["observed_plan_estimate"]["status"] == "ok"
    manifest = json.loads((output / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["model_provenance"]["history_as_of_part"] == cutoff


@pytest.mark.parametrize("missing", [
    "CLEAN_STUDENT_COURSE_PATH", "CLEAN_STUDENT_STATUS_PATH",
    "CLEAN_DEGREE_COURSE_PATH", "CLEAN_STUDENT_DIPLOMA_PATH",
])
def test_xml_missing_v2_fails_without_legacy_fallback(xml_v2_run, missing):
    configure, _, paths = xml_v2_run
    paths[missing].unlink()
    configure()
    with pytest.raises(FileNotFoundError):
        xml_evaluation.main()


def test_xml_older_history_requires_explicit_opt_in(xml_v2_run):
    configure, output, _ = xml_v2_run
    configure(cutoff=20232)
    with pytest.raises(SystemExit) as error:
        xml_evaluation.main()
    assert error.value.code == 2
    summary = json.loads((output / "run_manifest.json").read_text(encoding="utf-8"))
    assert summary["arguments"]["allow_older_history"] is False
    assert "older" in (output / "report_ar.md").read_text(encoding="utf-8")


def test_xml_older_history_opt_in_applies_to_recommendation_and_observed_plan(xml_v2_run):
    configure, output, _ = xml_v2_run
    configure(cutoff=20232, older=True)
    xml_evaluation.main()
    case = json.loads(next(output.glob("*/case.json")).read_text(encoding="utf-8"))
    assert case["observed_plan_estimate"]["status"] == "ok"
    assert case["observed_plan_estimate"]["expected_plan_gpa"] == pytest.approx(2.8)
    assert case["observed_plan_estimate"]["projected_cumulative_gpa"] == pytest.approx(2.55)
