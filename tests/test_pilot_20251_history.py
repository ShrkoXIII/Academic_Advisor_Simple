"""University aggregates must pass provenance and temporal integrity gates."""
import hashlib
import importlib
import json

import numpy as np
import pandas as pd
import pytest


PARTS = [year * 10 + term for year in range(2020, 2025) for term in (1, 2, 3)]


def module():
    spec = importlib.util.find_spec("tools.recommendation_pilot_20251.history")
    assert spec is not None, "The isolated history implementation is missing"
    return importlib.import_module("tools.recommendation_pilot_20251.history")


def row(part=20201, **changes):
    value = {"COURSE_ID": "c1", "PART_ID": str(part), "DEGREE_ID": "d1",
             "FACULTY_ID": "f1", "COURSE_CREDITS": "3", "STUDENTS_COUNT": "40",
             "REGISTER_STUDENTS_COUNT": "40", "PASS_STUDENTS": "30",
             "FAIL_STUDENTS": "6", "WITHDRAW_STUDENTS": "4",
             "SUM_MARKS": "2400", "RETAKE_COUNT": "8"}
    value.update(changes)
    return value


def write_source(root, part, rows, **metadata_changes):
    folder = root / "api_data" / "frozen_history"
    folder.mkdir(parents=True, exist_ok=True)
    file = folder / f"{part}.json"
    raw = json.dumps({"success": True, "data": {"CoursesStatistsic": rows}}).encode()
    file.write_bytes(raw)
    meta = {"kind": "history", "source": "university_frozen_history_api",
            "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
            "identity": {"part_id": part, "history_as_of_part": 20243, "row_count": len(rows)}}
    meta.update(metadata_changes)
    file.with_suffix(".meta.json").write_text(json.dumps(meta))
    return file


@pytest.fixture
def complete_sources(tmp_path):
    for part in PARTS:
        write_source(tmp_path, part, [row(part)])
    return tmp_path


def test_valid_sources_build_separate_artifact_without_mutating_inputs(complete_sources, tmp_path):
    folder = complete_sources / "api_data"
    before = {p: p.read_bytes() for p in folder.rglob("*.json")}
    output = tmp_path / "isolated"
    report = module().build_university_history(complete_sources, output_dir=output)
    assert report["status"] == "PASS"
    assert report["usable_for_b_c"] is True
    assert report["source_file_count"] == report["accepted_file_count"] == 15
    assert report["source_row_count"] == report["validated_row_count"] == 15
    assert report["as_of_part"] == 20243
    assert report["compatibility"]["requires_retraining"] is True
    artifact = json.loads((output / "university_history_validated.json").read_text())
    assert len(artifact["rows"]) == 15
    assert "attempt_sum" not in str(artifact)
    assert "plan_requirement_type_id" not in str(artifact)
    assert before == {p: p.read_bytes() for p in folder.rglob("*.json")}


@pytest.mark.parametrize("mutation,code", [
    ({"SUM_MARKS": None}, "INVALID_NUMBER"),
    ({"STUDENTS_COUNT": "0"}, "INVALID_DENOMINATOR"),
    ({"RETAKE_COUNT": "41"}, "COUNT_EXCEEDS_STUDENTS"),
    ({"FAIL_STUDENTS": "-1"}, "INVALID_NUMBER"),
    ({"PASS_STUDENTS": "31"}, "OUTCOME_COUNTS_EXCEED_STUDENTS"),
    ({"SUM_MARKS": "4001"}, "MARK_SUM_OUT_OF_RANGE"),
    ({"PART_ID": "20251"}, "SOURCE_PART_MISMATCH"),
])
def test_invalid_source_file_is_rejected_without_imputation(complete_sources, mutation, code):
    write_source(complete_sources, 20201, [row(**mutation)])
    report = module().build_university_history(complete_sources)
    assert report["status"] == "BLOCKED"
    assert report["usable_for_b_c"] is False
    assert report["rejected_file_count"] == 1
    assert report["accepted_file_count"] == 14
    assert code in {issue["code"] for issue in report["issues"]}
    assert all("student_id" not in issue for issue in report["issues"])


def test_incomplete_outcome_partition_is_unresolved_rather_than_fabricated(complete_sources):
    write_source(complete_sources, 20201, [row(PASS_STUDENTS="29")])
    report = module().build_university_history(complete_sources)
    assert report["status"] == "BLOCKED"
    assert report["rejected_file_count"] == 0
    assert report["unresolved_file_count"] == 1
    assert report["usable_for_b_c"] is False
    assert "UNRESOLVED_OUTCOME_PARTITION" in {i["code"] for i in report["issues"]}


