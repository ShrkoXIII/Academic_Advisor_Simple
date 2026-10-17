"""Filesystem isolation checks using disposable repositories only."""

import importlib

import pytest


@pytest.fixture
def guards():
    return importlib.import_module("scripts.experiments.attempt_sum_removal.safeguards")


def put(root, relative, content=b"abc"):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def test_snapshot_hashes_protected_graph_data_and_sources(guards, tmp_path):
    for path in ("src/main.py", "data/raw.bin", "graphify-out/cache/graph.json"):
        put(tmp_path, path)
    got = guards.snapshot(tmp_path)
    assert set(got) == {"src/main.py", "data/raw.bin", "graphify-out/cache/graph.json"}
    assert got["data/raw.bin"] == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_snapshot_excludes_only_runtime_and_allowed_outputs(guards, tmp_path):
    for path in (
        ".git/config", ".venv/pyvenv.cfg", "src/__pycache__/x.pyc",
        ".pytest_cache/state", "scripts/experiments/attempt_sum_removal/new.py",
        "data/evaluation/experiments/attempt_sum_removal/result.json",
        "models/experiments/attempt_sum_removal/model.bin",
        "reports/attempt_sum_removal_experiment.md",
    ):
        put(tmp_path, path)
    put(tmp_path, "reports/attempt_sum_removal_experiment.md.backup")
    assert set(guards.snapshot(tmp_path)) == {"reports/attempt_sum_removal_experiment.md.backup"}


def test_verify_reports_tampering_missing_and_new_protected_files(guards, tmp_path):
    changed = put(tmp_path, "src/changed.py")
    missing = put(tmp_path, "data/missing.bin")
    before = guards.snapshot(tmp_path)
    changed.write_bytes(b"tampered")
    missing.unlink()
    put(tmp_path, "models/unexpected.bin")
    put(tmp_path, "models/experiments/attempt_sum_removal/new.bin")
    assert guards.verify(tmp_path, before) == {
        "changed": ["src/changed.py"], "missing": ["data/missing.bin"],
        "new_protected": ["models/unexpected.bin"],
    }
    with pytest.raises(RuntimeError, match="Protected"):
        guards.assert_unchanged(tmp_path, before)


def test_assert_unchanged_accepts_only_allowed_new_outputs(guards, tmp_path):
    put(tmp_path, "src/official.py")
    before = guards.snapshot(tmp_path)
    put(tmp_path, "data/evaluation/experiments/attempt_sum_removal/result.json")
    assert guards.assert_unchanged(tmp_path, before) == {
        "changed": [], "missing": [], "new_protected": [],
    }


def test_output_creation_returns_confined_paths_and_refuses_second_run(guards, tmp_path):
    evidence, models = guards.create_output_dirs(tmp_path)
    assert evidence == tmp_path / "data/evaluation/experiments/attempt_sum_removal"
    assert models == tmp_path / "models/experiments/attempt_sum_removal"
    assert evidence.is_dir() and models.is_dir()
    with pytest.raises(FileExistsError):
        guards.create_output_dirs(tmp_path)


@pytest.mark.parametrize("existing", [
    "data/evaluation/experiments/attempt_sum_removal/result.json",
    "models/experiments/attempt_sum_removal/model.bin",
    "reports/attempt_sum_removal_experiment.md",
])
def test_existing_output_is_never_overwritten_or_partially_created(guards, tmp_path, existing):
    original = put(tmp_path, existing, b"preserve")
    before = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*"))
    with pytest.raises(FileExistsError):
        guards.create_output_dirs(tmp_path)
    assert original.read_bytes() == b"preserve"
    assert sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*")) == before


def symlink_or_skip(link, target, directory=False):
    try:
        link.symlink_to(target, target_is_directory=directory)
    except OSError:
        pytest.skip("Host does not allow creating symbolic links")


def test_snapshot_rejects_symlink_without_reading_external_data(guards, tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    outside = put(tmp_path, "outside.txt", b"secret")
    symlink_or_skip(root / "linked.txt", outside)
    with pytest.raises(ValueError, match="[Ss]ymbolic|[Ss]ymlink"):
        guards.snapshot(root)


def test_output_creation_rejects_parent_link_escape(guards, tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    symlink_or_skip(root / "data", outside, directory=True)
    with pytest.raises(ValueError):
        guards.create_output_dirs(root)
    assert list(outside.iterdir()) == []
    assert not (root / "models").exists()
