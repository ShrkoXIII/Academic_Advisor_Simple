"""Offline Arabic reports for the isolated XML 47 versus 33-to-47 experiment.

Rendering consumes recorded results only: it never loads inputs, runs inference,
fills missing measurements with zero, or changes production ranking behavior.
"""
from html import escape
import json
import math
from pathlib import Path


_FILES = {
    "experiment_01": "experiment_01_47_exhaustive.html",
    "experiment_02": "experiment_02_33_to_47.html",
    "comparison": "comparison.html",
}
_TITLES = {
    "experiment_01": "التجربة الأولى · البحث الكامل بـ 47 ميزة",
    "experiment_02": "التجربة الثانية · الترشيح بـ 33 ثم التقييم بـ 47",
    "comparison": "مقارنة التجربتين · الدقة والزمن والاحتفاظ بالبدائل",
}
_CSS = """
:root{color-scheme:light;--navy:#102a43;--teal:#087f8c;--amber:#b7791f;--bg:#eef3f7;
--ink:#18354d;--muted:#60758b;--border:#dce5ed;--white:#fff;--red:#a33340}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);
color:var(--ink);font-family:Tahoma,"Segoe UI",Arial,sans-serif;font-size:15px;line-height:1.85}
a{color:var(--teal);text-decoration:none}a:hover{text-decoration:underline}code,.tech{direction:ltr;
unicode-bidi:isolate;font-family:Consolas,"Courier New",monospace;font-size:.9em}bdi{unicode-bidi:isolate}
.shell{max-width:1440px;margin:auto;padding:28px}.hero{background:linear-gradient(125deg,#102a43,#14596a);
color:white;border-radius:22px;padding:34px 38px;box-shadow:0 14px 40px #102a4315}.eyebrow{color:#a4e1e4;
font-size:13px;letter-spacing:1px}.hero h1{font-size:28px;line-height:1.55;margin:8px 0 12px}.hero p{max-width:1000px;
color:#dfecf4;margin:0}.nav{display:flex;gap:10px;flex-wrap:wrap;margin-top:23px}.nav a{border:1px solid #ffffff45;
padding:7px 16px;border-radius:10px;color:white}.nav a.active{background:#fff;color:var(--navy)}
.metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(185px,1fr));gap:14px;margin:24px 0}
.metric,.card,.chart{background:white;border:1px solid var(--border);border-radius:16px;padding:20px}
.metric .label{color:var(--muted);font-size:13px}.metric .value{font-size:27px;line-height:1.6;font-weight:700;
color:var(--navy)}.metric .hint{font-size:12px;color:var(--muted)}.metric.accent{border-top:3px solid var(--teal)}
.card{margin:20px 0;box-shadow:0 5px 20px #102a4305}.card h2{margin:0 0 12px;font-size:21px}
.card h3{font-size:17px;margin:20px 0 10px}.subtle{color:var(--muted);font-size:13px}.section-intro{margin:0 0 16px}
.case-title{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}
.case-meta{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0 18px}.pill{background:#f0f5f9;border-radius:8px;
padding:5px 11px;font-size:12px}.badge{display:inline-block;border-radius:99px;padding:3px 12px;
font-size:12px;background:#e4f4f2;color:#087360}.badge.warn{background:#fff2d7;color:#8d5c12}
.badge.fail{background:#fdebef;color:var(--red)}.notice{background:#f6fafc;border-right:4px solid var(--teal);
border-radius:10px;padding:13px 17px;margin:15px 0}.notice.warning{background:#fff8e9;border-color:#dcac42}
.notice p{margin:4px 0}.grid-two{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}
.plan{border:1px solid var(--border);border-radius:14px;padding:18px;margin:14px 0;border-top:3px solid var(--teal)}
.plan h3{margin:0 0 10px}.plan-metrics{display:flex;gap:22px;flex-wrap:wrap;margin:10px 0 16px}
.plan-metrics span{display:block;color:var(--muted);font-size:12px}.plan-metrics strong{font-size:20px}
.table-wrap{overflow-x:auto;border:1px solid var(--border);border-radius:10px;margin:12px 0}
table{border-collapse:collapse;width:100%;white-space:nowrap;font-size:13px}th{background:#f1f6fa;color:var(--navy);
font-weight:600;text-align:right;padding:11px 13px}td{padding:10px 13px;border-top:1px solid #e5ecf2;
vertical-align:top}tbody tr:nth-child(even){background:#fbfdfe}tbody tr:hover{background:#f0f8fa}
td.name{white-space:normal;min-width:150px}.empty{color:var(--muted);padding:12px}.missing{color:#8796a5}
details{border:1px solid var(--border);border-radius:10px;margin:12px 0;background:#fff}
summary{cursor:pointer;font-weight:600;padding:12px 16px;background:#f8fafc;border-radius:10px}
.detail-body{padding:6px 16px 16px}pre{direction:ltr;text-align:left;white-space:pre-wrap;overflow-wrap:anywhere;
font-family:Consolas,"Courier New",monospace;font-size:12px;background:#f5f8fb;padding:16px;border-radius:10px}
.data-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:8px 16px;margin:10px 0}
.data-grid>div{border-bottom:1px solid #edf2f6;padding:7px 0}.data-grid dt{color:var(--muted);font-size:12px;
overflow-wrap:anywhere}.data-grid dd{margin:0;font-size:14px;overflow-wrap:anywhere}
.chart-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:16px;margin:20px 0}
.chart h3{margin:0 0 8px;font-size:16px}.chart svg{display:block;width:100%;height:auto;direction:ltr}
.legend{display:flex;gap:16px;font-size:12px;color:var(--muted);flex-wrap:wrap}.dot{display:inline-block;
width:10px;height:10px;border-radius:3px;margin-left:6px}.footer{color:var(--muted);font-size:12px;margin:25px 4px}
@media(max-width:760px){.shell{padding:12px}.hero{padding:23px 20px;border-radius:16px}.hero h1{font-size:22px}
.card{padding:16px}.grid-two{grid-template-columns:1fr}.chart-grid{grid-template-columns:1fr}.metrics{grid-template-columns:
repeat(2,minmax(0,1fr))}.metric{padding:14px}.metric .value{font-size:23px}.case-meta{gap:5px}}
@media print{body{background:white}.hero{background:#102a43!important;print-color-adjust:exact}.shell{padding:0}
.card,.plan{break-inside:avoid}.nav{display:none}.table-wrap{overflow:visible}details{display:block}}
"""


