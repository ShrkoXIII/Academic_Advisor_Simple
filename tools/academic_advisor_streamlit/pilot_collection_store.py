"""Local, immutable API-response archive for the 20251 validation pilot.

Store exact HTTP body bytes, not rewritten/normalized model inputs.  No inference.
"""
from __future__ import annotations

import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re

ALLOWED_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
PILOT_SUBPATH = Path('data/evaluation/recommendation_pilot_20251')


class CollectionError(ValueError):
    pass


def _safe(value: str, field: str) -> str:
    value = str(value).strip()
    if not ALLOWED_ID.fullmatch(value):
        raise CollectionError(f"Invalid {field} for a collection path.")
    return value


def _atomic_exclusive(path: Path, content: bytes) -> None:
    """Write once with O_EXCL. Never overwrite successful captures."""
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, 'wb') as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise


class PilotCollectionStore:
    def __init__(self, project_root: Path, *, snapshot_id='after_backend_fix'):
        from tools.recommendation_pilot_20251.snapshots import api_data_root, validate_snapshot
        self.pilot = Path(project_root).resolve() / PILOT_SUBPATH
        self.snapshot_id = validate_snapshot(snapshot_id)
        self.root = api_data_root(self.pilot, snapshot_id)

    def initialize(self):
        if self.snapshot_id == 'before_backend_fix':
            raise CollectionError('The before_backend_fix snapshot is read-only.')
        self.root.mkdir(parents=True, exist_ok=True)
        # The raw student responses must NEVER be staged by git add .
        ignore = self.root / '.gitignore'
        if not ignore.exists():
            _atomic_exclusive(ignore, b'*\n!.gitignore\n')

    def load_students(self) -> list[dict]:
        path = self.pilot / 'students.csv'
        if not path.is_file():
            raise CollectionError(f"Missing cohort file: {path}")
        with path.open(newline='', encoding='utf-8-sig') as handle:
            reader = csv.DictReader(handle)
            required = {'sample_id', 'role', 'student_id', 'degree_id', 'part_id'}
            if not required.issubset(set(reader.fieldnames or [])):
                raise CollectionError(f"students.csv missing columns: {sorted(required - set(reader.fieldnames or []))}")
            records = []
            seen = set()
            for row in reader:
                if row['role'] not in ('primary', 'reserve'):
                    raise CollectionError('Invalid role in students.csv')
                sample_id = _safe(row['sample_id'], 'sample_id')
                if sample_id in seen:
                    raise CollectionError('Duplicate sample_id in students.csv')
                seen.add(sample_id)
                if row['part_id'] != '20251':
                    raise CollectionError('Pilot cohort must use part_id=20251')
                if not row['student_id'] or not row['degree_id']:
                    raise CollectionError('Student and degree IDs cannot be empty.')
                records.append(row)
        return records

    def student_file(self, sample_id: str, kind: str) -> Path:
        if kind not in {'student', 'courses'}:
            raise CollectionError('Unexpected student API kind')
        return self.root / 'students' / _safe(sample_id, 'sample_id') / f'{kind}_response.json'

    def history_file(self, part_id: int) -> Path:
        part_id = int(part_id)
        if part_id not in history_parts():
            raise CollectionError('History part is outside this pilot cutoff.')
        return self.root / 'frozen_history' / f'{part_id}.json'

    def state(self, path: Path) -> str:
        if not path.exists():
            return 'missing'
        meta = path.with_suffix('.meta.json')
        if not meta.exists():
            return 'unverified'
        try:
            data = json.loads(meta.read_text(encoding='utf-8'))
            payload = path.read_bytes()
            json.loads(payload)
            return 'saved' if data['sha256'] == hashlib.sha256(payload).hexdigest() else 'corrupt'
        except (OSError, ValueError, KeyError):
            return 'corrupt'

    def save(self, path: Path, body: bytes, *, kind: str, identity: dict, source: str) -> bool:
        """Return True if saved, False if an already verified copy exists."""
        path = Path(path)
        if not path.resolve().is_relative_to(self.root.resolve()):
            raise CollectionError('Capture path is outside the selected snapshot.')
        self.initialize()
        state = self.state(path)
        if state == 'saved':
            return False
        if state != 'missing':
            raise CollectionError(f'An existing unverified/corrupt file needs manual review: {path}')
        if not isinstance(body, bytes) or not body:
            raise CollectionError('Empty or non-byte HTTP response body')
        try:
            parsed = json.loads(body)
        except (UnicodeDecodeError, ValueError) as exc:
            raise CollectionError('Response body is not valid JSON') from exc
        if not isinstance(parsed, dict):
            raise CollectionError('Expected an API JSON object')
        path.parent.mkdir(parents=True, exist_ok=True)
        metadata = {
            'snapshot_id': self.snapshot_id,
            'kind': kind,
            'identity': identity,
            'saved_at_utc': datetime.now(timezone.utc).isoformat(),
            'source': source, # caller passes only endpoint label, never URL/token/query
            'sha256': hashlib.sha256(body).hexdigest(),
            'bytes': len(body),
        }
        meta_path = path.with_suffix('.meta.json')
        _atomic_exclusive(path, body)
        try:
            _atomic_exclusive(meta_path, (json.dumps(metadata, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
        except BaseException:
            path.unlink(missing_ok=True)
            raise
        return True

    def overview(self, students: list[dict]) -> dict:
        main = [row for row in students if row['role'] == 'primary']
        student_states = [self.state(self.student_file(row['sample_id'], kind))
                          for row in main for kind in ('student', 'courses')]
        history_states = [self.state(self.history_file(part)) for part in history_parts()]
        return {
            'student_saved': student_states.count('saved'),
            'student_total': len(student_states),
            'history_saved': history_states.count('saved'),
            'history_total': len(history_states),
            'warnings': len([s for s in student_states + history_states if s in ('unverified', 'corrupt')]),
            'student_response_saved': sum(self.state(self.student_file(row['sample_id'], 'student')) == 'saved' for row in main),
            'courses_response_saved': sum(self.state(self.student_file(row['sample_id'], 'courses')) == 'saved' for row in main),
            'primary_total': len(main),
        }

    def collect_student(self, record, client, *, courses_only=False) -> bool:
        """Resume one capture in the selected snapshot; no recommendation/history calls."""
        if self.snapshot_id == 'before_backend_fix':
            raise CollectionError('The before_backend_fix snapshot is read-only.')
        sid, degree = str(record['student_id']).strip(), str(record['degree_id']).strip()
        term, sample = int(record['part_id']), str(record['sample_id']).strip()
        identity = {'sample_id': sample, 'student_id': sid, 'degree_id': degree, 'part_id': term}
        student_path = self.student_file(sample, 'student')
        courses_path = self.student_file(sample, 'courses')
        student_state = self.state(student_path)
        if student_state != 'saved':
            if courses_only or student_state != 'missing':
                raise CollectionError(f'{sample}: a verified original Student response is required.')
            student_json, raw = client.capture_student(sid, term)
        else:
            student_json, raw = json.loads(student_path.read_bytes()), None
        info = student_json.get('data', {}).get('studentDegreeInfo', {})
        for field, expected in (('STUDENT_ID', sid), ('DEGREE_ID', degree), ('STATUS_SEMESTER_ID', str(term))):
            if str(info.get(field, '')).strip() != expected:
                raise CollectionError(f'{sample}: Student identity mismatch: {field}; no save')
        if raw is not None:
            self.save(student_path, raw, kind='student', identity=identity, source='university_student_api')
        courses_state = self.state(courses_path)
        if courses_state == 'missing':
            _response, raw = client.capture_courses(sid, degree, term)
            self.save(courses_path, raw, kind='courses', identity=identity, source='university_courses_api')
        elif courses_state != 'saved':
            raise CollectionError(f'{sample}: existing Courses response needs manual review.')
        return self.state(student_path) == 'saved' and self.state(courses_path) == 'saved'


def history_parts() -> list[int]:
    return [year * 10 + semester for year in range(2020, 2025) for semester in (1, 2, 3)]
