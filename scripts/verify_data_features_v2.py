"""One-shot V2 migration verification; refuses to overwrite existing outputs.

Run from the project root with python -m scripts.verify_data_features_v2.
The pre-migration manifest/source snapshot must already exist in the report folder.
"""
import contextlib
import hashlib
import importlib
import io
import json
from pathlib import Path
import traceback
import types
import zipfile

import pandas as pd
from pandas.testing import assert_frame_equal

from src import paths


REPORT = paths.PROJECT_ROOT / "reports" / "data_features_v2_20260921"
STAGES = [
    ("src.data.clean_student_course", [], ["CLEAN_STUDENT_COURSE_PATH"]),
    ("src.data.clean_student_status", [], ["CLEAN_STUDENT_STATUS_PATH"]),
    ("src.data.clean_degree_course", [], ["CLEAN_DEGREE_COURSE_PATH"]),
    ("src.data.build_student_course_enriched", ["CLEAN_STUDENT_COURSE_PATH", "CLEAN_STUDENT_STATUS_PATH", "CLEAN_DEGREE_COURSE_PATH"], ["STUDENT_COURSE_ENRICHED_PATH"]),
    ("src.data.clean_student_diploma", ["STUDENT_COURSE_ENRICHED_PATH"], ["CLEAN_STUDENT_DIPLOMA_PATH", "STUDENT_COURSE_DIPLOMA_PATH"]),
    ("src.data.clean_outliers", ["STUDENT_COURSE_DIPLOMA_PATH"], ["STUDENT_COURSE_WITHOUT_OUTLIERS_PATH", "OUTLIER_STUDENTS_AUDIT_PATH"]),
    ("src.data.build_temporal_split", ["STUDENT_COURSE_WITHOUT_OUTLIERS_PATH"], ["TEMPORAL_TRAIN_PATH", "TEMPORAL_TEST_PATH"]),
    ("src.data.build_registration_roster", ["CLEAN_STUDENT_STATUS_PATH", "CLEAN_DEGREE_COURSE_PATH", "OUTLIER_STUDENTS_AUDIT_PATH"], ["CLEAN_REGISTRATION_ROSTER_PATH", "TEMPORAL_TRAIN_ROSTER_PATH", "TEMPORAL_TEST_ROSTER_PATH"]),
    ("src.features.build_temporal_features", ["TEMPORAL_TRAIN_PATH", "TEMPORAL_TEST_PATH", "TEMPORAL_TRAIN_ROSTER_PATH", "TEMPORAL_TEST_ROSTER_PATH"], ["TEMPORAL_TRAIN_FEATURES_PATH", "TEMPORAL_TEST_FEATURES_PATH", "COURSE_HISTORY_STATE_PATH"]),
]


def signature(path):
    with path.open("rb") as stream:
        return {"size": path.stat().st_size, "sha256": hashlib.file_digest(stream, "sha256").hexdigest()}


def describe(frame):
    return {
        "rows": len(frame),
        "unique_students": int(frame.student_id.nunique()) if "student_id" in frame else None,
        "columns": frame.columns.tolist(),
        "dtypes": {col: str(dtype) for col, dtype in frame.dtypes.items()},
        "part_id_distribution": {str(key): int(value) for key, value in frame.part_id.value_counts(dropna=False).sort_index().items()} if "part_id" in frame else {},
        "null_counts": {col: int(value) for col, value in frame.isna().sum().items()},
    }


def compare(left, right):
    keys = [key for key in ["student_course_id", "student_status_id", "degree_course_id", "student_id", "degree_id", "part_id", "course_id"] if key in left and key in right]
    a = left.sort_values(keys, kind="stable").reset_index(drop=True) if keys else left.reset_index(drop=True)
    b = right.sort_values(keys, kind="stable").reset_index(drop=True) if keys else right.reset_index(drop=True)
    try:
        assert_frame_equal(a, b, check_exact=True)
        return {"equal": True, "sort_keys": keys}
    except AssertionError as exc:
        return {"equal": False, "sort_keys": keys, "difference": str(exc)[:4000]}


def original_cleaner(name):
    # Execute the exact snapshotted pre-move function, resolving only its imports.
    import re
    with zipfile.ZipFile(REPORT / "source_before.zip") as archive:
        source = archive.read("src/" + name + ".py").decode("utf-8")
    source = re.sub(r"from cleaning_utils import", "from src.data.cleaning_utils import", source)
    source = re.sub(r"from paths import", "from src.paths import", source)
    module = types.ModuleType("migration_baseline_" + name)
    exec(compile(source, "snapshot/src/" + name + ".py", "exec"), module.__dict__)
    return getattr(module, name)


