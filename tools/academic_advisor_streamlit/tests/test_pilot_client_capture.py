import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock

app_dir = Path(__file__).resolve().parents[1]
client_path = app_dir / 'ui_client.py'
if not client_path.exists():
    client_path = Path(__file__).with_name('ui_client_updated.py')
spec = importlib.util.spec_from_file_location('pilot_ui_client', client_path)
mod = importlib.util.module_from_spec(spec)
import sys
sys.modules['pilot_ui_client'] = mod
spec.loader.exec_module(mod)

class CaptureTests(unittest.TestCase):
    def configure(self):
        cfg = mod.Config(
            fastapi_base='http://127.0.0.1:8000',student_url='https://example.test/student',
            courses_url='https://example.test/courses',history_url='https://example.test/history',
            student_params={'student_id':'studentId','part_id':'semesterId'},
            courses_params={'student_id':'studentId','degree_id':'degreeId','part_id':'semesterId'},
            history_params={'part_id':'part_id'},history_method='GET',service_key='',admin_key='',
            upstream_bearer='',timeout=20,context_file=None,
        )
        return mod.HttpClient(cfg)

    def test_student_preserves_wire_bytes(self):
        client=self.configure()
        body=b'{"data":{"studentDegreeInfo":{"STUDENT_ID":"123.111","STATUS_SEMESTER_ID":"20251","DEGREE_ID":"7.111"},"GPA":2.75}}'
        obj=mod.parse_json(body.decode())
        client._call=Mock(return_value=(200,obj,{},body))
        parsed, raw=client.capture_student('123.111',20251)
        self.assertEqual(body,raw)
        self.assertEqual(parsed['data']['GPA'],mod.Decimal('2.75'))
        self.assertEqual(client._call.call_args.kwargs['include_raw'],True)

    def test_history_supports_university_shape_without_conversion(self):
        client=self.configure()
        body=b'{"CoursesStatistsic":[{"PART_ID":"20243","SUM_MARKS":"3723","STUDENTS_COUNT":"74"}]}'
        client._call=Mock(return_value=(200,mod.parse_json(body.decode()),{},body))
        response, raw, count=client.capture_history(20243)
        self.assertEqual(count,1)
        self.assertEqual(raw,body)
        self.assertEqual(response['CoursesStatistsic'][0]['SUM_MARKS'],'3723')

    def test_history_rejects_wrong_period(self):
        client=self.configure()
        body=b'{"CoursesStatistsic":[{"PART_ID":"20251"}]}'
        client._call=Mock(return_value=(200,mod.parse_json(body.decode()),{},body))
        with self.assertRaises(mod.ClientError):
            client.capture_history(20243)

if __name__=='__main__':
    unittest.main()
