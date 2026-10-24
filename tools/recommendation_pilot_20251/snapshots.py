"""Resolve API snapshots separately from the shared, unchanged model artifacts."""
from pathlib import Path
import subprocess

from .adapter import PILOT_ROOT, sha256

BEFORE = 'before_backend_fix'
AFTER = 'after_backend_fix'
DEFAULT_SNAPSHOT = AFTER


def validate_snapshot(snapshot_id):
    if snapshot_id not in (BEFORE, AFTER):
        raise ValueError('Unknown Pilot snapshot identifier.')
    return snapshot_id


def api_data_root(root=PILOT_ROOT, snapshot_id=DEFAULT_SNAPSHOT):
    root = Path(root).resolve()
    directory = root / 'snapshots' / validate_snapshot(snapshot_id) / 'api_data'
    if not directory.resolve().is_relative_to(root / 'snapshots' / snapshot_id):
        raise ValueError('API snapshot path escapes its selected snapshot.')
    return directory


def model_versions_root(root=PILOT_ROOT):
    """The existing whole-folder archive may already contain the shared bundles."""
    root = Path(root).resolve()
    canonical = root / 'experiments/model_versions'
    archived = root / 'before_backend_fix/experiments/model_versions'
    return canonical if canonical.exists() or not archived.exists() else archived


def preparation_reports(root=PILOT_ROOT):
    root = Path(root)
    return sorted({p for base in (root / 'experiments', root / 'before_backend_fix/experiments')
                   for p in base.glob('preparation_*/features/feature_validation_report.json')}, reverse=True)


def run_root(root=PILOT_ROOT, snapshot_id=DEFAULT_SNAPSHOT, family='comparison'):
    if family not in ('comparison', 'actual_candidate_injection'):
        raise ValueError('Unknown Pilot experiment family.')
    return Path(root).resolve() / 'experiments' / validate_snapshot(snapshot_id) / family


def run_read_roots(root=PILOT_ROOT, family='comparison'):
    root = Path(root).resolve()
    suffix = Path() if family == 'comparison' else Path('actual_candidate_injection')
    return [(run_root(root, AFTER, family), AFTER), (run_root(root, BEFORE, family), BEFORE),
            (root / 'experiments' / suffix, BEFORE),
            (root / 'before_backend_fix/experiments' / suffix, BEFORE)]


def manifest_context(root, snapshot_id, students=()):
    directory = api_data_root(root, snapshot_id)
    repo = Path(__file__).resolve().parents[2]
    try:
        commit = subprocess.check_output(['git', '-c', f'safe.directory={repo.as_posix()}',
            'rev-parse', 'HEAD'], cwd=repo, text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        commit = 'UNAVAILABLE'
    return {'snapshot_id': validate_snapshot(snapshot_id), 'api_snapshot_path': str(directory),
            'api_response_sha256': {s['sample_id']: {name: sha256(directory / 'students' / s['sample_id'] / name)
                if (directory / 'students' / s['sample_id'] / name).is_file() else None
                for name in ('student_response.json', 'courses_response.json')} for s in students},
            'code_commit': commit, 'frozen_history_provenance': {
                'path': str(directory / 'frozen_history'), 'history_as_of_part': 20243,
                'source_sha256': {p.name: sha256(p) for p in sorted((directory / 'frozen_history').glob('*.json'))}}}
