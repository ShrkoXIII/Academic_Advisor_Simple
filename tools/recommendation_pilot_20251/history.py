"""Isolated university aggregate audit and point-in-time 1/2/6 history.

This contract deliberately omits historical attempt averages. It must never
be passed to the original 47-feature model. Original data and bundles remain
read-only; diagnostic output is created exclusively in a separate directory.
"""
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.features.temporal_features import temporal_weight
from src.paths import academic_part
from .adapter import HISTORY_AS_OF_PART, PILOT_ROOT


EXPECTED_PARTS = tuple(year * 10 + term for year in range(2020, 2025) for term in (1, 2, 3))
IDENTIFIER_FIELDS = ("DEGREE_ID", "COURSE_ID", "FACULTY_ID")
COUNT_FIELDS = ("STUDENTS_COUNT", "REGISTER_STUDENTS_COUNT", "PASS_STUDENTS",
                "FAIL_STUDENTS", "WITHDRAW_STUDENTS", "RETAKE_COUNT")
NUMBER_FIELDS = (*COUNT_FIELDS, "SUM_MARKS", "COURSE_CREDITS")
OUTPUT_COLUMNS = ("course_history_avg_mark", "course_history_fail_rate",
                  "course_history_retake_rate", "course_history_effective_support",
                  "course_history_fallback_level", "course_history_missing")
REMOVED_FEATURES = ("course_history_avg_attempt", "plan_credit_weighted_avg_attempt",
                    "peer_credit_weighted_avg_attempt")


def _issue(code, file, *, row_index=None, field=None, severity="error"):
    result = {"code": code, "file": file, "severity": severity}
    if row_index is not None:
        result["row_index"] = int(row_index)
    if field is not None:
        result["field"] = field
    return result


def _number(value, *, integer=False):
    if value is None or isinstance(value, (bool, dict, list)):
        raise ValueError("INVALID_NUMBER")
    try:
        number = Decimal(str(value))
        if (not number.is_finite() or number < 0
                or (integer and number != number.to_integral_value())):
            raise ValueError("INVALID_NUMBER")
        converted = int(number) if integer else float(number)
        if not integer and not np.isfinite(converted):
            raise ValueError("INVALID_NUMBER")
        return converted
    except (InvalidOperation, TypeError, OverflowError):
        raise ValueError("INVALID_NUMBER") from None


