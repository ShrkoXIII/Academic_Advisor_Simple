"""Research-only attempt ablation primitives; no production contract changes."""
import hashlib
import json

import numpy as np
import pandas as pd

from src.features.frozen_history import file_sha256
from src.paths import EVALUATION_DIR, MODEL_DIR, PROJECT_ROOT


OUTPUT_DIR = EVALUATION_DIR / "experiments" / "attempt_number"
EXPERIMENT_MODEL_DIR = MODEL_DIR / "experiments" / "attempt_number"
REPORT_PATH = PROJECT_ROOT / "reports" / "attempt_number_feature_analysis.md"
ROW_KEYS = ["student_course_id", "student_id", "degree_id", "course_id", "part_id"]
VARIANTS = {"A": "attempt_number", "B": "is_repeat", "C": "no_attempt"}


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    def encode(obj):
        if isinstance(obj, np.generic):
            return obj.item()
        raise TypeError(type(obj).__name__)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False,
                               allow_nan=False, default=encode), encoding="utf-8")


def transform_matrix(matrix, variant):
    """Transform only the already temporal personal attempt column, preserving order."""
    values = pd.to_numeric(matrix["attempt_number"], errors="coerce").to_numpy(dtype=float)
    if not np.isfinite(values).all() or (values < 1).any() or (values != np.floor(values)).any():
        raise ValueError("Invalid or missing attempt_number in experiment matrix.")
    result = matrix.copy()
    if variant == "B":
        result["attempt_number"] = (values > 1).astype("float32")
        return result.rename(columns={"attempt_number": "is_repeat"})
    if variant == "C":
        return result.drop(columns="attempt_number")
    if variant != "A":
        raise ValueError(f"Unknown experiment variant: {variant}")
    return result


def row_fingerprint(frame):
    """Hash ordered immutable record keys, not a sorted set of records."""
    hashed = pd.util.hash_pandas_object(frame[ROW_KEYS].astype("string"), index=False)
    return hashlib.sha256(hashed.to_numpy().tobytes()).hexdigest()


def paired_cluster_interval(students, differences, *, draws=1000):
    """Paired row-mean loss delta, resampling students with all their rows."""
    work = pd.DataFrame({"student": np.asarray(students), "delta": differences})
    groups = work.groupby("student", sort=True).delta.agg(["sum", "size"])
    sums, counts = groups["sum"].to_numpy(), groups["size"].to_numpy()
    rng, results = np.random.default_rng(42), []
    for _ in range(draws):
        selected = rng.integers(0, len(groups), len(groups))
        results.append(sums[selected].sum() / counts[selected].sum())
    return {"rows": len(work), "students": len(groups), "delta": float(work.delta.mean()),
            "low": float(np.quantile(results, .025)), "high": float(np.quantile(results, .975)),
            "draws": draws, "seed": 42}


def protected_manifest():
    """Protect all existing data/model artifacts and non-experiment Python sources."""
    paths = set()
    for name in ["models", "data"]:
        for path in (PROJECT_ROOT / name).rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts:
                if path.is_relative_to(OUTPUT_DIR) or path.is_relative_to(EXPERIMENT_MODEL_DIR):
                    continue
                paths.add(path)
    for path in (PROJECT_ROOT / "src").rglob("*.py"):
        if not path.is_relative_to(PROJECT_ROOT / "src/experiments"):
            paths.add(path)
    for path in (PROJECT_ROOT / "json").glob("*.json"):
        paths.add(path)
    return {p.relative_to(PROJECT_ROOT).as_posix(): file_sha256(p) for p in sorted(paths)}


def capture_protected():
    path = OUTPUT_DIR / "protected_before_sha256.json"
    if path.exists():
        return verify_protected()
    write_json(path, protected_manifest())


def verify_protected():
    before = json.loads((OUTPUT_DIR / "protected_before_sha256.json").read_text())
    after = protected_manifest()
    changed = [k for k in before if before[k] != after.get(k)]
    added = sorted(set(after) - set(before))
    result = {"protected_files": len(before), "changed": changed, "added": added,
              "official_artifacts_modified": bool(changed or added)}
    write_json(OUTPUT_DIR / "protected_after_sha256.json", after)
    write_json(OUTPUT_DIR / "isolation_verification.json", result)
    if changed or added:
        raise ValueError(f"Protected files changed: {changed}; added: {added}")
    return result