def _finite(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) else None


def _text(value):
    if value is None:
        return "—"
    if isinstance(value, float) and not math.isfinite(value):
        return "—"
    return str(value)


def _value(value, *, digits=3):
    if value is None or isinstance(value, float) and not math.isfinite(value):
        return '<span class="missing" title="غير متاح">—</span>'
    if isinstance(value, bool):
        return "نعم" if value else "لا"
    if isinstance(value, (int, float)):
        rendered = str(value) if isinstance(value, int) else f"{value:.{digits}f}"
    elif isinstance(value, (list, tuple)):
        rendered = "، ".join(_text(item) for item in value)
    elif isinstance(value, dict):
        return _structured(value)
    else:
        rendered = str(value)
    return f'<bdi>{escape(rendered)}</bdi>'


def _clean_json(value):
    if isinstance(value, dict):
        return {str(key): _clean_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean_json(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _structured(value):
    content = json.dumps(_clean_json(value), ensure_ascii=False, indent=2, default=str, allow_nan=False)
    return f"<pre>{escape(content)}</pre>"


def _details(title, body):
    return f'<details><summary>{escape(title)}</summary><div class="detail-body">{body}</div></details>'


def _table(headers, rows):
    head = "".join(f"<th>{escape(label)}</th>" for label in headers)
    body = "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows)
    if not body:
        body = f'<tr><td class="empty" colspan="{len(headers)}">غير متاح · لا توجد صفوف مسجلة</td></tr>'
    return f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def _data(items):
    rows = "".join(f"<div><dt>{escape(label)}</dt><dd>{_value(value)}</dd></div>" for label, value in items)
    return f'<dl class="data-grid">{rows}</dl>'


def _metric(label, value, hint="", *, digits=3):
    return (f'<div class="metric accent"><div class="label">{escape(label)}</div>'
            f'<div class="value">{_value(value, digits=digits)}</div>'
            f'<div class="hint">{escape(hint)}</div></div>')


def _badge(status):
    status_text = _text(status)
    lowered = status_text.lower()
    css = "fail" if any(word in lowered for word in ("fail", "error", "blocked")) else (
        "warn" if lowered not in {"success", "ok", "available", "completed"} else "")
    labels = {"success": "نجاح", "ok": "نجاح", "available": "متاح", "failed": "فشل", "blocked": "تعذر التنفيذ",
              "no_feasible_plans": "لا توجد خطة تحقق القيود", "no_feasible_plan": "لا توجد خطة تحقق القيود",
              "no_feasible": "لا توجد خطة تحقق القيود", "no_feasible_18_credit_plan": "لا توجد خطة تحقق 18 ساعة"}
    label = labels.get(lowered)
    content = f'{escape(label)} · <bdi>{escape(status_text)}</bdi>' if label else escape(status_text)
    return f'<span class="badge {css}">{content}</span>'


def _warnings(warnings):
    if not warnings:
        return ""
    values = warnings if isinstance(warnings, (list, tuple)) else [warnings]
    translations = {
        "Raw and cleaned registration counts/credits differ; per-course exclusions are retained.":
            "تختلف أعداد المقررات أو الساعات بين المصدر الخام والبيانات المنظفة؛ أسباب الاستبعاد محفوظة لكل مقرر.",
        "Raw course credits differ from published semester_reg_credits.":
            "مجموع ساعات المقررات الخام يختلف عن ساعات الفصل المنشورة في المصدر.",
        "Calculated course GPA differs from published gpa_points; university rounding/repeat rules are not assumed.":
            "المعدل المحسوب من المقررات يختلف عن معدل الفصل المنشور؛ لم تُفترض قواعد تقريب أو استبدال للإعادات.",
        "Prerequisites, offering timetable, requirement caps, official failed/withdrawn-repeat caps and historical XML eligibility are unverified where absent from this export.":
            "لم تتحقق المتطلبات السابقة أو مواعيد الطرح أو حدود المتطلبات والإعادات أو أهلية التسجيل التاريخية عندما لا يوفرها التصدير.",
        "Full-roster predicted GPA includes courses excluded by the current observed-GPA cleaner; policy-aligned error uses the same GPA-bearing denominator after prediction.":
            "تنبؤ القائمة الخام يشمل مقررات يستبعدها تنظيف GPA الفعلي؛ يستخدم الخطأ المتوافق مع السياسة مقام المقررات المحتسبة نفسه بعد التنبؤ.",
        "Cumulative prediction is additive with prior registered credits; official repeat replacement and GPA denominator may differ.":
            "المعدل التراكمي المتوقع إسقاط جمعي باستخدام الساعات المسجلة السابقة؛ قد تختلف سياسة استبدال الإعادات ومقام GPA الرسمي.",
    }
    rendered = []
    for value in values:
        translated = translations.get(str(value))
        rendered.append(f'<p>{escape(translated)}</p><p class="subtle">{_value(value)}</p>' if translated else f"<p>{_value(value)}</p>")
    return '<div class="notice warning">' + "".join(rendered) + "</div>"


def _plan(plan, position):
    header = f'<h3>البديل {_value(plan.get("rank", position))} · {_value(plan.get("course_ids"))}</h3>'
    metrics = [
        ("المعدل الفصلي المتوقع", plan.get("expected_plan_gpa")),
        ("المعدل التراكمي المتوقع", plan.get("projected_cumulative_gpa")),
        ("التغير التراكمي المتوقع", plan.get("expected_cumulative_gpa_gain")),
        ("الساعات", plan.get("total_credits")),
    ]
    blocks = "".join(f"<div><span>{escape(label)}</span><strong>{_value(value)}</strong></div>" for label, value in metrics)
    courses = plan.get("courses") or []
    table = _table(["المقرر", "الاسم", "الساعات", "العلامة المتوقعة", "النقاط المتوقعة"], [
        [_value(course.get(key)) for key in ("course_id", "course_name", "course_credits", "predicted_mark", "expected_points")]
        for course in courses])
    repeat = ""
    if plan.get("projected_gpa_requires_repeat_policy"):
        repeat = '<p class="subtle">الإسقاط التراكمي جمعي؛ تحتوي الخطة إعادات تحتاج إلى سياسة استبدال رسمية.</p>'
    return f'<div class="plan">{header}<div class="plan-metrics">{blocks}</div>{table}{repeat}</div>'


def _observed(observed):
    observed = observed or {}
    metrics = [
        ("المعدل المتوقع للخطة الفعلية", observed.get("predicted_actual_plan_gpa")),
        ("المعدل الفعلي من المقررات", observed.get("actual_plan_gpa")),
        ("خطأ المعدل الفصلي (متوقع − فعلي)", observed.get("plan_gpa_error")),
        ("الخطأ المطلق للمعدل الفصلي", observed.get("absolute_plan_gpa_error")),
        ("المعدل المتوقع للمقررات المحتسبة في GPA فقط", observed.get("predicted_actual_gpa_bearing_plan_gpa")),
        ("الخطأ الفصلي المتوافق مع سياسة GPA", observed.get("policy_aligned_plan_gpa_error")),
        ("الخطأ المطلق المتوافق مع سياسة GPA", observed.get("policy_aligned_absolute_plan_gpa_error")),
        ("المعدل التراكمي المتوقع للخطة الفعلية", observed.get("predicted_actual_cumulative_gpa")),
        ("المعدل التراكمي المنشور في المصدر", observed.get("actual_published_end_cumulative_gpa")),
        ("خطأ المعدل التراكمي", observed.get("cumulative_gpa_error")),
        ("المعدل الفصلي المنشور في المصدر", observed.get("actual_source_semester_gpa")),
        ("زمن تنبؤ الخطة الفعلية · التجربة الأولى (ث)", observed.get("experiment_01_prediction_seconds")),
        ("زمن تنبؤ الخطة الفعلية · التجربة الثانية (ث)", observed.get("experiment_02_prediction_seconds")),
    ]
    table = _table(["المقرر", "الاسم", "الساعات", "النقاط المتوقعة", "النقاط الفعلية", "فرق النقاط",
                    "الحالة", "in_gpa", "محتسب في GPA"], [
        [_value(course.get(key)) for key in ("course_id", "course_name", "course_credits", "predicted_points",
                                             "actual_points", "points_error", "finish_status", "in_gpa", "gpa_included")]
        for course in observed.get("courses") or []])
    audit = _data([
        ("عدد المقررات الخام", observed.get("actual_raw_course_count")),
        ("عدد المقررات بعد التنظيف", observed.get("actual_cleaned_course_count")),
        ("ساعات الخطة الفعلية", observed.get("actual_total_credits")),
        ("الساعات الداخلة في حساب GPA", observed.get("gpa_bearing_credits")),
        ("الساعات بعد التنظيف", observed.get("actual_cleaned_credits")),
        ("ساعات الفصل المنشورة في المصدر", observed.get("actual_source_semester_credits")),
    ])
    roster_credits = _finite(observed.get("actual_total_credits"))
    gpa_credits = _finite(observed.get("gpa_bearing_credits"))
    denominator_warning = ""
    if roster_credits is not None and gpa_credits is not None and roster_credits != gpa_credits:
        denominator_warning = ('<div class="notice warning"><p>مقام التنبؤ على كل مقررات التسجيل يختلف عن مقام GPA الفعلي '
                               'بعد التنظيف. يجب قراءة خطأ القائمة الكاملة منفصلًا عن الخطأ المتوافق مع سياسة GPA.</p></div>')
    return ('<h3>الخطة الفعلية · تقييم مستقل لما سجله الطالب</h3>'
            '<p class="subtle">تُقيّم هذه الخطة بمقرراتها وسياقها الكامل بـ 47 ميزة. النتائج الفعلية تخص هذه الخطة فقط؛ '
            'لا تمثل نتائج فعلية للبدائل المقترحة. فرق النقاط = المتوقع − الفعلي.</p>'
            + _badge(observed.get("status")) + _data(metrics) + table + audit + denominator_warning
            + _warnings(observed.get("warnings"))
            + _details("تفاصيل القياس الفعلي وسياسة حساب GPA", _structured(observed)))


def _candidate_audit(case):
    flag_keys = ("eligible", "is_eligible", "allow_register", "is_requestable", "finish_status",
                 "previous_course_status", "previous_semantic_status", "eligibility_reason",
                 "exclusion_reason", "excluded_reason")
    rows = []
    for candidate in case.get("candidates") or []:
        flags = "<br>".join(f"<code>{escape(key)}</code>: {_value(candidate.get(key))}"
                            for key in flag_keys if key in candidate)
        rows.append([_value(candidate.get("course_id")), _value(candidate.get("course_name")),
                     _value(candidate.get("course_credits")), _value(candidate.get("attempt_number")),
                     flags or _value(None)])
    body = _table(["المقرر المرشح", "الاسم", "الساعات", "المحاولة", "حقول الأهلية والحالة"], rows)
    body += _details("تفاصيل المرشحين كما سُجلت", _structured(case.get("candidates")))
    return _details("تدقيق الإدخال والمرشحين", _data([
        ("ملف XML", case.get("xml_file")), ("عدد المرشحين", case.get("candidate_count"))])
        + _structured(case.get("input_audit")) + _details("لقطة الطالب", _structured(case.get("snapshot"))) + body)


def _shortlist(plans):
    rows = []
    for plan in plans or []:
        rows.append([_value(plan.get("course_ids")), _value(plan.get("total_credits")),
                     _value(plan.get("stage1_rank")), _value(plan.get("stage1_GPA")),
                     _value(plan.get("stage2_rank")), _value(plan.get("stage2_GPA")),
                     _value(plan.get("delta")), _value(plan.get("stage1_expected_plan_gpa")),
                     _value(plan.get("stage2_expected_plan_gpa")),
                     _value(plan.get("rank")), _value(plan.get("expected_plan_gpa"))])
    return _details("القائمة المختصرة · حتى 50 خطة", '<p class="subtle">تظهر رتب ومعدلات المرحلتين كما سُجلت؛ '
                    'أي قياس غير متاح يبقى فارغًا.</p>' + _table(
                        ["مقررات الخطة", "الساعات", "رتبة 33", "GPA تراكمي 33", "رتبة 47", "GPA تراكمي 47",
                         "التغير 47 − 33", "GPA فصلي 33", "GPA فصلي 47", "الرتبة النهائية", "GPA الفصلي النهائي"], rows))


def _case_report(case, index, experiment):
    result = case.get(experiment) or {}
    counts, timings = result.get("counts") or {}, result.get("timings") or {}
    name = case.get("case_id", case.get("student_id"))
    title = f'<div class="case-title"><h2>{_value(name)}</h2>{_badge(result.get("status"))}</div>'
    meta = "".join(f'<span class="pill">{escape(label)}: {_value(case.get(key))}</span>' for label, key in (
        ("الطالب", "student_id"), ("الدرجة", "degree_id"), ("الفصل الهدف", "target_part"),
        ("سجل التاريخ حتى", "history_as_of_part"), ("المرشحون", "candidate_count")))
    counters = _data([
        ("الخطط المولدة", counts.get("generated")), ("الخطط المقيمة بـ 33", counts.get("scored33")),
        ("الخطط المقيمة بـ 47", counts.get("scored47")), ("صفوف التنبؤ بـ 33", counts.get("scored_rows33")),
        ("صفوف التنبؤ بـ 47", counts.get("scored_rows47")), ("الزمن الكلي بالثواني", timings.get("total_seconds")),
        ("زمن المرحلة الأولى بالثواني", timings.get("stage1_seconds")),
        ("زمن المرحلة الثانية بالثواني", timings.get("stage2_seconds")),
    ])
    plans = result.get("recommendations") or []
    top = "".join(_plan(plan, position) for position, plan in enumerate(plans[:3], 1))
    if not top:
        top = '<p class="empty">غير متاح · لا توجد توصيات ناجحة مسجلة لهذه الحالة.</p>'
    shortlist = _shortlist(result.get("shortlist")) if experiment == "experiment_02" else ""
    diagnostics = _details("تفاصيل التنفيذ والتشخيص", _structured(result.get("diagnostics")))
    return (f'<section class="card" id="case-{index}">{title}<div class="case-meta">{meta}</div>'
            + _warnings(case.get("warnings")) + counters + '<h3>أفضل ثلاث خطط مقترحة</h3>' + top
            + shortlist + _observed(case.get("observed")) + _candidate_audit(case) + diagnostics + '</section>')


def _result_gpa(case, experiment, key="expected_plan_gpa"):
    plans = (case.get(experiment) or {}).get("recommendations") or []
    return plans[0].get(key) if plans else None


def _overlap(value):
    return len(value) if isinstance(value, (list, tuple, set)) else value


def _parity_status(value):
    return value.get("all_match") if isinstance(value, dict) else value


def _chart(title, cases, series, maximum=None):
    """Draw measured bars only; absent/non-finite values get no artificial bar."""
    measured = []
    for case in cases:
        values = [_finite(getter(case)) for _, _, getter in series]
        if any(value is not None for value in values):
            measured.append((case.get("case_id", case.get("student_id")), values))
    largest = max((max(value, 0) for _, values in measured for value in values if value is not None), default=0)
    axis_max = maximum if maximum is not None else (largest * 1.12 if largest > 0 else 1)
    width, left, right, row_height = 680, 140, 82, 33 * len(series) + 18
    plot_width = width - left - right
    height = max(110, 38 + row_height * len(measured))
    fragments = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" '
                 f'aria-label="{escape(title, quote=True)}"><title>{escape(title)}</title>']
    if not measured:
        fragments.append('<text x="340" y="58" text-anchor="middle" fill="#60758b" font-size="15">غير متاح</text>')
    for row_index, (label, values) in enumerate(measured):
        top = 24 + row_index * row_height
        label_text = _text(label)
        shown = label_text[:18] + "…" if len(label_text) > 19 else label_text
        fragments.append(f'<text x="{left-12}" y="{top+18}" text-anchor="end" fill="#18354d" '
                         f'font-size="12"><title>{escape(label_text)}</title>{escape(shown)}</text>')
        for series_index, ((series_label, color, _), value) in enumerate(zip(series, values)):
            y = top + series_index * 30
            fragments.append(f'<rect x="{left}" y="{y}" width="{plot_width}" height="19" rx="4" fill="#f0f5f9"/>')
            if value is None:
                fragments.append(f'<text x="{left+plot_width+8}" y="{y+15}" fill="#8796a5" font-size="12">—</text>')
                continue
            bar = min(max(value / axis_max, 0), 1) * plot_width
            fragments.append(f'<rect x="{left}" y="{y}" width="{bar:.3f}" height="19" rx="4" fill="{color}">'
                             f'<title>{escape(series_label)}: {value:.3f}</title></rect>')
            fragments.append(f'<text x="{left+plot_width+8}" y="{y+15}" fill="#18354d" font-size="12">{value:.3f}</text>')
    fragments.append('</svg>')
    legend = "".join(f'<span><i class="dot" style="background:{color}"></i>{escape(label)}</span>' for label, color, _ in series)
    return f'<div class="chart"><h3>{escape(title)}</h3>{"".join(fragments)}<div class="legend">{legend}</div></div>'


def _comparison(cases):
    rows = []
    for index, case in enumerate(cases, 1):
        first, second, comparison = case.get("experiment_01") or {}, case.get("experiment_02") or {}, case.get("comparison") or {}
        first_time = (first.get("timings") or {}).get("total_seconds")
        second_time = (second.get("timings") or {}).get("total_seconds")
        rows.append([f'<a href="{_FILES["experiment_01"]}#case-{index}">{_value(case.get("case_id", case.get("student_id")))}</a>',
                     _badge(first.get("status")), _badge(second.get("status")),
                     _value((first.get("counts") or {}).get("scored47")), _value((second.get("counts") or {}).get("scored47")),
                     _value(_result_gpa(case, "experiment_01")), _value(_result_gpa(case, "experiment_02")),
                     _value(_result_gpa(case, "experiment_01", "projected_cumulative_gpa")),
                     _value(_result_gpa(case, "experiment_02", "projected_cumulative_gpa")),
                     _value(first_time), _value(second_time), _value(comparison.get("speedup")),
                     _value(comparison.get("top_1_match")), _value(_overlap(comparison.get("top_3_overlap"))),
                     _value(comparison.get("baseline_top_3_recall_at_50_count")),
                     _value(comparison.get("baseline_top_3_recall_at_50")),
                     _value(comparison.get("gpa_regret")), _value(_parity_status(comparison.get("prediction_parity")))])
    headers = ["الحالة / الطالب", "حالة الكامل", "حالة المرحلتين", "خطط 47 الكاملة", "خطط 47 المختصرة", "أفضل GPA فصلي كامل",
               "أفضل GPA فصلي مرحلتين", "أفضل GPA تراكمي كامل", "أفضل GPA تراكمي مرحلتين",
               "زمن الكامل (ث)", "زمن المرحلتين (ث)", "التسريع", "تطابق أفضل خطة", "تقاطع أفضل 3",
               "احتفاظ أفضل 3 عند 50", "نسبة الاحتفاظ", "فقد المعدل التراكمي", "تطابق تنبؤ 47"]
    charts = _chart("الزمن الفعلي لكل حالة · ثوانٍ", cases, [
        ("الكامل 47", "#102a43", lambda c: ((c.get("experiment_01") or {}).get("timings") or {}).get("total_seconds")),
        ("33 ثم 47", "#087f8c", lambda c: ((c.get("experiment_02") or {}).get("timings") or {}).get("total_seconds")),
    ])
    charts += _chart("المعدل التراكمي المتوقع لأفضل خطة", cases, [
        ("الكامل 47", "#102a43", lambda c: _result_gpa(c, "experiment_01", "projected_cumulative_gpa")),
        ("33 ثم 47", "#087f8c", lambda c: _result_gpa(c, "experiment_02", "projected_cumulative_gpa")),
    ], maximum=4)
    charts += _chart("تقاطع أفضل 3 والاحتفاظ داخل 50", cases, [
        ("تقاطع أفضل 3", "#087f8c", lambda c: _overlap((c.get("comparison") or {}).get("top_3_overlap"))),
        ("احتفاظ أفضل 3 عند 50", "#c78b27", lambda c: (c.get("comparison") or {}).get("baseline_top_3_recall_at_50_count")),
    ], maximum=3)
    explanations = (
        '<section class="card"><h2>قراءة الفروق بين التجربتين</h2><div class="notice">'
        '<p><code>baseline_top_3_recall_at_50_count</code> يوضح كم خطة من أفضل ثلاث خطط في البحث الكامل وصلت إلى القائمة المختصرة، '
        'و<code>baseline_top_3_recall_at_50</code> يسجل نسبتها. '
        'إذا خرج بديل قوي من هذه القائمة، فلن يعيده التقييم اللاحق بـ 47 ميزة.</p>'
        '<p><code>prediction_parity</code> يختبر اتفاق تنبؤ النموذج 47 للخطة نفسها في المسارين. عند تطابقه، يكون '
        'اختلاف أفضل البدائل مرتبطًا بالترشيح وترتيب الخطط؛ عند عدم تطابقه، يجب مراجعة سياق الخطة والميزات قبل تفسير النتيجة.</p>'
        '<p><code>gpa_regret</code> هو المعدل التراكمي لأفضل خطة كاملة ناقص المعدل التراكمي لأفضل خطة في مسار المرحلتين. '
        'التسريع = زمن الكامل ÷ زمن المرحلتين، اعتمادًا على القياسات المسجلة.</p></div>'
        '<p class="subtle">المخططات تعرض قياسات متاحة ومحدودة فقط. الشرطات تعني أن القيمة غير متاحة؛ '
        'لا يُستبدل القياس المفقود بصفر. نتائج المقررات الفعلية تقيس الخطة التي سجلها الطالب وحدها.</p></section>')
    audits = []
    for case in cases:
        comparison = case.get("comparison") or {}
        parity = comparison.get("prediction_parity")
        parity = parity if isinstance(parity, dict) else {}
        checks = _data([
            ("اتفاق تنبؤ 47 للخطة نفسها", parity.get("all_match")),
            ("عدد المقارنات المشتركة · خطط", parity.get("compared_plan_count")),
            ("عدد المقارنات المشتركة · مقررات", parity.get("compared_course_count")),
            ("أكبر فرق مطلق في العلامات", parity.get("max_abs_mark_difference")),
            ("أكبر فرق مطلق في النقاط", parity.get("max_abs_points_difference")),
        ])
        audits.append(_details(f'تفاصيل المقارنة · {_text(case.get("case_id", case.get("student_id")))}',
                               checks + _structured(comparison) + _warnings(case.get("warnings"))))
    return ('<section class="card"><h2>المقارنة حالةً بحالة</h2>' + _table(headers, rows) + '</section>'
            + '<div class="chart-grid">' + charts + '</div>' + explanations
            + '<section class="card"><h2>تفاصيل المقارنة والتحذيرات</h2>' + "".join(audits) + '</section>')


def _dashboard(summary, page, cases):
    common = [_metric("الطلاب المطلوبون", summary.get("requested_students")),
              _metric("الطلاب المختارون", summary.get("selected_students"))]
    if page in {"experiment_01", "experiment_02"}:
        best = [_finite(_result_gpa(case, page, "projected_cumulative_gpa")) for case in cases]
        batch_rows = [_finite(((case.get(page) or {}).get("diagnostics") or {}).get("max_batch_rows")) for case in cases]
        common.extend([
            _metric("حالات لها توصيات", summary.get(f"{page}_successful")),
            _metric("حالات اكتمل بحثها", summary.get(f"{page}_completed")),
            _metric("حالات بلا خطة تحقق 18 ساعة", summary.get(f"{page}_no_feasible")),
            _metric("الخطط الممكنة المولدة", summary.get(f"{page}_total_generated")),
            _metric("الخطط المقيمة بـ 47", summary.get(f"{page}_total_plans47")),
            _metric("الزمن المقاس · ثوانٍ", summary.get(f"{page}_seconds")),
            _metric("متوسط زمن الحالة · ثوانٍ", summary.get(f"{page}_mean_seconds")),
            _metric("أفضل معدل تراكمي متوقع", max((value for value in best if value is not None), default=None)),
            _metric("أقصى صفوف في دفعة تنبؤ", max((value for value in batch_rows if value is not None), default=None), digits=0),
            _metric("MAE للقائمة الكاملة", summary.get("actual_plan_mae"), "متوقع كل مقررات التسجيل مقابل GPA الفعلي المنظف"),
            _metric("MAE المتوافق مع سياسة GPA", summary.get("policy_aligned_actual_plan_mae"), "المقررات الداخلة في GPA فقط"),
        ])
    else:
        common.extend([
            _metric("حالات قابلة لمقارنة البدائل", summary.get("comparable_students")),
            _metric("توصيات الكامل", summary.get("experiment_01_successful")),
            _metric("توصيات المرحلتين", summary.get("experiment_02_successful")),
            _metric("حالات بلا خطة تحقق 18 ساعة", summary.get("experiment_01_no_feasible")),
            _metric("زمن البحث الكامل · ثوانٍ", summary.get("experiment_01_seconds")),
            _metric("زمن المرحلتين · ثوانٍ", summary.get("experiment_02_seconds")),
            _metric("MAE للقائمة الكاملة", summary.get("actual_plan_mae")),
            _metric("MAE المتوافق مع سياسة GPA", summary.get("policy_aligned_actual_plan_mae")),
            _metric("الحالات الفعلية الصالحة", summary.get("actual_valid_students")),
        ])
    return '<div class="metrics">' + "".join(common) + '</div>'


def _document(page, cases, manifest, summary):
    description = (
        "تقييم كل خطة ممكنة بالنموذج الرسمي ذي 47 ميزة ثم ترتيب أفضل ثلاث خطط."
        if page == "experiment_01" else
        "تقييم أولي بـ 33 ميزة، الاحتفاظ بأفضل 50 خطة، ثم تقييم هذه الخطط بـ 47 ميزة واختيار أفضل ثلاث."
        if page == "experiment_02" else
        "مقارنة البدائل وجودة الاحتفاظ والزمن، باستخدام الحالات والمرشحين والقيود نفسها في المسارين."
    )
    nav = "".join(f'<a class="{"active" if key == page else ""}" href="{filename}">{escape(_TITLES[key])}</a>'
                  for key, filename in _FILES.items())
    hero = (f'<header class="hero"><div class="eyebrow">XML · V2 · 47 / 33 → 47</div>'
            f'<h1>{escape(_TITLES[page])}</h1><p>{escape(description)}</p><nav class="nav">{nav}</nav></header>')
    method = ('<div class="notice"><p>يعتمد الترتيب على المعدل المتوقع من نموذج العلامات وتحويل '
              '<code>GradeScale</code>؛ لا تُستخدم احتمالات مصنف الرسوب في الدرجة أو الترتيب.</p>'
              '<p>المعدل الفصلي: <code>Σ(credits × predicted_points) / Σ(credits)</code>. '
              'الميزات التاريخية للرسوب والصعوبة تبقى جزءًا من عقد النموذج الأصلي.</p>'
              '<p>للتقييم الفعلي: يحتوي سياق التنبؤ الكامل على كل مقررات التسجيل الخام، بينما يحسب GPA الفعلي '
              'من المقررات المنظفة المؤهلة <code>F/FE/FA/P</code> ويستبعد <code>D/W</code>. '
              'قد يختلف مقام الساعات؛ لذلك يظهر خطأ القائمة الكاملة منفصلًا عن الخطأ المتوافق مع سياسة GPA عند توفره.</p></div>')
    body = _comparison(cases) if page == "comparison" else "".join(
        _case_report(case, index, page) for index, case in enumerate(cases, 1))
    if not cases:
        body += '<section class="card"><p class="empty">غير متاح · لا توجد حالات في هذا التشغيل.</p></section>'
    provenance = ('<section class="card"><h2>منهج التشغيل ومصادره</h2>'
                  + _details("بيانات التشغيل والمودلات والسجل", _structured(manifest))
                  + _details("ملخص القياسات المسجلة", _structured(summary)) + '</section>')
    footer = '<footer class="footer">تقرير محلي مستقل · جميع النصوص والرسوم مضمنة · القيم غير المتاحة تظهر بشرطة.</footer>'
    return ('<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{escape(_TITLES[page])}</title><style>{_CSS}</style></head><body><main class="shell">'
            + hero + _dashboard(summary, page, cases) + method + body + provenance + footer + '</main></body></html>')


def write_reports(run_dir: Path, cases: list[dict], manifest: dict, summary: dict) -> None:
    """Write three self-contained UTF-8 reports from recorded experiment evidence."""
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    for page, filename in _FILES.items():
        (run_dir / filename).write_text(_document(page, cases, manifest, summary), encoding="utf-8")
