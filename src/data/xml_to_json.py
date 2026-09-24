"""Convert Spreadsheet XML exports to JSON."""

from pathlib import Path
import json

from src.data.xml_spreadsheet import NAMESPACE, get_value, load_xml


BASE_DIR = Path(__file__).resolve().parents[2]
XML_DIR = BASE_DIR / "xml"
JSON_DIR = BASE_DIR / "json"

def convert_xml_to_json(xml_file):

    print(f"جاري تحويل: {xml_file.name}")

    tree = load_xml(xml_file)

    root = tree.getroot()

    worksheet = root.find(
        ".//ss:Worksheet",
        NAMESPACE
    )

    if worksheet is None:
        print(
            f"❌ لم يتم العثور على Worksheet "
            f"في {xml_file.name}"
        )
        return

    rows = worksheet.findall(
        "./ss:Table/ss:Row",
        NAMESPACE
    )

    if not rows:
        print(f"❌ الملف لا يحتوي على صفوف")
        return

    # ================================
    # Header
    # ================================

    header_cells = rows[0].findall(
        "ss:Cell",
        NAMESPACE
    )

    headers = [
        get_value(cell)
        for cell in header_cells
    ]

    if headers:
        headers[0] = "_ROW"

    for i, header in enumerate(headers):

        if header is None or header == "":
            headers[i] = f"_COLUMN_{i + 1}"

    # ================================
    # Rows
    # ================================

    result = []

    for row in rows[1:]:

        cells = row.findall(
            "ss:Cell",
            NAMESPACE
        )

        values = [
            get_value(cell)
            for cell in cells
        ]

        while len(values) < len(headers):
            values.append(None)

        record = dict(
            zip(headers, values)
        )

        result.append(record)

    # ================================
    # JSON
    # ================================

    json_file = (
        JSON_DIR
        / f"{xml_file.stem}.json"
    )

    JSON_DIR.mkdir(exist_ok=True)

    with open(
        json_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            result,
            file,
            ensure_ascii=False,
            indent=4
        )

    print(
        f"✅ تم إنشاء: {json_file.name}"
    )

    print(
        f"   عدد السجلات: {len(result)}"
    )


def main():

    xml_files = sorted(
        XML_DIR.glob("*.xml")
    )

    if not xml_files:

        print(
            "❌ لا توجد ملفات XML "
            "داخل مجلد xml"
        )

        return

    print(
        f"تم العثور على "
        f"{len(xml_files)} ملف XML\n"
    )

    success = 0
    failed = 0

    for xml_file in xml_files:

        try:

            convert_xml_to_json(xml_file)

            success += 1

        except Exception as error:

            print(
                f"❌ خطأ في "
                f"{xml_file.name}: {error}"
            )

            failed += 1

        print("-" * 50)

    print()
    print("✅ انتهى التحويل")
    print(f"نجح: {success}")
    print(f"فشل: {failed}")


if __name__ == "__main__":
    main()