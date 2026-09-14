"""Stream accepted course details; keep one ranked summary row per accepted plan."""
from datetime import datetime, timezone
import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

COURSE_SCHEMA = pa.schema([
    ("plan_id", pa.int64()), ("course_id", pa.string()), ("course_name", pa.string()),
    ("course_credits", pa.float64()), ("expected_points", pa.float64()), ("fail_probability", pa.float64()),
])


def write_json(path, payload):
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")


def save_recommendations(engine, output_dir, **kwargs):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    files = [output_dir / name for name in ["plans.parquet", "courses.parquet", "result.json"]]
    if any(p.exists() for p in files):
        raise FileExistsError("Use a new output directory for each recommendation run.")
    # An interrupted run has no result.json completion marker.
    with pq.ParquetWriter(output_dir / "courses.parquet", COURSE_SCHEMA, compression="zstd") as writer:
        def sink(frame):
            writer.write_table(pa.Table.from_pandas(frame, schema=COURSE_SCHEMA, preserve_index=False))
        plans, result = engine.recommend(course_sink=sink, **kwargs)
    plans.to_parquet(output_dir / "plans.parquet", index=False)
    result["created_at_utc"] = datetime.now(timezone.utc).isoformat()
    result["files"] = {p.stem: str(p.resolve()) for p in files if p.suffix == ".parquet"}
    write_json(output_dir / "result.json", result)
    return result
