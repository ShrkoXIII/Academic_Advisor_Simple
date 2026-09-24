"""Reusable helpers for Spreadsheet XML exports."""

import re
import xml.etree.ElementTree as ET


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