def main():
    original = json.loads((REPORT / "original_artifacts_manifest.json").read_text(encoding="utf-8"))
    outputs = [name for _, _, names in STAGES for name in names]
    existing = [str(getattr(paths, name + "_V2")) for name in outputs if getattr(paths, name + "_V2").exists()]
    if existing:
        raise FileExistsError(f"Refusing to overwrite existing V2 outputs: {existing}")
    results = {"stages": [], "comparisons": {}, "baseline_comparisons": {}}
    for stage, inputs, names in STAGES:
        missing = [name + "_V2" for name in inputs if not getattr(paths, name + "_V2").is_file()]
        entry = {"module": stage, "inputs": inputs, "outputs": names}
        results["stages"].append(entry)
        if missing:
            entry.update(status="blocked", missing=missing)
            print(stage, "BLOCKED", missing, flush=True)
            continue
        with (REPORT / (stage.rsplit(".", 1)[-1] + ".log")).open("x", encoding="utf-8") as log:
            try:
                with contextlib.redirect_stdout(log):
                    importlib.import_module(stage).main()
                entry["status"] = "generated"
            except Exception as exc:
                traceback.print_exc(file=log)
                entry.update(status="failed", error=f"{type(exc).__name__}: {exc}")
        print(stage, entry["status"], entry.get("error", ""), flush=True)

    # Diploma cleaning itself depends only on raw data, so verify it independently
    # if its main() is blocked by the unavailable enriched table.
    diploma_path = paths.CLEAN_STUDENT_DIPLOMA_PATH_V2
    if not diploma_path.exists():
        from src.data.clean_student_diploma import clean_student_diploma
        frame = clean_student_diploma(pd.read_parquet(paths.ACADEMIC_INFO_PATH))
        diploma_path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_parquet(diploma_path, index=False)
        results["standalone_diploma"] = "Generated only the raw-to-clean diploma artifact; merged diploma remains blocked."

    for name in outputs:
        old, new = getattr(paths, name), getattr(paths, name + "_V2")
        if new.suffix != ".parquet" or not new.is_file():
            results["comparisons"][name] = {"status": "unavailable"}
            continue
        current = pd.read_parquet(new)
        entry = {"v2": describe(current)}
        if old.is_file():
            previous = pd.read_parquet(old)
            entry.update(v1=describe(previous), **compare(previous, current))
        results["comparisons"][name] = entry

    for name, raw, output in [
        ("clean_student_course", paths.STUDENT_COURSE_PATH, paths.CLEAN_STUDENT_COURSE_PATH_V2),
        ("clean_degree_course", paths.DEGREE_COURSE_PATH, paths.CLEAN_DEGREE_COURSE_PATH_V2),
        ("clean_student_diploma", paths.ACADEMIC_INFO_PATH, paths.CLEAN_STUDENT_DIPLOMA_PATH_V2),
    ]:
        if output.exists():
            baseline = original_cleaner(name)(pd.read_parquet(raw))
            # Compare like-for-like persisted tables. Parquet normalizes pandas
            # column-label string metadata even when all values/dtypes agree.
            buffer = io.BytesIO()
            baseline.to_parquet(buffer, index=False)
            buffer.seek(0)
            results["baseline_comparisons"][name] = compare(pd.read_parquet(buffer), pd.read_parquet(output))

    raw_status = pd.read_parquet(paths.STUDENT_STATUS_PATH)
    part_column = next(col for col in raw_status.columns if col.lower().strip() == "part_id")
    parts = pd.to_numeric(raw_status[part_column], errors="raise")
    invalid = raw_status.loc[parts.gt(20193) & ~parts.mod(10).isin([1, 2, 3])]
    results["invalid_raw_status_parts"] = {str(key): int(value) for key, value in invalid[part_column].value_counts().items()}
    changes = []
    for name, before in original.items():
        path = paths.PROJECT_ROOT / name
        if not path.is_file() or signature(path) != before:
            changes.append(name)
    results["protected_files"] = len(original)
    results["original_artifact_changes"] = changes
    with (REPORT / "real_data_verification.json").open("x", encoding="utf-8") as stream:
        json.dump(results, stream, indent=2, ensure_ascii=False)
    print("Original files changed:", changes)
    print("Same-code baseline comparisons:", results["baseline_comparisons"])
    print("Invalid raw status parts:", results["invalid_raw_status_parts"])


if __name__ == "__main__":
    main()
