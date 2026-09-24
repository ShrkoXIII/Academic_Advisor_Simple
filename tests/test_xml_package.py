"""Structural and small-file regression checks for Spreadsheet XML tools."""

import json
from pathlib import Path
import runpy
import subprocess
import sys

from src.data import xml_to_json
from src.evaluation.evaluate_xml_recommendations import xml_rows
from src import xml_2_json


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_xml_module_imports_do_not_create_directories():
    code = """
from pathlib import Path

def reject_mkdir(self, *args, **kwargs):
    raise AssertionError(f"Import created directory: {self}")

Path.mkdir = reject_mkdir
import src.data.xml_spreadsheet
import src.data.xml_to_json
import src.xml_2_json
"""
    result = subprocess.run(
        [sys.executable, "-c", code], cwd=PROJECT_ROOT,
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_xml_converter_and_evaluator_keep_parsing_behavior(tmp_path, monkeypatch):
    xml_file = tmp_path / "candidate.xml"
    xml_file.write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<ss:Workbook xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">'
        '<ss:Worksheet ss:Name="Sheet1"><ss:Table>'
        '<ss:Row>'
        '<ss:Cell><ss:Data ss:Type="String">ROW</ss:Data></ss:Cell>'
        '<ss:Cell><ss:Data ss:Type="String">COURSE_ID</ss:Data></ss:Cell>'
        '<ss:Cell><ss:Data ss:Type="String">REQUESTABLE</ss:Data></ss:Cell>'
        '<ss:Cell><ss:Data ss:Type="String">NAME</ss:Data></ss:Cell>'
        '</ss:Row>'
        '<ss:Row>'
        '<ss:Cell><ss:Data ss:Type="Number">1</ss:Data></ss:Cell>'
        '<ss:Cell><ss:Data ss:Type="Number">123.5</ss:Data></ss:Cell>'
        '<ss:Cell><ss:Data ss:Type="Boolean">true</ss:Data></ss:Cell>'
        '<ss:Cell><ss:Data ss:Type="String">A & B</ss:Data></ss:Cell>'
        '</ss:Row>'
        '</ss:Table></ss:Worksheet></ss:Workbook>',
        encoding="utf-8",
    )
    original_xml = xml_file.read_bytes()
    output_dir = tmp_path / "json"
    monkeypatch.setattr(xml_to_json, "JSON_DIR", output_dir)

    assert not output_dir.exists()
    xml_to_json.convert_xml_to_json(xml_file)
    records = json.loads((output_dir / "candidate.json").read_text(encoding="utf-8"))
    assert records == [{"_ROW": 1, "COURSE_ID": 123.5, "REQUESTABLE": True, "NAME": "A & B"}]
    assert xml_file.read_bytes() == original_xml

    frame, repaired = xml_rows(xml_file)
    assert repaired is True
    assert frame.to_dict("records") == records
    assert xml_2_json.convert_xml_to_json is xml_to_json.convert_xml_to_json


def test_xml_evaluation_root_module_still_exposes_cli_help():
    result = subprocess.run(
        [sys.executable, "-m", "src.evaluate_xml_recommendations", "--help"],
        cwd=PROJECT_ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "--history-as-of-part" in result.stdout


def test_xml_conversion_root_entrypoint_delegates_to_package(monkeypatch):
    calls = []
    monkeypatch.setattr(xml_to_json, "main", lambda: calls.append(True))
    runpy.run_path(str(PROJECT_ROOT / "src" / "xml_2_json.py"), run_name="__main__")
    assert calls == [True]


def test_xml_conversion_direct_script_resolves_project_package(tmp_path):
    src_dir = tmp_path / "src"
    data_dir = src_dir / "data"
    data_dir.mkdir(parents=True)
    (src_dir / "__init__.py").write_text("", encoding="utf-8")
    (data_dir / "__init__.py").write_text("", encoding="utf-8")
    wrapper = src_dir / "xml_2_json.py"
    wrapper.write_bytes((PROJECT_ROOT / "src" / "xml_2_json.py").read_bytes())
    (data_dir / "xml_spreadsheet.py").write_text(
        'NAMESPACE = {}\nSS = ""\nclean_xml = get_value = load_xml = lambda value: value\n',
        encoding="utf-8",
    )
    (data_dir / "xml_to_json.py").write_text(
        'BASE_DIR = JSON_DIR = XML_DIR = None\n'
        'convert_xml_to_json = lambda path: None\n'
        'def main(): print("DIRECT_XML_OK")\n',
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, "-I", str(wrapper)], cwd=tmp_path,
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == "DIRECT_XML_OK"
