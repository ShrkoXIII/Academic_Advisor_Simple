"""Rebuild the authorized V2 cleaning policy and audit V1 without changing it."""
import contextlib
import importlib
import io
import json
from pathlib import Path
import types
import zipfile

import pandas as pd
from pandas.testing import assert_frame_equal

from src import paths
from src.data.cleaning_utils import clean_column_names, clean_id_columns
from scripts.verify_data_features_v2 import STAGES, describe, signature


REPORT = paths.PROJECT_ROOT / "reports/data_features_v2_20260921/cleaning_policy_resolution"


def audit_policy():
    courses = clean_column_names(pd.read_parquet(paths.STUDENT_COURSE_PATH))
    courses = clean_id_columns(courses, ["student_id", "course_id"])
    courses["part_id"] = pd.to_numeric(courses.part_id, errors="coerce").astype("Int64")
    registered = courses.register_status.astype("string").str.strip().str.upper().isin(["R", "E"])
    missing_course = registered & courses.course_id.isna()
    missing_part = registered & courses.part_id.isna()
    missing = courses[missing_course | missing_part]
    status = clean_column_names(pd.read_parquet(paths.STUDENT_STATUS_PATH))
    status = clean_id_columns(status, ["student_id"])
    status["part_id"] = pd.to_numeric(status.part_id).astype("Int64")
    invalid = status[status.part_id.gt(20193) & status.part_id.mod(10).eq(4)]
    return {
        "course_scope": "R/E registrations, after key normalization and before key validation",
        "missing_course_id_rows": int(missing_course.sum()),
        "missing_part_id_rows": int(missing_part.sum()),
        "both_missing_rows": int((missing_course & missing_part).sum()),
        "unique_course_rows_removed": len(missing),
        "invalid_semester_4_rows": len(invalid),
        "invalid_part_ids": sorted(invalid.part_id.unique().astype(int).tolist()),
        "invalid_parts_distribution": {str(k): int(v) for k, v in invalid.part_id.value_counts().sort_index().items()},
        "course_affected_students": int(missing.student_id.nunique()),
        "status_affected_students": int(invalid.student_id.nunique()),
        "affected_students_union": int(pd.concat([missing.student_id, invalid.student_id]).nunique()),
        "missing_key_rows": json.loads(missing[["student_course_id", "student_id", "course_id", "part_id"]].to_json(orient="records")),
        "invalid_status_rows": json.loads(invalid[["student_status_id", "student_id", "part_id"]].to_json(orient="records")),
    }


def compare_tables(old, new):
    if "student_course_id" in old:
        keys = ["student_course_id"]
    elif "student_status_id" in old:
        keys = ["student_status_id"]
    elif "degree_course_id" in old:
        keys = ["degree_course_id"]
    elif "rule" in old:
        keys = ["student_id", "scope", "rule"]
    else:
        keys = ["student_id"]
    left, right = old.set_index(keys), new.set_index(keys)
    if not left.index.is_unique or not right.index.is_unique:
        raise ValueError(f"Non-unique comparison keys: {keys}")
    common = left.index.intersection(right.index)
    removed, added = left.index.difference(right.index), right.index.difference(left.index)
    columns = old.columns.intersection(new.columns).difference(keys)
    a, b = left.loc[common, columns], right.loc[common, columns]
    changed = {}
    for col in columns:
        same = a[col].eq(b[col]).fillna(False) | (a[col].isna() & b[col].isna())
        count = int((~same).sum())
        if count:
            changed[col] = count
    return {
        "v1": describe(old), "v2": describe(new), "keys": keys,
        "removed_rows": len(removed), "added_rows": len(added), "common_rows": len(common),
        "changed_common_values": changed,
        "dtype_changes": {c: [str(old[c].dtype), str(new[c].dtype)] for c in columns if old[c].dtype != new[c].dtype},
        "columns_equal": old.columns.tolist() == new.columns.tolist(),
    }


