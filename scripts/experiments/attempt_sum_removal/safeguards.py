"""Fail-closed filesystem safeguards for this isolated experiment.

No production artifact is written here. Snapshots stream all protected files,
including untracked files and Graphify content, without loading data into memory.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import stat
from typing import Mapping


EXCLUDED_DIRECTORIES = {".git", ".venv", "__pycache__", ".pytest_cache"}
ALLOWED_DIRECTORIES = (
    "scripts/experiments/attempt_sum_removal",
    "data/evaluation/experiments/attempt_sum_removal",
    "models/experiments/attempt_sum_removal",
)
REPORT = "reports/attempt_sum_removal_experiment.md"


def _reject_link(path: Path) -> None:
    """Reject symlinks and Windows junctions before following their targets."""
    if not path.exists() and not path.is_symlink():
        return
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode) or (
        getattr(info, "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    ):
        raise ValueError(f"Symbolic link or reparse point is forbidden: {path}")


def _root(root: Path) -> Path:
    root = Path(root).absolute()
    _reject_link(root)
    if not root.is_dir():
        raise NotADirectoryError(root)
    return root.resolve(strict=True)


def _allowed(relative: str) -> bool:
    return relative == REPORT or any(
        relative == directory or relative.startswith(directory + "/")
        for directory in ALLOWED_DIRECTORIES
    )


def snapshot(root: Path) -> dict[str, str]:
    """Return repository-relative POSIX paths and SHA-256 for protected files."""
    root = _root(root)
    result = {}
    for directory, children, files in os.walk(root, followlinks=False):
        base = Path(directory)
        retained = []
        for name in sorted(children):
            path = base / name
            relative = path.relative_to(root).as_posix()
            if name in EXCLUDED_DIRECTORIES:
                continue
            _reject_link(path)
            if not _allowed(relative):
                retained.append(name)
        children[:] = retained
        for name in sorted(files):
            path = base / name
            _reject_link(path)
            relative = path.relative_to(root).as_posix()
            if _allowed(relative):
                continue
            if not path.is_file():
                raise ValueError(f"Non-regular protected file: {path}")
            digest = hashlib.sha256()
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
            result[relative] = digest.hexdigest()
    return dict(sorted(result.items()))


def verify(root: Path, before: Mapping[str, str]) -> dict[str, list[str]]:
    """Compare protected file contents and membership with an earlier snapshot."""
    after = snapshot(root)
    return {
        "changed": sorted(path for path in before.keys() & after.keys() if before[path] != after[path]),
        "missing": sorted(before.keys() - after.keys()),
        "new_protected": sorted(after.keys() - before.keys()),
    }


def assert_unchanged(root: Path, before: Mapping[str, str]) -> dict[str, list[str]]:
    """Raise if a protected file changed, disappeared, or was added."""
    changes = verify(root, before)
    if any(changes.values()):
        raise RuntimeError(f"Protected repository files changed: {changes}")
    return changes


def create_output_dirs(root: Path) -> tuple[Path, Path]:
    """Create fresh confined evidence/model directories, refusing existing output.

    All destinations and their ancestors are checked before the first mkdir.
    The report itself is left for the runner to create exclusively.
    """
    root = _root(root)
    evidence = root / ALLOWED_DIRECTORIES[1]
    models = root / ALLOWED_DIRECTORIES[2]
    report = root / REPORT
    for destination in (evidence, models, report):
        relative = destination.relative_to(root)
        current = root
        for component in relative.parts:
            current = current / component
            _reject_link(current)
            if current.exists() and current != destination and not current.is_dir():
                raise NotADirectoryError(current)
        if not destination.resolve().is_relative_to(root):
            raise ValueError(f"Destination escapes repository: {destination}")
        if destination.exists():
            raise FileExistsError(f"Experiment output already exists: {destination}")
    evidence.mkdir(parents=True, exist_ok=False)
    models.mkdir(parents=True, exist_ok=False)
    return evidence, models
