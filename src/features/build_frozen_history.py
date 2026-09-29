"""Build immutable base-only V2 history from finalized V2 feature outcomes."""
import argparse
from pathlib import Path

import pandas as pd

from src.features.feature_contract import FEATURE_ENGINEERING_VERSION, require_current_features
from src.features.frozen_history import (
    HISTORY_SOURCE_COLUMNS, build_frozen_history, file_sha256, load_frozen_history,
    save_frozen_history, verify_legacy_course_history,
)
from src.paths import (
    FROZEN_HISTORY_DIR_V2, TEMPORAL_TRAIN_FEATURES_PATH_V2,
    TEMPORAL_TEST_FEATURES_PATH_V2, academic_part, frozen_history_dir,
)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of-part", type=int, required=True)
    parser.add_argument("--finalized-through-part", type=int, required=True,
                        help="Explicit attestation of the latest finalized semester in the source export.")
    parser.add_argument("--sources", type=Path, nargs="+",
                        help="Defaults to official V2 train (plus test for cutoffs after 20243). Custom sources must have _v2 names and dataset_version=V2 metadata.")
    parser.add_argument("--history-root", type=Path, default=FROZEN_HISTORY_DIR_V2,
                        help="Isolated V2 history root; existing versions are never overwritten.")
    parser.add_argument("--verify-legacy-course-state", type=Path,
                        help="Migrate only if this original course state matches the rebuilt history.")
    args = parser.parse_args(argv)
    try:
        if frozen_history_dir(args.as_of_part, args.history_root).exists():
            raise FileExistsError("History version already exists; it will not be overwritten.")
        cutoff = academic_part(args.as_of_part)
        official_sources = {
            TEMPORAL_TRAIN_FEATURES_PATH_V2.resolve(), TEMPORAL_TEST_FEATURES_PATH_V2.resolve(),
        }
        source_paths = args.sources or [TEMPORAL_TRAIN_FEATURES_PATH_V2]
        if args.sources is None and cutoff > 20243:
            source_paths.append(TEMPORAL_TEST_FEATURES_PATH_V2)
        frames, signatures = [], []
        for path in source_paths:
            before = file_sha256(path)
            frame = pd.read_parquet(path, columns=HISTORY_SOURCE_COLUMNS)
            require_current_features(frame.attrs)
            declared_version = frame.attrs.get("dataset_version")
            if declared_version not in (None, "V2"):
                raise ValueError(f"History source dataset_version must be V2: {path}")
            if path.resolve() not in official_sources and (
                    not path.stem.endswith("_v2") or declared_version != "V2"):
                raise ValueError(f"Custom history sources require a _v2 filename and dataset_version=V2 metadata: {path}")
            if file_sha256(path) != before:
                raise ValueError(f"History source changed while reading: {path}")
            frames.append(frame)
            signatures.append({"path": str(path.resolve()), "sha256": before, "dataset_version": "V2"})
        source = pd.concat(frames, ignore_index=True)
        source.attrs["feature_engineering_version"] = FEATURE_ENGINEERING_VERSION
        source.attrs["dataset_version"] = "V2"
        course, specialty, metadata = build_frozen_history(
            source, args.as_of_part, finalized_through_part=args.finalized_through_part,
            dataset_version="V2",
        )
        metadata["sources"] = signatures
        if args.verify_legacy_course_state:
            course = verify_legacy_course_history(args.verify_legacy_course_state, course)
            metadata["legacy_course_state"] = {
                "path": str(args.verify_legacy_course_state.resolve()),
                "sha256": file_sha256(args.verify_legacy_course_state), "equivalence_verified": True,
            }
        save_frozen_history(course, specialty, metadata, root=args.history_root)
        _, _, loaded = load_frozen_history(args.as_of_part, root=args.history_root, dataset_version="V2")
        print(f"Saved and verified: {loaded['directory']}")
        print(f"Finalized outcomes: {loaded['source_row_count']:,}; as_of_part: {loaded['as_of_part']}")
    except (ValueError, KeyError, OSError) as exc:
        parser.exit(2, f"{exc}\n")


if __name__ == "__main__":
    main()
