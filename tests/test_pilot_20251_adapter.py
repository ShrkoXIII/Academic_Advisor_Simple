"""The pilot exception maps source counters literally; it is not a timing claim."""
import hashlib
import json
from decimal import Decimal

import pytest

from tools.recommendation_pilot_20251 import adapter


MAPPING = {
    "prior_total_reg_courses": "TOTAL_REG_COURSES",
    "prior_total_reg_credits": "TOTAL_REG_CREDITS",
    "prior_total_fail_courses": "TOTAL_FAIL_COURSES",
    "prior_total_fail_credits": "TOTAL_FAIL_CREDITS",
    "prior_registered_semesters": "REG_TOTAL_SEMESTERS",
}


def info():
    return {"STUDENT_ID": "student", "DEGREE_ID": "degree", "STATUS_SEMESTER_ID": "20251",
            **dict(zip(MAPPING.values(), ["31", "97.5", "7", "19.25", "9"]))}


def test_five_values_are_direct_numeric_conversions():
    original = info()
    mapped = adapter.map_student_features(original)
    assert adapter.PILOT_STUDENT_FEATURE_MAPPING == MAPPING
    for target, source in MAPPING.items():
        assert Decimal(str(mapped[target])) == Decimal(original[source])
    assert original == info()


@pytest.mark.parametrize("value", [None, "", "bad", "NaN", "inf", -1, True, [], {}])
def test_reject_invalid_source_counter(value):
    row = info()
    row["TOTAL_REG_CREDITS"] = value
    with pytest.raises(adapter.PilotInputError, match="TOTAL_REG_CREDITS"):
        adapter.map_student_features(row)


@pytest.mark.parametrize("source", MAPPING.values())
def test_missing_value_is_not_derived(source):
    row = info()
    del row[source]
    with pytest.raises(adapter.PilotInputError, match=source):
        adapter.map_student_features(row)


def test_count_must_be_integral():
    row = info()
    row["REG_TOTAL_SEMESTERS"] = "2.5"
    with pytest.raises(adapter.PilotInputError):
        adapter.map_student_features(row)


def test_identity_matches_all_three_fields():
    expected = {"student_id": "student", "degree_id": "degree", "part_id": 20251}
    adapter.validate_identity(info(), expected, required=True)
    for source in ["STUDENT_ID", "DEGREE_ID", "STATUS_SEMESTER_ID"]:
        row = info()
        row[source] = "20243" if source == "STATUS_SEMESTER_ID" else "other"
        with pytest.raises(adapter.PilotInputError):
            adapter.validate_identity(row, expected, required=True)


def test_local_response_hash_and_metadata_identity(tmp_path):
    expected = {"student_id": "student", "degree_id": "degree", "part_id": 20251}
    file = tmp_path / "student_response.json"
    raw = json.dumps({"success": True, "data": {"studentDegreeInfo": info()}}).encode()
    file.write_bytes(raw)
    meta = {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw), "identity": expected}
    file.with_suffix(".meta.json").write_text(json.dumps(meta))
    assert adapter.read_verified_json(file, expected=expected)[0]["success"] is True
    file.write_bytes(raw + b" ")
    with pytest.raises(adapter.PilotInputError, match="HASH_MISMATCH"):
        adapter.read_verified_json(file, expected=expected)


def test_metadata_mismatch_rejected_even_with_valid_hash(tmp_path):
    file = tmp_path / "response.json"
    file.write_text('{"success": true, "data": {}}')
    file.with_suffix('.meta.json').write_text(json.dumps({
        "sha256": hashlib.sha256(file.read_bytes()).hexdigest(),
        "identity": {"student_id": "other", "degree_id": "degree", "part_id": 20251}}))
    with pytest.raises(adapter.PilotInputError):
        adapter.read_verified_json(file, expected={"student_id": "student", "degree_id": "degree", "part_id": 20251})