def _validate_rows(rows, file, expected_part=None, *, allow_incomplete_outcomes=False,
                   retain_row_indices=False):
    issues, validated, keys = [], [], set()
    for index, source in enumerate(rows):
        if not isinstance(source, dict):
            issues.append(_issue("INVALID_AGGREGATE_ROW", file, row_index=index))
            continue
        current, start = {}, len(issues)
        for field in IDENTIFIER_FIELDS:
            value = source.get(field)
            if value is None or isinstance(value, (bool, dict, list)) or not str(value).strip():
                issues.append(_issue("INVALID_SOURCE_KEY", file, row_index=index, field=field))
            else:
                current[field] = str(value).strip()
        try:
            part = academic_part(_number(source.get("PART_ID"), integer=True))
            current["PART_ID"] = part
            if expected_part is not None and part != expected_part:
                issues.append(_issue("SOURCE_PART_MISMATCH", file, row_index=index, field="PART_ID"))
        except ValueError:
            issues.append(_issue("INVALID_SOURCE_PART", file, row_index=index, field="PART_ID"))
        for field in NUMBER_FIELDS:
            try:
                current[field] = _number(source.get(field), integer=field in COUNT_FIELDS)
            except ValueError:
                issues.append(_issue("INVALID_NUMBER", file, row_index=index, field=field))
        if "FAIL_STUDENTS_WITH_W" in source:
            try:
                current["FAIL_STUDENTS_WITH_W"] = _number(source["FAIL_STUDENTS_WITH_W"], integer=True)
            except ValueError:
                issues.append(_issue("INVALID_NUMBER", file, row_index=index, field="FAIL_STUDENTS_WITH_W"))
        count = current.get("STUDENTS_COUNT")
        if count is not None:
            if count <= 0:
                issues.append(_issue("INVALID_DENOMINATOR", file, row_index=index, field="STUDENTS_COUNT"))
            for field in (*COUNT_FIELDS[1:], "FAIL_STUDENTS_WITH_W"):
                if field in current and current[field] > count:
                    issues.append(_issue("COUNT_EXCEEDS_STUDENTS", file, row_index=index, field=field))
            partition = ("PASS_STUDENTS", "FAIL_STUDENTS", "WITHDRAW_STUDENTS")
            if all(field in current for field in partition):
                total = sum(current[field] for field in partition)
                if total > count:
                    issues.append(_issue("OUTCOME_COUNTS_EXCEED_STUDENTS", file, row_index=index))
                elif total < count:
                    # A residual is unresolved source semantics, not proof of
                    # corrupt counts. Never assign those students an outcome.
                    issues.append(_issue("UNRESOLVED_OUTCOME_PARTITION", file,
                                         row_index=index, severity=("warning" if allow_incomplete_outcomes
                                                                    else "unresolved")))
            if "SUM_MARKS" in current and current["SUM_MARKS"] > count * 100:
                issues.append(_issue("MARK_SUM_OUT_OF_RANGE", file, row_index=index, field="SUM_MARKS"))
        key_fields = (*IDENTIFIER_FIELDS, "PART_ID")
        if all(field in current for field in key_fields):
            key = tuple(current[field] for field in key_fields)
            if key in keys:
                issues.append(_issue("DUPLICATE_SOURCE_KEY", file, row_index=index))
            keys.add(key)
        if not any(issue["severity"] != "warning" for issue in issues[start:]):
            if retain_row_indices:
                current["_source_row_index"] = index
                current["_source_file"] = file
            validated.append(current)
    return validated, issues


