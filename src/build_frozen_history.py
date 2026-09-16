"""Build a new immutable history version from explicit finalized feature sources."""
import argparse
from pathlib import Path

import pandas as pd

from .feature_contract import FEATURE_ENGINEERING_VERSION, require_current_features
from .frozen_history import (
    HISTORY_SOURCE_COLUMNS, build_frozen_history, file_sha256, load_frozen_history,
    save_frozen_history, verify_legacy_course_history,
)
from .paths import frozen_history_dir


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of-part", type=int, required=True)
    parser.add_argument("--finalized-through-part", type=int, required=True,
                        help="Explicit attestation of the latest finalized semester in the source export.")
    parser.add_argument("--sources", type=Path, nargs="+", required=True,
                        help="Existing versioned feature tables; only finalized outcome columns are used.")
    parser.add_argument("--history-root", type=Path)
    parser.add_argument("--verify-legacy-course-state", type=Path,
                        help="Migrate only if this original course state matches the rebuilt history.")
    args = parser.parse_args()
    try:
        if frozen_history_dir(args.as_of_part, args.history_root).exists():
            raise FileExistsError("History version already exists; it will not be overwritten.")
        frames, signatures = [], []
        for path in args.sources:
            before = file_sha256(path)
            frame = pd.read_parquet(path, columns=HISTORY_SOURCE_COLUMNS)
            require_current_features(frame.attrs)
            if file_sha256(path) != before:
                raise ValueError(f"History source changed while reading: {path}")
            frames.append(frame)
            signatures.append({"path": str(path.resolve()), "sha256": before})
        source = pd.concat(frames, ignore_index=True)
        source.attrs["feature_engineering_version"] = FEATURE_ENGINEERING_VERSION
        course, specialty, metadata = build_frozen_history(
            source, args.as_of_part, finalized_through_part=args.finalized_through_part,
        )
        metadata["sources"] = signatures
        if args.verify_legacy_course_state:
            course = verify_legacy_course_history(args.verify_legacy_course_state, course)
            metadata["legacy_course_state"] = {
                "path": str(args.verify_legacy_course_state.resolve()),
                "sha256": file_sha256(args.verify_legacy_course_state), "equivalence_verified": True,
            }
        save_frozen_history(course, specialty, metadata, root=args.history_root)
        _, _, loaded = load_frozen_history(args.as_of_part, root=args.history_root)
        print(f"Saved and verified: {loaded['directory']}")
        print(f"Finalized outcomes: {loaded['source_row_count']:,}; as_of_part: {loaded['as_of_part']}")
    except (ValueError, KeyError, OSError) as exc:
        parser.exit(2, f"{exc}\n")


if __name__ == "__main__":
    main()
