"""Copy-only, checksum-verified migration. No network, model loading or deletes."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from uuid import uuid4

from .adapter import PILOT_ROOT


def digest(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def _json(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)


def _files(directory):
    return sorted(p for p in directory.rglob('*') if p.is_file()) if directory.exists() else []


def _references(value, key=''):
    if isinstance(value, dict):
        for name, item in value.items():
            yield from _references(item, key + '.' + name)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _references(item, key + f'[{index}]')
    elif isinstance(value, str) and (Path(value).is_absolute() or
            value.startswith(('data/', 'models/', 'data\\', 'models\\'))):
        yield {'key': key, 'path': value}


def verify(audit):
    """Verify every protected source and every copied file against the inventory."""
    if isinstance(audit, (str, Path)):
        audit = json.loads(Path(audit).read_text(encoding='utf-8'))
    changed = [record['path'] for record in audit['inventory']
               if not Path(record['path']).is_file() or digest(record['path']) != record['sha256']]
    mismatched = [record['destination'] for record in audit['copies']
                  if not Path(record['destination']).is_file() or digest(record['destination']) != record['sha256']]
    return {'status': 'PASS' if not changed and not mismatched else 'FAIL',
            'source_file_count': len(audit['inventory']), 'copy_file_count': len(audit['copies']),
            'changed_sources': changed, 'mismatched_copies': mismatched}


def migrate(root=PILOT_ROOT, *, protected=()):
    root = Path(root).resolve()
    sources = [p for p in (root, root / 'before_backend_fix') if (p / 'api_data').is_dir()]
    if len(sources) != 1:
        raise ValueError('Expected one unambiguous legacy archive source.')
    source = sources[0]
    with (source / 'students.csv').open(encoding='utf-8-sig', newline='') as stream:
        cohort = list(csv.DictReader(stream))
    captures = _files(source / 'api_data')
    for p in captures:
        if p.suffix != '.json' or p.name.endswith('.meta.json'):
            continue
        metadata = p.with_suffix('.meta.json')
        if not metadata.is_file():
            raise ValueError(f'Missing source fingerprint metadata: {p}')
        meta = json.loads(metadata.read_text(encoding='utf-8-sig'))
        raw = p.read_bytes()
        json.loads(raw)
        if meta.get('sha256') != hashlib.sha256(raw).hexdigest() or meta.get('bytes', len(raw)) != len(raw):
            raise ValueError(f'Source fingerprint mismatch: {p}')
    for row in cohort:
        if row.get('role') != 'primary':
            continue
        base = source / 'api_data/students' / row['sample_id']
        for kind in ('student', 'courses'):
            p = base / f'{kind}_response.json'
            if not p.is_file():
                raise ValueError(f'Missing primary source: {p}')
            meta = json.loads(p.with_suffix('.meta.json').read_text(encoding='utf-8-sig'))
            identity = meta.get('identity', {})
            for key in ('student_id', 'degree_id', 'part_id'):
                if str(identity.get(key)) != str(row[key]):
                    raise ValueError(f'Source identity mismatch: {p.name}, {row["sample_id"]}, {key}')
            if kind == 'student':
                info = json.loads(p.read_bytes())['data']['studentDegreeInfo']
                for key, field in (('student_id', 'STUDENT_ID'), ('degree_id', 'DEGREE_ID'), ('part_id', 'STATUS_SEMESTER_ID')):
                    if str(info.get(field)) != str(row[key]):
                        raise ValueError(f'Student identity mismatch: {row["sample_id"]}, {key}')
    for year in range(2020, 2025):
        for semester in (1, 2, 3):
            if not (source / 'api_data/frozen_history' / f'{year * 10 + semester}.json').is_file():
                raise ValueError('Missing original Frozen History source.')

    selected = set(_files(source))
    for item in protected:
        item = Path(item)
        selected.update(_files(item) if item.is_dir() else [item] if item.is_file() else [])
    inventory = [{'path': str(p), 'sha256': digest(p), 'bytes': p.stat().st_size}
                 for p in sorted(selected) if '__pycache__' not in p.parts]
    hashes = {r['path']: r['sha256'] for r in inventory}
    plan, runs, other, references = [], [], [], []
    for p in captures:
        relative = p.relative_to(source / 'api_data')
        plan.append((p, root / 'snapshots/before_backend_fix/api_data' / relative))
        if relative.parts[0] == 'frozen_history' or p.name in {'student_response.json', 'student_response.meta.json', '.gitignore'}:
            plan.append((p, root / 'snapshots/after_backend_fix/api_data' / relative))
    if source != root:
        plan.append((source / 'students.csv', root / 'students.csv'))
    plan.append((source / 'students.csv', root / 'snapshots/before_backend_fix/students.csv'))
    experiments = source / 'experiments'
    if experiments.exists():
        for p in sorted(experiments.iterdir()):
            if p.name.startswith('run_') and p.is_dir():
                family, directories = 'comparison', [p]
            elif p.name == 'actual_candidate_injection':
                family, directories = 'actual_candidate_injection', sorted(q for q in p.glob('run_*') if q.is_dir())
            else:
                other.append({'path': str(p), 'classification': 'shared_models' if p.name == 'model_versions' else
                              'preparation' if p.name.startswith('preparation_') else 'supporting_output', 'action': 'unchanged'})
                continue
            for directory in directories:
                manifest_file = directory / 'run_manifest.json'
                manifest = json.loads(manifest_file.read_text(encoding='utf-8-sig')) if manifest_file.exists() else {}
                complete = manifest.get('status') == 'completed' and all((directory / name).is_file()
                    for name in ('student_results.json', 'diagnostics.json'))
                destination = root / 'experiments/before_backend_fix' / family / directory.name
                runs.append({'run_id': directory.name, 'family': family, 'status': 'completed' if complete else 'incomplete',
                             'source': str(directory), 'destination': str(destination)})
                for item in _files(directory):
                    plan.append((item, destination / item.relative_to(directory)))
    for p in sorted(selected):
        if p.suffix == '.json' and (p.name in {'manifest.json', 'run_manifest.json', 'student_results.json', 'latest.json'}):
            for ref in _references(json.loads(p.read_text(encoding='utf-8-sig'))):
                references.append({'file': str(p), **ref})
    copies = [{'source': str(src), 'destination': str(dst), 'sha256': hashes[str(src)]} for src, dst in plan]
    # Preflight every destination before any archive is created; identical files can be verified/reused.
    for record in copies:
        dst = Path(record['destination'])
        if dst.is_symlink() or (dst.exists() and (not dst.is_file() or digest(dst) != record['sha256'])):
            raise ValueError(f'Conflicting migration destination: {dst}')
    audit_dir = root / 'migration_audits' / (datetime.now(timezone.utc).strftime('migration_%Y%m%dT%H%M%S_') + uuid4().hex[:8])
    audit_dir.mkdir(parents=True, exist_ok=False)
    audit = {'created_at_utc': datetime.now(timezone.utc).isoformat(), 'source_root': str(source),
             'pilot_root': str(root), 'inventory': inventory, 'copies': copies, 'runs': runs,
             'other_outputs': other, 'path_references': references, 'destructive_operations': 0,
             'originals_retained': True, 'cohort_sha256': hashes[str(source / 'students.csv')]}
    _json(audit_dir / 'inventory_before.json', audit)
    for record in copies:
        src, dst = Path(record['source']), Path(record['destination'])
        if not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            with src.open('rb') as reader, dst.open('xb') as writer:
                for block in iter(lambda: reader.read(1024 * 1024), b''):
                    writer.write(block)
                writer.flush()
                os.fsync(writer.fileno())
        if digest(src) != record['sha256'] or digest(dst) != record['sha256']:
            raise ValueError('Migration copy fingerprint verification failed.')
    for family in ('comparison', 'actual_candidate_injection'):
        (root / 'experiments/after_backend_fix' / family).mkdir(parents=True, exist_ok=True)
    result = {**verify(audit), 'audit_path': str(audit_dir / 'inventory_before.json'),
              'run_count': len(runs), 'completed_runs': sum(r['status'] == 'completed' for r in runs),
              'originals_retained': True, 'source_root': str(source)}
    _json(audit_dir / 'copy_verification.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=PILOT_ROOT)
    parser.add_argument('--verify', type=Path)
    args = parser.parse_args()
    if args.verify:
        result = verify(args.verify)
    else:
        repo = Path(__file__).resolve().parents[2]
        result = migrate(args.root, protected=[repo / 'models', repo / 'data/artifacts',
            *repo.joinpath('reports').glob('pilot_20251*.md')])
    print(json.dumps(result, ensure_ascii=True))
    if result['status'] != 'PASS':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