def _read_source(path, part, *, allow_incomplete_outcomes=False, retain_row_indices=False):
    """Return canonical rows, safe audit information and every source issue."""
    issues, raw_rows = [], []
    summary = {"file": path.name, "part_id": part, "row_count": 0}
    try:
        raw = path.read_bytes()
    except OSError:
        return [], summary, [_issue("MISSING_SOURCE_FILE", path.name)]
    summary.update({"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)})
    try:
        payload = json.loads(raw.decode("utf-8-sig"))
        if (not isinstance(payload, dict) or payload.get("success") is not True
                or not isinstance(payload.get("data"), dict)
                or not isinstance(payload["data"].get("CoursesStatistsic"), list)):
            raise ValueError
        raw_rows = payload["data"]["CoursesStatistsic"]
        summary["row_count"] = len(raw_rows)
        if not raw_rows:
            issues.append(_issue("EMPTY_SOURCE_HISTORY", path.name))
    except (ValueError, UnicodeError):
        issues.append(_issue("INVALID_HISTORY_ENVELOPE", path.name))
    try:
        meta = json.loads(path.with_suffix(".meta.json").read_text(encoding="utf-8-sig"))
        if not isinstance(meta, dict):
            raise ValueError
        if meta.get("sha256") != summary["sha256"]:
            issues.append(_issue("HASH_MISMATCH", path.name))
        if meta.get("bytes") != len(raw):
            issues.append(_issue("BYTE_COUNT_MISMATCH", path.name))
        identity = meta.get("identity")
        if not isinstance(identity, dict):
            raise ValueError
        if identity.get("part_id") != part:
            issues.append(_issue("METADATA_PART_MISMATCH", path.name))
        if identity.get("history_as_of_part") != HISTORY_AS_OF_PART:
            issues.append(_issue("METADATA_CUTOFF_MISMATCH", path.name))
        if identity.get("row_count") != len(raw_rows):
            issues.append(_issue("METADATA_ROW_COUNT_MISMATCH", path.name))
        if meta.get("kind") != "history" or meta.get("source") != "university_frozen_history_api":
            issues.append(_issue("METADATA_SOURCE_MISMATCH", path.name))
    except (OSError, ValueError, UnicodeError):
        issues.append(_issue("INVALID_OR_MISSING_METADATA", path.name))
    rows, row_issues = _validate_rows(
        raw_rows, path.name, expected_part=part,
        allow_incomplete_outcomes=allow_incomplete_outcomes,
        retain_row_indices=retain_row_indices)
    issues.extend(row_issues)
    return rows, summary, issues


def build_university_history(root=PILOT_ROOT, output_dir=None, *, snapshot_id="after_backend_fix"):
    """Audit all fifteen local parts; incomplete history cannot serve B/C.

    Rejected files have definite schema, provenance or numeric errors.
    Unresolved files have incomplete outcome partitions requiring clarification.
    Both are withheld entirely from the diagnostic validated artifact.
    """
    from .snapshots import api_data_root
    root = Path(root)
    if output_dir is not None:
        output_dir = Path(output_dir).resolve()
        for original in ((root / "api_data").resolve(), (root / "snapshots").resolve(), (PILOT_ROOT / "api_data").resolve(), (PILOT_ROOT / "snapshots").resolve()):
            if output_dir == original or output_dir.is_relative_to(original):
                raise ValueError("History output must be separate from original API data.")
    directory = api_data_root(root, snapshot_id) / "frozen_history"
    sources, issues, validated = [], [], []
    for part in EXPECTED_PARTS:
        rows, source, file_issues = _read_source(directory / f"{part}.json", part)
        source["status"] = ("REJECTED" if any(i["severity"] == "error" for i in file_issues)
                            else "UNRESOLVED" if file_issues else "ACCEPTED")
        sources.append(source)
        issues.extend(file_issues)
        if source["status"] == "ACCEPTED":
            validated.extend(rows)
    for path in directory.glob("*.json"):
        if not path.name.endswith(".meta.json") and path.stem not in {str(p) for p in EXPECTED_PARTS}:
            issues.append(_issue("UNEXPECTED_SOURCE_FILE", path.name))
    accepted = sum(s["status"] == "ACCEPTED" for s in sources)
    compatible = accepted == len(EXPECTED_PARTS) and not issues
    report = {
        "phase": 2, "status": "PASS" if compatible else "BLOCKED",
        "as_of_part": HISTORY_AS_OF_PART, "usable_for_b_c": compatible,
        "source_file_count": sum("sha256" in s for s in sources),
        "expected_file_count": len(EXPECTED_PARTS), "accepted_file_count": accepted,
        "rejected_file_count": sum(s["status"] == "REJECTED" for s in sources),
        "unresolved_file_count": sum(s["status"] == "UNRESOLVED" for s in sources),
        "source_row_count": sum(s["row_count"] for s in sources),
        "validated_row_count": len(validated),
        "source_hashes": {s["file"]: s["sha256"] for s in sources if "sha256" in s},
        "issues": issues, "issue_counts": dict(Counter(i["code"] for i in issues)),
        "sources": sources,
        "compatibility": {
            "requires_retraining": True, "original_47_feature_model_compatible": False,
            "removed_features": list(REMOVED_FEATURES), "individual_attempt_number_retained": True,
            "fallback_levels": [1, 2, 6], "smoothing_k": 20, "min_support": 20,
            "temporal_weight": {"before_2022": .25, "from_2022": 1.0},
            "prediction_history_rule": "source PART_ID strictly less than each target part",
            "university_fail_rate": "FAIL_STUDENTS / STUDENTS_COUNT; withdrawals excluded from numerator",
            "original_failure_target": "final_mark < 50 on cleaned finalized pass/fail records",
            "original_cleaning": "src/data/clean_student_course.py keeps F, FE, FA, P; no withdrawal label",
            "original_population_equivalence_proven": False,
            "aggregate_points_available": False,
            "faculty_rows": "distinct faculty source keys retained; L1/L2/global sum source rows",
            "plan_requirement_history_available": False,
        },
        "limitations": [
            "University all-student denominator differs from the original cleaned pass/fail population.",
            "An incomplete outcome partition has unresolved semantics; missing marks are never imputed.",
            "No conversion of average marks into average points is supported.",
        ],
    }
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        artifact = {"format_version": 1, "as_of_part": HISTORY_AS_OF_PART,
                    "usable_for_b_c": compatible, "source_hashes": report["source_hashes"],
                    "accepted_parts": [s["part_id"] for s in sources if s["status"] == "ACCEPTED"],
                    "rows": validated}
        for name, value in (("university_history_validated.json", artifact), ("history_report.json", report)):
            with (output_dir / name).open("x", encoding="utf-8") as stream:
                json.dump(value, stream, indent=2, allow_nan=False)
    return report


def build_experimental_university_history(root=PILOT_ROOT, output_dir=None, *, snapshot_id="after_backend_fix"):
    """Audit a separate, explicitly partial history for retrained B/C models.

    All expected files still require intact envelopes, hashes and metadata.
    Invalid aggregate rows are quarantined without imputing any values. A
    nonexhaustive outcome partition does not invalidate the three authorized
    all-student ratios. Ambiguous cross-faculty cohorts are excluded entirely:
    neither their independence nor a deduplication rule is assumed.
    """
    from .snapshots import api_data_root
    root = Path(root)
    if output_dir is not None:
        output_dir = Path(output_dir).resolve()
        for original in ((root / "api_data").resolve(), (root / "snapshots").resolve(), (PILOT_ROOT / "api_data").resolve(), (PILOT_ROOT / "snapshots").resolve()):
            if output_dir == original or output_dir.is_relative_to(original):
                raise ValueError("History output must be separate from original API data.")
    directory = api_data_root(root, snapshot_id) / "frozen_history"
    sources, issues, candidates = [], [], []
    for part in EXPECTED_PARTS:
        rows, source, file_issues = _read_source(
            directory / f"{part}.json", part,
            allow_incomplete_outcomes=True, retain_row_indices=True)
        # Duplicate full keys make both duplicate versions ambiguous. They are
        # a file-level failure rather than silently retaining the first row.
        fatal = any("row_index" not in issue or issue["code"] == "DUPLICATE_SOURCE_KEY"
                    for issue in file_issues)
        source["status"] = "REJECTED" if fatal else "ACCEPTED"
        for issue in file_issues:
            issue["blocks_prediction"] = fatal
            issue["disposition"] = ("REJECTED_SOURCE_FILE" if fatal else
                                    "RATIO_DEFINITIONS_AVAILABLE" if issue["severity"] == "warning"
                                    else "QUARANTINED_ROW")
        sources.append(source)
        issues.extend(file_issues)
        if not fatal:
            candidates.extend(rows)
    for path in directory.glob("*.json"):
        if not path.name.endswith(".meta.json") and path.stem not in {str(p) for p in EXPECTED_PARTS}:
            issues.append({**_issue("UNEXPECTED_SOURCE_FILE", path.name), "blocks_prediction": True,
                           "disposition": "REJECTED_SOURCE_FILE"})

    groups = defaultdict(list)
    for row in candidates:
        groups[(row["DEGREE_ID"], row["COURSE_ID"], row["PART_ID"])].append(row)
    ambiguous = {key for key, group in groups.items()
                 if len({row["FACULTY_ID"] for row in group}) > 1}
    validated = []
    for key, group in groups.items():
        if key not in ambiguous:
            validated.extend(group)
            continue
        for row in group:
            issues.append({**_issue("AMBIGUOUS_FACULTY_OVERLAP", row["_source_file"],
                                    row_index=row["_source_row_index"], field="FACULTY_ID",
                                    severity="warning"),
                           "blocks_prediction": False, "disposition": "QUARANTINED_ROW"})
    # Preserve stable source/row ordering for identical training and serving
    # fingerprints. Audit metadata is retained separately from feature values.
    validated.sort(key=lambda row: (row["PART_ID"], row["_source_row_index"]))
    for source in sources:
        retained = {row["_source_row_index"] for row in validated if row["_source_file"] == source["file"]}
        source["retained_row_count"] = len(retained)
        source["quarantined_row_indices"] = sorted(set(range(source["row_count"])) - retained)
        source["quarantined_row_count"] = len(source["quarantined_row_indices"])
    hashes = {source["file"]: source["sha256"] for source in sources if "sha256" in source}
    manifest_sha256 = hashlib.sha256(json.dumps(hashes, sort_keys=True,
                                               separators=(",", ":")).encode()).hexdigest()
    rows_sha256 = hashlib.sha256(json.dumps(validated, sort_keys=True,
                                           separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    accepted = sum(source["status"] == "ACCEPTED" for source in sources)
    usable = (accepted == len(EXPECTED_PARTS) and bool(validated)
              and not any(issue["blocks_prediction"] for issue in issues))
    source_row_count = sum(source["row_count"] for source in sources)
    compatibility = {
        "requires_retraining": True, "original_47_feature_model_compatible": False,
        "removed_features": list(REMOVED_FEATURES), "individual_attempt_number_retained": True,
        "fallback_levels": [1, 2, 6], "smoothing_k": 20, "min_support": 20,
        "temporal_weight": {"before_2022": .25, "from_2022": 1.0},
        "prediction_history_rule": "source PART_ID strictly less than each target part",
        "university_fail_rate": "FAIL_STUDENTS / STUDENTS_COUNT; withdrawals excluded from numerator",
        "university_avg_mark": "SUM_MARKS / STUDENTS_COUNT",
        "university_retake_rate": "RETAKE_COUNT / STUDENTS_COUNT",
        "outcome_partition_policy": "retain_nonexhaustive_partition_with_warning_without_assigning_residual",
        "faculty_overlap_policy": "quarantine_all_rows_in_ambiguous_degree_course_part_group",
        "original_population_equivalence_proven": False,
        "aggregate_points_available": False, "plan_requirement_history_available": False,
    }
    report = {
        "phase": 2, "status": ("PARTIAL" if issues else "PASS") if usable else "BLOCKED",
        "history_policy_version": "audited_row_quarantine_v1",
        "as_of_part": HISTORY_AS_OF_PART, "usable_for_b_c": usable,
        "source_file_count": len(hashes), "expected_file_count": len(EXPECTED_PARTS),
        "accepted_file_count": accepted, "rejected_file_count": len(EXPECTED_PARTS) - accepted,
        "source_row_count": source_row_count, "validated_row_count": len(validated),
        "quarantined_row_count": source_row_count - len(validated),
        "retained_row_fraction": len(validated) / source_row_count if source_row_count else 0,
        "ambiguous_faculty_group_count": len(ambiguous),
        "source_hashes": hashes, "source_manifest_sha256": manifest_sha256,
        "usable_rows_sha256": rows_sha256,
        "issues": issues, "issue_counts": dict(Counter(issue["code"] for issue in issues)),
        "sources": sources, "compatibility": compatibility,
        "limitations": [
            "Partial experimental reference history; quarantined rows are excluded from every ratio and support.",
            "Nonexhaustive outcome categories are disclosed; residual students are never assigned an outcome.",
            "Faculty cohort independence is unproven; ambiguous degree/course/part groups are withheld.",
            "All-student ratios differ from the original cleaned finalized pass/fail population.",
            "No aggregate average points, attempt averages or requirement-type history are fabricated.",
        ],
    }
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        artifact = {"format_version": 2, "history_policy_version": report["history_policy_version"],
                    "as_of_part": HISTORY_AS_OF_PART, "usable_for_b_c": usable,
                    "source_hashes": hashes, "source_manifest_sha256": manifest_sha256,
                    "usable_rows_sha256": rows_sha256, "compatibility": compatibility,
                    "coverage": {key: report[key] for key in
                                 ("source_row_count", "validated_row_count", "quarantined_row_count",
                                  "retained_row_fraction", "ambiguous_faculty_group_count")},
                    "accepted_parts": [source["part_id"] for source in sources
                                       if source["status"] == "ACCEPTED"],
                    "rows": validated}
        for name, value in (("university_history_experimental.json", artifact),
                            ("experimental_history_report.json", report)):
            with (output_dir / name).open("x", encoding="utf-8") as stream:
                json.dump(value, stream, indent=2, allow_nan=False)
    return report


class UniversityHistory:
    """Weighted, smoothed aggregates using exclusively earlier source parts."""

    def __init__(self, rows, *, smoothing_k=20.0, min_support=20.0,
                 allow_incomplete_outcomes=False):
        if isinstance(rows, pd.DataFrame):
            rows = rows.to_dict("records")
        canonical, issues = _validate_rows(list(rows), "in_memory_history",
                                          allow_incomplete_outcomes=allow_incomplete_outcomes)
        blocking = [issue for issue in issues if issue["severity"] != "warning"]
        if blocking:
            raise ValueError("Invalid/unresolved university aggregates: " + ", ".join(sorted({i["code"] for i in issues})))
        if not np.isfinite(smoothing_k) or smoothing_k <= 0 or not np.isfinite(min_support) or min_support < 0:
            raise ValueError("Invalid history smoothing/support parameters.")
        self.rows = pd.DataFrame(canonical)
        self.warnings = issues
        self.smoothing_k, self.min_support = float(smoothing_k), float(min_support)
        self.as_of_part = int(self.rows.PART_ID.max()) if len(self.rows) else None

    def apply(self, frame):
        """Select L1, then L2, then global; never infer unsupported attempts."""
        required = {"part_id", "degree_id", "course_id"}
        if not required.issubset(frame.columns):
            raise ValueError("History target rows require part_id, degree_id, course_id.")
        parts = frame.part_id.map(lambda value: academic_part(_number(value, integer=True)))
        identifiers = frame[["degree_id", "course_id"]].astype("string")
        for column in identifiers:
            identifiers[column] = identifiers[column].str.strip()
            if identifiers[column].isna().any() or identifiers[column].eq("").any():
                raise ValueError("History target keys cannot be missing.")
        results = np.full((len(frame), len(OUTPUT_COLUMNS)), np.nan)
        results[:, 3:] = [0.0, 6, 1]
        sum_columns = ["_support", "_mark", "_fail", "_retake"]
        # Aggregate once per target part, rather than once per course/plan row.
        for part in parts.unique():
            positions = np.flatnonzero(parts.to_numpy() == part)
            target = identifiers.iloc[positions]
            prefix = self.rows.loc[self.rows.PART_ID.lt(part)] if len(self.rows) else self.rows
            if prefix.empty:
                continue
            weights = temporal_weight(prefix.PART_ID)
            weighted = prefix.assign(_support=prefix.STUDENTS_COUNT * weights,
                                     _mark=prefix.SUM_MARKS * weights,
                                     _fail=prefix.FAIL_STUDENTS * weights,
                                     _retake=prefix.RETAKE_COUNT * weights)
            sums = weighted[sum_columns].sum().to_numpy(dtype=float)
            global_rates = sums[1:] / sums[0]
            values = np.tile([*global_rates, sums[0], 6, 1], (len(target), 1))
            # Apply course-only first, then override with the more specific L1.
            for level, keys in ((2, ["COURSE_ID"]), (1, ["DEGREE_ID", "COURSE_ID"])):
                table = weighted.groupby(keys, sort=False)[sum_columns].sum()
                lookup = (target.course_id if level == 2 else pd.MultiIndex.from_arrays(
                    [target.degree_id, target.course_id], names=keys))
                local = table.reindex(lookup).to_numpy(dtype=float)
                available = np.isfinite(local[:, 0])
                support = local[available, 0]
                values[available, :3] = ((local[available, 1:] + self.smoothing_k * global_rates)
                                        / (support[:, None] + self.smoothing_k))
                values[available, 3] = support
                values[available, 4] = level
            values[:, 5] = (values[:, 4] >= 3) | (values[:, 3] < self.min_support)
            results[positions] = values
        result = pd.DataFrame(results, index=frame.index, columns=OUTPUT_COLUMNS)
        for column in ("course_history_fallback_level", "course_history_missing"):
            result[column] = result[column].astype("int64")
        return result
