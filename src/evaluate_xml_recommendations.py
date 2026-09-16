"""Evaluate approved XML candidate lists against observed target-semester outcomes.

The XML PART_ID is deliberately treated as diagnostic only.  The target part is
an explicit command-line contract because those export rows can retain a part
from their originating request rather than the recommendation request.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd

from .clean_student_status import clean_student_status
from .cleaning_utils import clean_column_names, clean_id
from .paths import (
    CLEAN_DEGREE_COURSE_PATH,
    CLEAN_STUDENT_COURSE_PATH,
    CLEAN_STUDENT_DIPLOMA_PATH,
    EVALUATION_DIR,
    STUDENT_STATUS_PATH,
)
from .recommendation import (
    AcademicPlanRecommender,
    build_plan_rows,
    project_cumulative_gpa,
    summarize_scored_plans,
)
from .recommendation_inputs import (
    CandidateImportError,
    build_student_snapshot,
    normalize_candidates,
    validate_snapshot,
)
from .xml_2_json import NAMESPACE, clean_xml, get_value


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xml-dir", type=Path, default=Path("xml"))
    parser.add_argument("--target-part", type=int, required=True)
    parser.add_argument("--history-as-of-part", type=int, required=True)
    parser.add_argument("--min-credits", type=float, default=12)
    parser.add_argument("--max-credits", type=float, default=18)
    parser.add_argument("--top-n", type=int, default=3)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--output-dir", type=Path)
    return parser.parse_args()


def json_value(value):
    """Convert pandas/numpy values to strict JSON values."""
    if isinstance(value, dict):
        return {str(k): json_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_value(v) for v in value]
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, (float, np.floating)):
        return float(value) if np.isfinite(value) else None
    if value is None or pd.isna(value):
        return None
    if isinstance(value, Path):
        return str(value)
    return value


def write_json(path, payload):
    path.write_text(json.dumps(json_value(payload), ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")


def xml_rows(path):
    """Read Spreadsheet XML and report whether an in-memory repair was needed."""
    try:
        tree = ET.parse(path)
        repaired = False
    except ET.ParseError:
        root = ET.fromstring(clean_xml(path.read_text(encoding="utf-8-sig", errors="replace")))
        tree, repaired = ET.ElementTree(root), True
    worksheet = tree.getroot().find(".//ss:Worksheet", NAMESPACE)
    if worksheet is None:
        raise ValueError("لم يتم العثور على Worksheet")
    rows = worksheet.findall("./ss:Table/ss:Row", NAMESPACE)
    if len(rows) < 2:
        raise ValueError("لا توجد صفوف بيانات في XML")
    headers = [get_value(cell) for cell in rows[0].findall("ss:Cell", NAMESPACE)]
    if headers:
        headers[0] = "_ROW"
    headers = [header if header not in (None, "") else f"_COLUMN_{i + 1}" for i, header in enumerate(headers)]
    records = []
    for row in rows[1:]:
        values = [get_value(cell) for cell in row.findall("ss:Cell", NAMESPACE)]
        values.extend([None] * (len(headers) - len(values)))
        records.append(dict(zip(headers, values)))
    return pd.DataFrame(records), repaired


def source_candidates(raw):
    """Keep only fields that define candidates; intentionally omit XML PART_ID."""
    rows = clean_column_names(raw)
    columns = [c for c in ["student_id", "course_id", "course_credits", "is_requestable", "course_name_sl"] if c in rows]
    required = {"student_id", "course_id", "course_credits"}
    missing = required - set(columns)
    if missing:
        raise ValueError(f"أعمدة XML مفقودة: {sorted(missing)}")
    return rows[columns].copy(), rows


def one_id(rows, name):
    values = clean_id(rows[name]).dropna().unique().tolist()
    if len(values) != 1:
        raise ValueError(f"يتطلب XML قيمة واحدة لـ {name}: {values}")
    return values[0]


def actual_metrics(status_row, actual):
    total_reg = float(status_row.total_reg_credits)
    semester_reg = float(status_row.semester_reg_credits)
    start_gpa = float(status_row.start_agpa_points)
    semester_gpa = float(status_row.gpa_points)
    denominator = total_reg + semester_reg
    calculated = ((semester_reg * semester_gpa) + (total_reg * start_gpa)) / denominator if denominator else None
    actual = actual.copy()
    credits = pd.to_numeric(actual.get("course_credits"), errors="coerce") if len(actual) else pd.Series(dtype=float)
    points = pd.to_numeric(actual.get("points"), errors="coerce") if len(actual) else pd.Series(dtype=float)
    valid = credits.notna() & points.notna() & credits.gt(0)
    cleaned_gpa = float(np.average(points[valid], weights=credits[valid])) if valid.any() else None
    return {
        "actual_source_semester_gpa": semester_gpa,
        "actual_source_semester_courses": int(status_row.semester_reg_courses),
        "actual_source_semester_credits": semester_reg,
        "actual_source_prior_credits": total_reg,
        "actual_source_start_cumulative_gpa": start_gpa,
        "actual_cumulative_gpa_formula": calculated,
        "actual_published_end_cumulative_gpa": float(status_row.end_agpa_points),
        "actual_formula_minus_published": calculated - float(status_row.end_agpa_points) if calculated is not None else None,
        "actual_cleaned_course_count": int(len(actual)),
        "actual_cleaned_credits": float(credits[valid].sum()),
        "actual_cleaned_plan_gpa": cleaned_gpa,
        "actual_cleaned_failed_credits": float(credits[valid & points.lt(2)].sum()),
    }


def observed_plan_estimate(engine, snapshot, actual, catalog, history, student_id, degree_id, target_part):
    if actual.empty:
        return {"status": "no_cleaned_actual_courses"}
    try:
        actual_candidates, _ = normalize_candidates(
            actual[["course_id", "course_credits"]].drop_duplicates("course_id"),
            catalog, history, student_id, degree_id, target_part,
        )
        prepared = engine.prepare_candidates(snapshot, actual_candidates, target_part)
        scored = engine.score_rows(build_plan_rows(prepared, [tuple(range(len(prepared)))], first_plan_id=-1))
        summary = summarize_scored_plans(
            scored, snapshot["start_agpa_points"], snapshot["prior_total_reg_credits"],
        ).iloc[0].to_dict()
        courses = scored[[
            "course_id", "course_name", "course_credits", "expected_points", "fail_probability",
        ]].sort_values("course_id", kind="stable").to_dict("records")
        return {"status": "ok", **summary, "courses": courses}
    except Exception as error:  # An actual plan can include rows outside the current catalog contract.
        return {"status": "unavailable", "reason": str(error)}


def course_overlap(recommendation, actual_ids):
    recommended_ids = {str(c["course_id"]) for c in recommendation.get("courses", [])}
    shared = sorted(recommended_ids & actual_ids)
    union = recommended_ids | actual_ids
    return {
        "recommended_course_count": len(recommended_ids),
        "shared_actual_course_ids": shared,
        "shared_actual_course_count": len(shared),
        "jaccard_with_actual": len(shared) / len(union) if union else None,
    }


def markdown_number(value, digits=3):
    return "—" if value is None or (isinstance(value, float) and not np.isfinite(value)) else f"{float(value):.{digits}f}"


def course_text(courses):
    if not courses:
        return "—"
    return "، ".join(f"{c['course_id']} ({markdown_number(c.get('course_credits'), 1)} س)" for c in courses)


def report_markdown(cases, args, run_dir):
    successful = [case for case in cases if case["status"] == "ok"]
    lines = [
        "# تقرير تقييم توصيات XML — الفصل 20251",
        "",
        f"- عدد الملفات: **{len(cases)}**؛ الحالات المنفذة: **{len(successful)}**.",
        f"- فصل التوصية ثابت بطلب المستخدم: **{args.target_part}**. تاريخ الحالة التاريخية للنموذج: **{args.history_as_of_part}**.",
        f"- نطاق الخطة: **{args.min_credits:g}–{args.max_credits:g} ساعة**، وأفضل **{args.top_n}** خطط محفوظة لكل حالة حيث توجد خطط مطابقة.",
        "- توقعات أفضل الخطط هي بدائل مضادة للواقع؛ لا تعني أن الطالب كان سيحققها لو اختارها. تقييم النموذج على اختيار الطالب نفسه يظهر منفصلًا عندما يكون متاحًا.",
        "",
        "## المعادلات المستخدمة",
        "",
        "- المعدل العام المتوقع للخطة = `(ساعات الخطة × معدل الخطة المتوقع + total_reg_credits × start_agpa_points) ÷ (ساعات الخطة + total_reg_credits)`.",
        "- المعدل العام الفعلي المقارن = `(semester_reg_credits × gpa_points + total_reg_credits × start_agpa_points) ÷ (semester_reg_credits + total_reg_credits)`.",
        "- `total_reg_credits` هو رصيد الساعات المسجلة قبل الفصل داخل لقطة البداية؛ أما `semester_reg_credits` و`gpa_points` فهما ناتجا الفصل الفعليان من سجل الحالة.",
        "- لا تطبق هذه الصيغة سياسة استبدال علامات الإعادة؛ أي خطة تضم مقررًا معادًا تحمل إشارة خاصة في المخرجات.",
        "",
        "## ملخص الحالات",
        "",
        "|XML|الطالب|الخطط المطابقة|أفضل معدل عام متوقع|المعدل العام الفعلي|الفرق المتوقع−الفعلي|التقاطع مع اختيار الطالب|",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for case in cases:
        if case["status"] != "ok":
            lines.append(f"|{case['xml_file']}|—|—|—|—|—|فشل الإدخال: {case['error']}|")
            continue
        metric, best, overlap = case["metrics"], case["recommendations"][0] if case["recommendations"] else None, case["top1_overlap"]
        lines.append(
            f"|{case['xml_file']}|{case['student_id']}|{case['result']['matching_plan_count']}|"
            f"{markdown_number(best.get('projected_cumulative_gpa') if best else None)}|"
            f"{markdown_number(metric['actual_cumulative_gpa_formula'])}|"
            f"{markdown_number((best.get('projected_cumulative_gpa') if best else np.nan) - metric['actual_cumulative_gpa_formula'] if best and metric['actual_cumulative_gpa_formula'] is not None else None)}|"
            f"{overlap.get('shared_actual_course_count', 0)}/{metric['actual_cleaned_course_count']}|")
    for index, case in enumerate(cases, 1):
        lines.extend(["", f"## الحالة {index}: {case['xml_file']}", ""])
        if case["status"] != "ok":
            lines.extend([f"تعذر تنفيذ هذه الحالة: `{case['error']}`.", ""])
            continue
        result, metrics = case["result"], case["metrics"]
        lines.extend([
            f"- الطالب/البرنامج: **{case['student_id']} / {case['degree_id']}**؛ فصل الهدف: **{args.target_part}**.",
            f"- قائمة XML: {case['raw_rows']} صفًا، وبعد اختيار الصفوف القابلة للطلب وتطبيعها: **{case['candidate_count']} مقررًا**. القيم التشخيصية لـ `PART_ID` في XML: `{case['xml_part_values'] or 'فارغ'}`.",
            f"- حالة البداية: معدل عام **{markdown_number(metrics['actual_source_start_cumulative_gpa'])}** على **{markdown_number(metrics['actual_source_prior_credits'], 1)} ساعة**.",
            f"- الواقع المسجل: معدل فصل **{markdown_number(metrics['actual_source_semester_gpa'])}** على **{markdown_number(metrics['actual_source_semester_credits'], 1)} ساعة**؛ المعدل العام الفعلي بالمعادلة **{markdown_number(metrics['actual_cumulative_gpa_formula'])}**، والمنشور في المصدر **{markdown_number(metrics['actual_published_end_cumulative_gpa'])}** (فرق **{markdown_number(metrics['actual_formula_minus_published'])}**).",
            f"- مواد الاختيار الفعلية النظيفة: **{metrics['actual_cleaned_course_count']}** مقررًا / **{markdown_number(metrics['actual_cleaned_credits'], 1)} ساعة**؛ منها الموجودة في قائمة XML: **{case['actual_courses_in_xml']}**.",
            "",
            "|الرتبة|الخطة|مواد/ساعات|معدل الخطة المتوقع|المعدل العام المتوقع|التحسن من البداية|ساعات رسوب متوقعة|المشترك مع الفعلي|",
            "|---:|---:|---:|---:|---:|---:|---:|---:|",
        ])
        for rec in case["recommendations"]:
            overlap = course_overlap(rec, set(case["actual_course_ids"]))
            lines.append(
                f"|{rec['rank']}|{rec['plan_id']}|{rec['course_count']}/{markdown_number(rec['total_credits'], 1)}|"
                f"{markdown_number(rec['expected_plan_gpa'])}|{markdown_number(rec['projected_cumulative_gpa'])}|"
                f"{markdown_number(rec['expected_cumulative_gpa_gain'])}|{markdown_number(rec['expected_failed_credits'], 2)}|"
                f"{overlap['shared_actual_course_count']}/{metrics['actual_cleaned_course_count']}|")
        if not case["recommendations"]:
            lines.append("|—|—|لا توجد خطة تحقق نطاق الساعات|—|—|—|—|—|")
        lines.extend(["", "### تفاصيل أفضل خطة", ""])
        if case["recommendations"]:
            best = case["recommendations"][0]
            lines.extend([
                "|المقرر|الاسم|الساعات|النقاط المتوقعة|احتمال الرسوب|",
                "|---|---|---:|---:|---:|",
            ])
            for course in best["courses"]:
                lines.append(
                    f"|{course['course_id']}|{course.get('course_name') or '—'}|"
                    f"{markdown_number(course.get('course_credits'), 1)}|"
                    f"{markdown_number(course.get('expected_points'))}|"
                    f"{markdown_number(course.get('fail_probability'))}|"
                )
            if best.get("projected_gpa_requires_repeat_policy"):
                lines.append("إشارة: تحتوي الخطة على مقرر له محاولة سابقة في السجل النظيف؛ المعدل العام المتوقع جمعٌ إضافي حتى تتوفر سياسة الإعادة الرسمية.")
        lines.extend(["", "### إشارات المقارنة", ""])
        if case["recommendations"]:
            best = case["recommendations"][0]
            actual_gpa = metrics["actual_cumulative_gpa_formula"]
            lines.append(f"- فرق أفضل بديل متوقع عن المعدل العام الفعلي: **{markdown_number(best['projected_cumulative_gpa'] - actual_gpa if actual_gpa is not None else None)}**. هذه مقارنة بديل غير مختار بالواقع، وليست قياس دقة سببي.")
        else:
            lines.append("- لا يمكن توليد خطة في نطاق 12–18 ساعة من قائمة المرشحين المعتمدة.")
        overlap = case["top1_overlap"]
        lines.append(f"- تقاطع أفضل خطة مع اختيار الطالب: **{overlap.get('shared_actual_course_count', 0)}** مقررًا؛ جاكارد **{markdown_number(overlap.get('jaccard_with_actual'))}**.")
        best = case["recommendations"][0] if case["recommendations"] else None
        lines.extend([
            "",
            "### مقارنة الحمل الدراسي",
            "",
            "|الخطة|عدد المقررات|الساعات|",
            "|---|---:|---:|",
            f"|أفضل خطة للمودل|{best['course_count'] if best else 'لا توجد خطة'}|{markdown_number(best['total_credits'], 1) if best else None}|",
            f"|اختيار الطالب الفعلي في سجل الفصل|{metrics['actual_source_semester_courses']}|{markdown_number(metrics['actual_source_semester_credits'], 1)}|",
            f"|المواد الفعلية المتاحة في سجل التقييم النظيف|{metrics['actual_cleaned_course_count']}|{markdown_number(metrics['actual_cleaned_credits'], 1)}|",
        ])
        observed = case["observed_plan_estimate"]
        if observed["status"] == "ok":
            lines.extend([
                "",
                "### تقدير النموذج للخطة التي اختارها الطالب",
                "",
                "|مواد/ساعات الخطة الفعلية|معدل الفصل المتوقع|المعدل العام المتوقع للخطة الفعلية|المعدل العام الفعلي|فرق المتوقع−الفعلي|",
                "|---:|---:|---:|---:|---:|",
                f"|{observed['course_count']}/{markdown_number(observed['total_credits'], 1)}|"
                f"{markdown_number(observed['expected_plan_gpa'])}|"
                f"**{markdown_number(observed['projected_cumulative_gpa'])}**|"
                f"{markdown_number(metrics['actual_cumulative_gpa_formula'])}|"
                f"{markdown_number(observed['projected_cumulative_gpa'] - metrics['actual_cumulative_gpa_formula'] if metrics['actual_cumulative_gpa_formula'] is not None else None)}|",
                "",
                "توقع النموذج لكل مادة في تشكيلة الطالب الفعلية:",
                "",
                "|المقرر|الاسم|الساعات|النقاط المتوقعة|احتمال الرسوب|",
                "|---|---|---:|---:|---:|",
            ])
            for course in observed["courses"]:
                lines.append(
                    f"|{course['course_id']}|{course.get('course_name') or '—'}|"
                    f"{markdown_number(course.get('course_credits'), 1)}|"
                    f"{markdown_number(course.get('expected_points'))}|"
                    f"{markdown_number(course.get('fail_probability'))}|"
                )
        else:
            lines.append(f"- لم يتوفر تقدير نموذج لخطة الطالب الفعلية: {observed.get('reason', observed['status'])}.")
        if case["xml_repaired"]:
            lines.append("- تم إصلاح XML في الذاكرة بسبب صياغة غير صالحة؛ لم يُعدّل الملف الأصلي.")
        if case.get("mixed_student_xml_rows_excluded", 0):
            lines.append(
                f"- الملف يجمع **{case['mixed_student_xml_rows_excluded']}** صفًا لطالب آخر؛ "
                "قُيِّمت هوية الصف الأول فقط وحُفظ التعارض بدل دمج قائمتين مختلفتين."
            )
        if str(args.target_part) not in case["xml_part_values"] and case["xml_part_values"]:
            lines.append("- `PART_ID` داخل XML لا يساوي فصل الهدف؛ عومل كإشارة منشأ فقط لأن فصل التقييم محدد صراحةً من المستخدم.")
        lines.append("")
    lines.extend(["## الملفات الناتجة", "", f"مجلد التشغيل: `{run_dir}`. يحتوي على `summary.parquet` و`report_ar.md` وملف JSON مستقل لكل حالة."])
    return "\n".join(lines)


def run_case(path, engine, status, history, diplomas, catalog, args, run_dir):
    raw, repaired = xml_rows(path)
    candidates_raw, diagnostic = source_candidates(raw)
    raw_student_ids = clean_id(candidates_raw["student_id"])
    student_id = raw_student_ids.dropna().iloc[0]
    foreign_rows = int(raw_student_ids.ne(student_id).sum())
    candidates_raw = candidates_raw.loc[raw_student_ids.eq(student_id)].copy()
    target_status = status[(status.student_id.eq(student_id)) & status.part_id.eq(args.target_part)]
    if len(target_status) != 1:
        raise ValueError(f"لا توجد حالة هدف فريدة للطالب في {args.target_part}: {len(target_status)}")
    degree_id = str(target_status.iloc[0].degree_id)
    candidates, import_report = normalize_candidates(
        candidates_raw, catalog, history, student_id, degree_id, args.target_part,
    )
    snapshot = validate_snapshot(
        build_student_snapshot(status, history, diplomas, student_id, degree_id, args.target_part),
        student_id, degree_id, args.target_part,
    )
    all_plans, result = engine.recommend(
        snapshot, candidates, args.target_part, snapshot["start_agpa_points"],
        min_credits=args.min_credits, max_credits=args.max_credits, top_n=args.top_n,
    )
    actual = history[(history.student_id.eq(student_id)) & (history.degree_id.eq(degree_id)) & (history.part_id.eq(args.target_part))].copy()
    status_row = target_status.iloc[0]
    metrics = actual_metrics(status_row, actual)
    actual_ids = set(actual.course_id.astype(str))
    recommendations = result["recommendations"]
    xml_ids = set(candidates.course_id.astype(str))
    source_parts = sorted({str(x) for x in diagnostic.get("part_id", pd.Series(dtype="string")).dropna().tolist()})
    payload = {
        "status": "ok", "xml_file": path.name, "xml_sha256": sha256(path.read_bytes()).hexdigest(),
        "xml_repaired": repaired, "raw_rows": len(raw), "student_id": student_id, "degree_id": degree_id,
        "target_part": args.target_part, "history_as_of_part": args.history_as_of_part,
        "xml_part_values": source_parts, "candidate_count": len(candidates), "candidate_import": import_report,
        "snapshot": snapshot, "result": result, "metrics": metrics,
        "recommendations": recommendations, "actual_course_ids": sorted(actual_ids),
        "actual_courses_in_xml": int(len(actual_ids & xml_ids)),
        "top1_overlap": course_overlap(recommendations[0], actual_ids) if recommendations else {},
        "mixed_student_xml_rows_excluded": foreign_rows,
        "observed_plan_estimate": observed_plan_estimate(
            engine, snapshot, actual, catalog, history, student_id, degree_id, args.target_part,
        ),
    }
    stem = re.sub(r"[^A-Za-z0-9]+", "_", path.stem).strip("_")
    case_dir = run_dir / f"{stem}_{student_id.replace('.', '_')}"
    case_dir.mkdir()
    write_json(case_dir / "case.json", payload)
    candidates.to_parquet(case_dir / "candidates.parquet", index=False)
    actual.to_parquet(case_dir / "actual_cleaned_courses.parquet", index=False)
    pd.DataFrame(recommendations).drop(columns=["courses"], errors="ignore").to_parquet(case_dir / "top_plans.parquet", index=False)
    return payload


def main():
    args = parse_args()
    xml_files = sorted(args.xml_dir.glob("*.xml"), key=lambda path: [int(x) if x.isdigit() else x.lower() for x in re.split(r"(\d+)", path.name)])
    if not xml_files:
        raise SystemExit(f"لا توجد ملفات XML في {args.xml_dir}")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = args.output_dir or EVALUATION_DIR / "xml_recommendations" / f"target_{args.target_part}_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=False)
    status = clean_student_status(pd.read_parquet(STUDENT_STATUS_PATH))
    history = pd.read_parquet(CLEAN_STUDENT_COURSE_PATH)
    diplomas = pd.read_parquet(CLEAN_STUDENT_DIPLOMA_PATH)
    catalog = pd.read_parquet(CLEAN_DEGREE_COURSE_PATH)
    engine = AcademicPlanRecommender.load(history_as_of_part=args.history_as_of_part, num_threads=args.threads)
    cases = []
    for path in xml_files:
        try:
            case = run_case(path, engine, status, history, diplomas, catalog, args, run_dir)
            print(f"OK {path.name}: {case['result']['matching_plan_count']} plans")
        except Exception as error:
            case = {"status": "error", "xml_file": path.name, "error": f"{type(error).__name__}: {error}"}
            print(f"ERROR {path.name}: {case['error']}")
        cases.append(case)
    summary = pd.DataFrame([
        {
            "xml_file": c["xml_file"], "status": c["status"], "student_id": c.get("student_id"),
            "degree_id": c.get("degree_id"), "candidate_count": c.get("candidate_count"),
            "matching_plan_count": c.get("result", {}).get("matching_plan_count"),
            "best_projected_cumulative_gpa": c.get("result", {}).get("best_projected_cumulative_gpa"),
            "actual_cumulative_gpa_formula": c.get("metrics", {}).get("actual_cumulative_gpa_formula"),
            "actual_published_end_cumulative_gpa": c.get("metrics", {}).get("actual_published_end_cumulative_gpa"),
            "top1_shared_actual_course_count": c.get("top1_overlap", {}).get("shared_actual_course_count"),
        } for c in cases
    ])
    summary.to_parquet(run_dir / "summary.parquet", index=False)
    write_json(run_dir / "run_manifest.json", {
        "created_at_utc": datetime.now(timezone.utc).isoformat(), "arguments": vars(args),
        "xml_files": [path.name for path in xml_files], "model_provenance": engine.provenance,
        "formula": {
            "expected": "(plan_credits * expected_plan_gpa + total_reg_credits * start_agpa_points) / (plan_credits + total_reg_credits)",
            "actual": "(semester_reg_credits * gpa_points + total_reg_credits * start_agpa_points) / (semester_reg_credits + total_reg_credits)",
        },
    })
    (run_dir / "report_ar.md").write_text(report_markdown(cases, args, run_dir), encoding="utf-8")
    print(f"REPORT {run_dir}")
    if any(case["status"] == "error" for case in cases):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
