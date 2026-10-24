"""Strict local input adapter for the explicitly approved pilot exception.

The five counters preserve Student API values. Their pre-semester equivalence
is unproven; this module makes no leakage-free or production-readiness claim.
"""
import csv
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import re

from src import paths


PILOT_ROOT = paths.EVALUATION_DIR / "recommendation_pilot_20251"
EXPERIMENT_ROOT = PILOT_ROOT / "experiments"
TARGET_PART = 20251
HISTORY_AS_OF_PART = 20243
PILOT_STUDENT_FEATURE_MAPPING = {
    "prior_total_reg_courses": "TOTAL_REG_COURSES",
    "prior_total_reg_credits": "TOTAL_REG_CREDITS",
    "prior_total_fail_courses": "TOTAL_FAIL_COURSES",
    "prior_total_fail_credits": "TOTAL_FAIL_CREDITS",
    "prior_registered_semesters": "REG_TOTAL_SEMESTERS",
}
TIMING_LIMITATION = (
    "TOTAL_* and REG_TOTAL_SEMESTERS are copied literally by pilot authorization. "
    "Their timing equivalence to training history is unproven; they may include "
    "target-semester information. This pilot does not establish freedom from leakage."
)


class PilotInputError(ValueError):
    """Safe diagnostics contain field/code names rather than student records."""

    def __init__(self, code, field=None):
        self.code, self.field = code, field
        super().__init__(code + (": " + field if field else ""))


def numeric(value, field, *, integer=False):
    if value is None or isinstance(value, (bool, list, dict)):
        raise PilotInputError("INVALID_NUMBER", field)
    try:
        result = Decimal(str(value))
        valid = result.is_finite() and result >= 0
        if not valid or (integer and result != result.to_integral_value()):
            raise PilotInputError("INVALID_NUMBER", field)
    except (InvalidOperation, TypeError, ValueError):
        raise PilotInputError("INVALID_NUMBER", field) from None
    return int(result) if integer else result


def map_student_features(info):
    """Copy exactly the five authorized values, converting numeric types only."""
    counts = {"prior_total_reg_courses", "prior_total_fail_courses", "prior_registered_semesters"}
    return {target: numeric(info.get(source), source, integer=target in counts)
            for target, source in PILOT_STUDENT_FEATURE_MAPPING.items()}


def validate_identity(record, expected, *, required=False):
    aliases = {"student_id": ("student_id", "STUDENT_ID"),
               "degree_id": ("degree_id", "DEGREE_ID"),
               "part_id": ("part_id", "PART_ID", "STATUS_SEMESTER_ID", "SEMESTER_ID")}
    if not isinstance(record, dict):
        raise PilotInputError("INVALID_IDENTITY_SHAPE")
    for key, names in aliases.items():
        present = [name for name in names if name in record]
        if required and not present:
            raise PilotInputError("MISSING_IDENTITY", key)
        for name in present:
            value = record[name]
            if key == "part_id":
                value = numeric(value, name, integer=True)
            elif not isinstance(value, str) or not value.strip():
                raise PilotInputError("INVALID_IDENTITY", key)
            else:
                value = value.strip()
            if value != expected[key]:
                raise PilotInputError("IDENTITY_MISMATCH", key)


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_verified_json(path, *, expected=None):
    """Read local bytes, verify available metadata, never access the network."""
    path = Path(path)
    try:
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        meta_path = path.with_suffix(".meta.json")
        meta = json.loads(meta_path.read_text(encoding="utf-8-sig")) if meta_path.exists() else None
        if meta is not None:
            if not isinstance(meta, dict) or meta.get("sha256") != digest:
                raise PilotInputError("HASH_MISMATCH", path.name)
            if "bytes" in meta and meta["bytes"] != len(raw):
                raise PilotInputError("BYTE_COUNT_MISMATCH", path.name)
            if expected is not None:
                validate_identity(meta.get("identity"), expected, required=True)
        payload = json.loads(raw.decode("utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise PilotInputError("INVALID_LOCAL_FILE", path.name) from None
    if not isinstance(payload, dict) or payload.get("success") is not True or not isinstance(payload.get("data"), dict):
        raise PilotInputError("INVALID_RESPONSE", path.name)
    if expected is not None:
        validate_identity(payload, expected)
        validate_identity(payload["data"], expected)
    return payload, {"sha256": digest, "metadata_verified": meta is not None, "metadata": meta}


def read_students(root=PILOT_ROOT, *, include_reserve=False):
    """Load primary CSV identities without leaking names or other personal fields."""
    with (Path(root) / "students.csv").open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    selected, seen = [], set()
    for row in rows:
        if row.get('role') not in (('primary', 'reserve') if include_reserve else ('primary',)):
            continue
        sample = row.get("sample_id", "")
        if not re.fullmatch(r"[A-Za-z0-9_-]+", sample) or sample in seen:
            raise PilotInputError("INVALID_SAMPLE_ID")
        seen.add(sample)
        expected = {"student_id": row.get("student_id"), "degree_id": row.get("degree_id"),
                    "part_id": numeric(row.get("part_id"), "part_id", integer=True)}
        validate_identity(expected, expected, required=True)
        if expected["part_id"] != TARGET_PART or int(row.get("history_as_of_part", HISTORY_AS_OF_PART)) != HISTORY_AS_OF_PART:
            raise PilotInputError("PILOT_SEMESTER_MISMATCH")
        selected.append({"sample_id": sample, "role": row['role'], **expected,
                         "previous_gpa": float(numeric(row["previous_gpa"], "previous_gpa")),
                         "gpa_category": row.get("gpa_category"), "grade_version_id": row.get("grade_version_id")})
    if not selected:
        raise PilotInputError("NO_PRIMARY_STUDENTS")
    return selected


def load_student_inputs(student, root=PILOT_ROOT, *, snapshot_id='after_backend_fix'):
    from .snapshots import api_data_root
    expected = {key: student[key] for key in ("student_id", "degree_id", "part_id")}
    base = api_data_root(root, snapshot_id) / "students" / student["sample_id"]
    for name in ('student_response.json', 'courses_response.json'):
        if not (base / name).is_file():
            raise PilotInputError('MISSING_SNAPSHOT_RESPONSE', snapshot_id + '/' + name)
    sp, sm = read_verified_json(base / "student_response.json", expected=expected)
    cp, cm = read_verified_json(base / "courses_response.json", expected=expected)
    info = sp["data"].get("studentDegreeInfo")
    validate_identity(info, expected, required=True)
    if not cm["metadata_verified"]:
        # Courses responses have no student identity; require collector binding.
        validate_identity(cp["data"], expected, required=True)
    mapped = map_student_features(info)
    return {"identity": expected, "snapshot_id": snapshot_id, "api_snapshot_path": str(base.parent.parent),
            "student_api_response": sp, "courses_api_response": cp,
            "mapped_features": mapped, "timing_limitation": TIMING_LIMITATION,
            "fingerprints": {"student_response.json": sm["sha256"], "courses_response.json": cm["sha256"]}}
