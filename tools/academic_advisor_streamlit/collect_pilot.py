"""Explicit operator command for corrected Courses captures; never run at startup."""
import argparse
import json
from pathlib import Path

from .pilot_collection_store import PilotCollectionStore, CollectionError
from .ui_client import ClientError, Config, HttpClient


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--all-primary', action='store_true', required=True)
    parser.add_argument('--snapshot', choices=['after_backend_fix'], default='after_backend_fix')
    args = parser.parse_args(argv)
    project = Path(__file__).resolve().parents[2]
    store = PilotCollectionStore(project, snapshot_id=args.snapshot)
    students = [row for row in store.load_students() if row['role'] == 'primary']
    client = HttpClient(Config.from_env())
    failed = 0
    print(json.dumps({'snapshot_id': args.snapshot, 'destination': str(store.root), 'student_count': len(students)}))
    for student in students:
        path = store.student_file(student['sample_id'], 'courses')
        previous = store.state(path)
        try:
            store.collect_student(student, client, courses_only=True)
            result = {'sample_id': student['sample_id'], 'status': 'skipped_verified' if previous == 'saved' else 'saved'}
        except (CollectionError, ClientError, ValueError, OSError) as error:
            failed += 1
            result = {'sample_id': student['sample_id'], 'status': 'failed', 'reason': str(error)}
        print(json.dumps(result, ensure_ascii=True))
    if failed:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
