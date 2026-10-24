import hashlib
import json
from pathlib import Path

import pytest


def legacy(root):
    source = root / 'before_backend_fix'
    source.mkdir()
    (source / 'students.csv').write_text('sample_id,role,student_id,degree_id,part_id\ns,primary,S,D,20251\n')
    folder = source / 'api_data/students/s'
    folder.mkdir(parents=True)
    for kind in ('student', 'courses'):
        body = json.dumps({'success': True, 'data': {'studentDegreeInfo': {
            'STUDENT_ID': 'S', 'DEGREE_ID': 'D', 'STATUS_SEMESTER_ID': '20251'}}}).encode()
        p = folder / (kind + '_response.json')
        p.write_bytes(body)
        p.with_suffix('.meta.json').write_text(json.dumps({'sha256': hashlib.sha256(body).hexdigest(),
            'bytes': len(body), 'identity': {'student_id': 'S', 'degree_id': 'D', 'part_id': 20251}}))
    folder = source / 'api_data/frozen_history'
    folder.mkdir()
    for year in range(2020, 2025):
        for semester in (1, 2, 3):
            p = folder / f'{year * 10 + semester}.json'
            p.write_bytes(b'{"success":true,"data":{"rows":[]}}')
            p.with_suffix('.meta.json').write_text(json.dumps({'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}))
    for name in ('run_old', 'actual_candidate_injection/run_diag'):
        run = source / 'experiments' / name
        run.mkdir(parents=True)
        for f, v in {'run_manifest': {'run_id': run.name, 'status': 'completed'},
                     'student_results': [], 'diagnostics': {}}.items():
            (run / (f + '.json')).write_text(json.dumps(v))
    models = source / 'experiments/model_versions'
    models.mkdir()
    (models / 'latest.json').write_bytes(b'{"unchanged":"shared"}')
    return source


def test_copy_migration_preserves_sources_and_never_seeds_old_courses(tmp_path):
    from tools.recommendation_pilot_20251.snapshot_migration import migrate
    source = legacy(tmp_path)
    before = {p: p.read_bytes() for p in source.rglob('*') if p.is_file()}
    result = migrate(tmp_path)
    assert result['status'] == 'PASS'
    assert all(p.read_bytes() == raw for p, raw in before.items())
    assert (tmp_path / 'snapshots/before_backend_fix/api_data/students/s/courses_response.json').is_file()
    after = tmp_path / 'snapshots/after_backend_fix/api_data'
    assert (after / 'students/s/student_response.json').is_file()
    assert not list(after.rglob('courses_response*'))
    assert len(list((after / 'frozen_history').glob('*.json'))) == 30
    assert (tmp_path / 'experiments/before_backend_fix/comparison/run_old/student_results.json').read_bytes() == b'[]'
    assert (tmp_path / 'experiments/before_backend_fix/actual_candidate_injection/run_diag/student_results.json').is_file()
    assert not (tmp_path / 'experiments/model_versions').exists()
    assert (tmp_path / 'students.csv').read_bytes() == (source / 'students.csv').read_bytes()


def test_migration_refuses_corrupt_source_before_copy(tmp_path):
    from tools.recommendation_pilot_20251.snapshot_migration import migrate
    source = legacy(tmp_path)
    (source / 'api_data/students/s/courses_response.json').write_bytes(b'{}')
    with pytest.raises(ValueError, match='fingerprint'):
        migrate(tmp_path)
    assert not (tmp_path / 'snapshots').exists()


def test_migration_never_overwrites_destination(tmp_path):
    from tools.recommendation_pilot_20251.snapshot_migration import migrate
    legacy(tmp_path)
    p = tmp_path / 'snapshots/after_backend_fix/api_data/students/s/student_response.json'
    p.parent.mkdir(parents=True)
    p.write_bytes(b'preserve destination')
    with pytest.raises(ValueError, match='destination'):
        migrate(tmp_path)
    assert p.read_bytes() == b'preserve destination'