@pytest.mark.parametrize("change,code", [
    ({"sha256": "0" * 64}, "HASH_MISMATCH"),
    ({"bytes": 1}, "BYTE_COUNT_MISMATCH"),
    ({"identity": {"part_id": 20202, "history_as_of_part": 20243, "row_count": 1}}, "METADATA_PART_MISMATCH"),
    ({"identity": {"part_id": 20201, "history_as_of_part": 20243, "row_count": 2}}, "METADATA_ROW_COUNT_MISMATCH"),
])
def test_bad_metadata_blocks_the_file(complete_sources, change, code):
    write_source(complete_sources, 20201, [row()], **change)
    report = module().build_university_history(complete_sources)
    assert report["status"] == "BLOCKED"
    assert code in {i["code"] for i in report["issues"]}


def test_missing_source_cannot_be_silently_omitted(complete_sources):
    (complete_sources / "api_data/frozen_history/20201.json").unlink()
    report = module().build_university_history(complete_sources)
    assert report["status"] == "BLOCKED"
    assert report["source_file_count"] == 14
    assert "MISSING_SOURCE_FILE" in {i["code"] for i in report["issues"]}


def test_full_source_key_duplicates_rejected_but_distinct_faculties_kept(complete_sources):
    write_source(complete_sources, 20201, [row(), row(FACULTY_ID="f2")])
    assert module().build_university_history(complete_sources)["status"] == "PASS"
    write_source(complete_sources, 20201, [row(), row()])
    report = module().build_university_history(complete_sources)
    assert "DUPLICATE_SOURCE_KEY" in {i["code"] for i in report["issues"]}


def test_weighted_history_uses_only_earlier_parts_and_fallback_1_2_6():
    history = module().UniversityHistory([
        row(20201, SUM_MARKS="1600"),
        row(20221, SUM_MARKS="3200", PASS_STUDENTS="20", FAIL_STUDENTS="16"),
        row(20251, SUM_MARKS="0", PASS_STUDENTS="0", FAIL_STUDENTS="36"),
    ])
    target = pd.DataFrame({"part_id": [20251] * 3, "degree_id": ["d1", "d2", "d2"],
                           "course_id": ["c1", "c1", "unknown"]})
    actual = history.apply(target)
    assert actual.course_history_fallback_level.tolist() == [1, 2, 6]
    assert actual.course_history_effective_support.tolist() == [50, 50, 50]
    assert actual.course_history_avg_mark.tolist() == pytest.approx([72, 72, 72])
    assert actual.course_history_fail_rate.tolist() == pytest.approx([.35, .35, .35])
    assert actual.course_history_retake_rate.tolist() == pytest.approx([.2, .2, .2])
    assert actual.course_history_missing.tolist() == [0, 0, 1]
    assert not any("attempt" in c for c in actual)
    earlier = history.apply(target.assign(part_id=20201))
    assert earlier.course_history_effective_support.eq(0).all()
    assert earlier.course_history_avg_mark.isna().all()


def test_smoothing_uses_global_prior_and_effective_support():
    history = module().UniversityHistory([
        row(20201, STUDENTS_COUNT="4", REGISTER_STUDENTS_COUNT="4", PASS_STUDENTS="4",
            FAIL_STUDENTS="0", WITHDRAW_STUDENTS="0", SUM_MARKS="160", RETAKE_COUNT="0"),
        row(20201, COURSE_ID="c2", STUDENTS_COUNT="36", REGISTER_STUDENTS_COUNT="36",
            PASS_STUDENTS="36", FAIL_STUDENTS="0", WITHDRAW_STUDENTS="0",
            SUM_MARKS="2880", RETAKE_COUNT="0"),
    ])
    result = history.apply(pd.DataFrame({"part_id": [20202], "degree_id": ["d1"], "course_id": ["c1"]}))
    # Global mark=(40+720)/(1+9)=76; local=(40+20*76)/(1+20).
    assert result.course_history_avg_mark.iloc[0] == pytest.approx(1560 / 21)
    assert result.course_history_effective_support.iloc[0] == 1
    assert result.course_history_missing.iloc[0] == 1


def test_output_cannot_be_written_into_original_api_directory(complete_sources):
    with pytest.raises(ValueError, match="original"):
        module().build_university_history(complete_sources, output_dir=complete_sources / "api_data/frozen_history")


