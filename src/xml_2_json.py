"""Compatibility entry point for Spreadsheet XML to JSON conversion."""

if __package__ in (None, ""):
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data.xml_spreadsheet import NAMESPACE, SS, clean_xml, get_value, load_xml
from src.data.xml_to_json import BASE_DIR, JSON_DIR, XML_DIR, convert_xml_to_json, main


if __name__ == "__main__":
    main()
