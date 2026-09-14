from pathlib import Path
import xml.etree.ElementTree as ET
import json
import re


BASE_DIR = Path(__file__).resolve().parent.parent

XML_DIR = BASE_DIR / "xml"
JSON_DIR = BASE_DIR / "json"

JSON_DIR.mkdir(exist_ok=True)


NAMESPACE = {
    "ss": "urn:schemas-microsoft-com:office:spreadsheet"
}

SS = "{urn:schemas-microsoft-com:office:spreadsheet}"


def clean_xml(text):
    """
    تنظيف أكثر المشاكل الشائعة التي تجعل XML غير صالح.
    """

    # إزالة المحارف غير المسموحة في XML 1.0
    text = "".join(
        char for char in text
        if (
            char == "\t"
            or char == "\n"
            or char == "\r"
            or ord(char) >= 32
        )
    )

    # تحويل & غير الصالحة إلى &amp;
    # مع عدم المساس بـ:
    # &amp;
    # &lt;
    # &#123;
    # &#x123;
    text = re.sub(
        r'&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9a-fA-F]+;)',
        '&amp;',
        text
    )

    return text


def load_xml(xml_file):
    """
    محاولة قراءة XML بشكل طبيعي.
    إذا فشل، يتم تنظيف الملف وإعادة المحاولة.
    """

    try:
        return ET.parse(xml_file)

    except ET.ParseError as error:

        print(f"⚠️ XML غير صالح: {error}")
        print("   محاولة إصلاحه تلقائياً...")

        # utf-8-sig يعالج وجود BOM أيضاً
        text = xml_file.read_text(
            encoding="utf-8-sig",
            errors="replace"
        )

        text = clean_xml(text)

        try:
            root = ET.fromstring(text)

            print("✅ تم إصلاح XML مؤقتاً")

            return ET.ElementTree(root)

        except ET.ParseError as second_error:
            print(f"❌ فشل الإصلاح: {second_error}")
            raise


def get_value(cell):

    data = cell.find("ss:Data", NAMESPACE)

    if data is None:
        return None

    value = data.text

    if value is None or value == "":
        return None

    data_type = data.attrib.get(f"{SS}Type")

    if data_type == "Number":

        try:
            number = float(value)

            if number.is_integer():
                return int(number)

            return number

        except ValueError:
            return value

    if data_type == "Boolean":
        return value.lower() in ("1", "true")

    return value


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