def verify_policy_only():
    """Old cleaner + independently filtered raw must equal new persisted output."""
    results = {}
    for name, raw_path, out_path in [
        ("clean_student_course", paths.STUDENT_COURSE_PATH, paths.CLEAN_STUDENT_COURSE_PATH_V2),
        ("clean_student_status", paths.STUDENT_STATUS_PATH, paths.CLEAN_STUDENT_STATUS_PATH_V2),
    ]:
        with zipfile.ZipFile(REPORT / "before_policy.zip") as archive:
            source = archive.read(f"src/data/{name}.py").decode("utf-8")
        old_module = types.ModuleType("policy_reference_" + name)
        exec(compile(source, "before_policy/" + name + ".py", "exec"), old_module.__dict__)
        raw = pd.read_parquet(raw_path)
        normalized = clean_column_names(raw)
        parts = pd.to_numeric(normalized.part_id, errors="coerce")
        if name == "clean_student_course":
            ids = clean_id_columns(normalized, ["course_id"])
            keep = ids.course_id.notna() & parts.notna()
        else:
            keep = ~parts.mod(10).eq(4)
        reference = getattr(old_module, name)(raw.loc[keep].copy())
        buffer = io.BytesIO()
        reference.to_parquet(buffer, index=False)
        buffer.seek(0)
        assert_frame_equal(pd.read_parquet(buffer), pd.read_parquet(out_path), check_exact=True)
        results[name] = "Exact match to pre-policy cleaner with only authorized raw-row exclusions"
    return results


def main():
    result_path = REPORT / "pipeline_verification.json"
    if result_path.exists():
        raise FileExistsError("This audited rebuild already completed; preserve its evidence.")
    if not (REPORT / "before_policy.zip").exists():
        raise FileNotFoundError("A pre-policy source/V2 snapshot is required before rebuilding.")
    outputs = {getattr(paths, n + "_V2").resolve() for _, _, names in STAGES for n in names}
    produced = set()
    reads, writes = [], []
    original_read, original_write = pd.read_parquet, pd.DataFrame.to_parquet

    def read(path, *args, **kwargs):
        target = Path(path).resolve()
        if not target.is_relative_to(paths.RAW_DIR) and target not in produced:
            raise AssertionError(f"Not raw or an output of this V2 run: {target}")
        reads.append(str(target.relative_to(paths.PROJECT_ROOT)))
        return original_read(path, *args, **kwargs)

    def write(frame, path, *args, **kwargs):
        target = Path(path).resolve()
        if target not in outputs:
            raise AssertionError(f"Not an authorized V2 output: {target}")
        writes.append(str(target.relative_to(paths.PROJECT_ROOT)))
        return original_write(frame, path, *args, **kwargs)

    result = {"policy_audit": audit_policy(), "stages": []}
    with (REPORT / "policy_audit.json").open("x", encoding="utf-8") as stream:
        json.dump(result["policy_audit"], stream, indent=2, ensure_ascii=False)
    pd.read_parquet, pd.DataFrame.to_parquet = read, write
    try:
        for stage, _, names in [STAGES[2], STAGES[1], STAGES[0], *STAGES[3:]]:
            print("Running", stage, flush=True)
            with (REPORT / (stage.rsplit(".", 1)[-1] + ".log")).open("x", encoding="utf-8") as log:
                with contextlib.redirect_stdout(log):
                    importlib.import_module(stage).main()
            for name in names:
                output = getattr(paths, name + "_V2").resolve()
                assert output.is_file(), output
                produced.add(output)
            result["stages"].append({"module": stage, "status": "PASS"})
    finally:
        pd.read_parquet, pd.DataFrame.to_parquet = original_read, original_write
        (REPORT / "io_trace.json").write_text(json.dumps({"reads": reads, "writes": writes}, indent=2), encoding="utf-8")

    result["policy_only_reference"] = verify_policy_only()
    result["comparisons"] = {}
    for _, _, names in STAGES:
        for name in names:
            old, new = getattr(paths, name), getattr(paths, name + "_V2")
            if new.suffix == ".parquet":
                result["comparisons"][name] = compare_tables(pd.read_parquet(old), pd.read_parquet(new))
    manifest = json.loads((REPORT / "before_manifest.json").read_text(encoding="utf-8"))
    result["protected_original_changes"] = [
        name for name, before in manifest.items()
        if (paths.PROJECT_ROOT / name).resolve() not in outputs
        and (not (paths.PROJECT_ROOT / name).is_file() or signature(paths.PROJECT_ROOT / name) != before)
    ]
    with result_path.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False)
    print("Completed stages:", len(result["stages"]), "Protected changes:", result["protected_original_changes"])
    for name, entry in result["comparisons"].items():
        print(name, entry["v1"]["rows"], "->", entry["v2"]["rows"], "added", entry["added_rows"], "removed", entry["removed_rows"], "changed", entry["changed_common_values"])


if __name__ == "__main__":
    main()