def test_experimental_ratio_policy_retains_incomplete_partition_without_fabricating_outcomes(complete_sources, tmp_path):
    write_source(complete_sources, 20201, [row(PASS_STUDENTS="29")])
    output = tmp_path / "experimental"
    report = module().build_experimental_university_history(complete_sources, output_dir=output)
    assert report["status"] == "PARTIAL"
    assert report["usable_for_b_c"] is True
    assert report["validated_row_count"] == report["source_row_count"] == 15
    assert report["quarantined_row_count"] == 0
    assert report["issue_counts"]["UNRESOLVED_OUTCOME_PARTITION"] == 1
    artifact = json.loads((output / "university_history_experimental.json").read_text())
    assert artifact["rows"][0]["PASS_STUDENTS"] == 29
    assert artifact["rows"][0]["FAIL_STUDENTS"] == 6
    assert artifact["source_manifest_sha256"] == report["source_manifest_sha256"]
    history = module().UniversityHistory(artifact["rows"], allow_incomplete_outcomes=True)
    result = history.apply(pd.DataFrame({"part_id": [20202], "degree_id": ["d1"], "course_id": ["c1"]}))
    assert result.course_history_avg_mark.iloc[0] == 60
    assert result.course_history_fail_rate.iloc[0] == pytest.approx(6 / 40)
    assert result.course_history_retake_rate.iloc[0] == pytest.approx(8 / 40)


def test_experimental_history_quarantines_missing_mark_row_and_keeps_valid_same_file(complete_sources, tmp_path):
    write_source(complete_sources, 20201, [row(SUM_MARKS=None), row(COURSE_ID="valid")])
    output = tmp_path / "experimental"
    report = module().build_experimental_university_history(complete_sources, output_dir=output)
    assert report["status"] == "PARTIAL" and report["usable_for_b_c"]
    assert report["source_file_count"] == report["accepted_file_count"] == 15
    assert report["source_row_count"] == 16
    assert report["validated_row_count"] == 15
    assert report["quarantined_row_count"] == 1
    artifact = json.loads((output / "university_history_experimental.json").read_text())
    assert all(r["SUM_MARKS"] is not None for r in artifact["rows"])
    assert any(r["COURSE_ID"] == "valid" and r["PART_ID"] == 20201 for r in artifact["rows"])
    assert report["sources"][0]["quarantined_row_indices"] == [0]


def test_experimental_history_never_sums_ambiguous_cross_faculty_cohorts(complete_sources, tmp_path):
    write_source(complete_sources, 20201, [row(), row(FACULTY_ID="f2", SUM_MARKS="2000"),
                                         row(COURSE_ID="unambiguous")])
    output = tmp_path / "experimental"
    report = module().build_experimental_university_history(complete_sources, output_dir=output)
    assert report["usable_for_b_c"] and report["status"] == "PARTIAL"
    assert report["ambiguous_faculty_group_count"] == 1
    assert report["quarantined_row_count"] == 2
    assert report["validated_row_count"] == 15
    assert report["sources"][0]["quarantined_row_indices"] == [0, 1]
    artifact = json.loads((output / "university_history_experimental.json").read_text())
    assert not any(r["PART_ID"] == 20201 and r["COURSE_ID"] == "c1" for r in artifact["rows"])
    assert report["compatibility"]["faculty_overlap_policy"] == "quarantine_all_rows_in_ambiguous_degree_course_part_group"


@pytest.mark.parametrize("mutation", ["hash", "missing"])
def test_experimental_row_quarantine_never_relaxes_source_provenance(complete_sources, mutation):
    if mutation == "hash":
        write_source(complete_sources, 20201, [row()], sha256="0" * 64)
    else:
        (complete_sources / "api_data/frozen_history/20201.json").unlink()
    report = module().build_experimental_university_history(complete_sources)
    assert report["status"] == "BLOCKED" and report["usable_for_b_c"] is False
    assert report["rejected_file_count"] == 1


def test_experimental_history_explicit_partition_policy_preserves_strict_constructor():
    rows = [row(PASS_STUDENTS="29")]
    with pytest.raises(ValueError, match="UNRESOLVED_OUTCOME_PARTITION"):
        module().UniversityHistory(rows)
    history = module().UniversityHistory(rows, allow_incomplete_outcomes=True)
    targets = pd.DataFrame({"part_id": [20201, 20202], "degree_id": ["d1", "d1"],
                            "course_id": ["c1", "c1"]})
    result = history.apply(targets)
    assert result.course_history_effective_support.tolist() == [0, 10]
    assert np.isnan(result.course_history_avg_mark.iloc[0])
    assert result.course_history_avg_mark.iloc[1] == 60


def test_experimental_output_cannot_mutate_original_archives(complete_sources):
    with pytest.raises(ValueError, match="original"):
        module().build_experimental_university_history(
            complete_sources, output_dir=complete_sources / "api_data/frozen_history")
