import json
from pathlib import Path
import tempfile
import unittest
import sys
# Support both tests/ inside the Streamlit package and standalone local tests.
app_dir = Path(__file__).resolve().parents[1]
if (app_dir / "pilot_collection_store.py").exists():
    sys.path.insert(0, str(app_dir))
from pilot_collection_store import PilotCollectionStore, CollectionError, history_parts


class PilotCollectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        pilot = self.root / 'data/evaluation/recommendation_pilot_20251'
        pilot.mkdir(parents=True)
        (pilot / 'students.csv').write_text(
            'sample_id,role,student_id,degree_id,part_id\n'
            'S001,primary,29485.111,7.111,20251\n'
            'S002,reserve,29486.111,8.111,20251\n',encoding='utf-8')
        self.store = PilotCollectionStore(self.root)

    def test_archive_is_immutable_and_original_bytes_preserved(self):
        data = b'{"data":{"GPA_POINTS":2.5,"STUDENT_ID":"29485.111"}}'
        path = self.store.student_file('S001', 'student')
        self.assertTrue(self.store.save(path,data,kind='student',identity={'sample_id':'S001'},source='student_api'))
        self.assertEqual(path.read_bytes(), data)
        self.assertFalse(self.store.save(path,data,kind='student',identity={'sample_id':'S001'},source='student_api'))
        self.assertEqual(self.store.state(path),'saved')
        self.assertTrue((self.store.root / '.gitignore').exists())

    def test_detects_corruption_and_refuses_overwrite(self):
        path = self.store.history_file(20243)
        self.store.save(path,b'{"rows":[{"PART_ID":20243}]}',kind='history',identity={'part_id':20243},source='history_api')
        path.write_bytes(b'{}')
        self.assertEqual(self.store.state(path),'corrupt')
        with self.assertRaises(CollectionError):
            self.store.save(path,b'{}',kind='history',identity={'part_id':20243},source='history_api')

    def test_cohort_and_period_constraints(self):
        self.assertEqual(len(history_parts()),15)
        self.assertEqual(history_parts()[0],20201)
        self.assertEqual(history_parts()[-1],20243)
        self.assertEqual(len(self.store.load_students()),2)
        with self.assertRaises(CollectionError):
            self.store.student_file('../escape', 'student')
        with self.assertRaises(CollectionError):
            self.store.history_file(20251)

    def test_summary(self):
        self.assertEqual(self.store.overview(self.store.load_students())['student_total'],2)
        self.assertEqual(self.store.overview(self.store.load_students())['history_total'],15)

if __name__ == '__main__':
    unittest.main()
