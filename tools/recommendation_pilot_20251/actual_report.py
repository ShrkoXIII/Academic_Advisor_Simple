"""Render an Arabic report from immutable actual-candidate experiment outputs.

This command never loads a model, reads target source Parquets, calls an API,
or recomputes predictions. Its only write is the explicitly selected report.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import re
from statistics import mean

from .adapter import PILOT_ROOT
from .snapshots import run_read_roots, run_root


REPO = Path(__file__).resolve().parents[2]
RUN_ROOT = run_root(PILOT_ROOT, family='actual_candidate_injection')
DEFAULT_OUTPUT = REPO / "reports" / "pilot_20251_actual_candidate_injection_results.md"
MODELS = "ABC"
LOADS = {"fixed_18": "Experiment A — Fixed 18 Credits", "actual_load": "Experiment B — Actual Credit Load Diagnostic"}
WARNING = "DIAGNOSTIC ONLY \u2014 ACTUAL COURSES WERE INJECTED"


def _read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def _digest(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def _link(path, label=None):
    path = Path(path).resolve()
    return f"[{label or path.name}](<{path.as_posix()}>)"


def _fmt(value, places=3):
    if value is None:
        return "N/A"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        if not math.isfinite(value):
            return "N/A"
        return str(value) if isinstance(value, int) else f"{value:.{places}f}"
    return str(value)


def _table(headers, rows):
    def cell(value):
        return _fmt(value).replace("|", "\\|").replace("\n", "<br>")
    return "\n".join(["| " + " | ".join(map(cell, headers)) + " |",
                      "| " + " | ".join("---" for _ in headers) + " |",
                      *("| " + " | ".join(map(cell, row)) + " |" for row in rows)]) + "\n"


def _num(value):
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) else None


def _mean(values):
    values = [value for value in values if _num(value) is not None]
    return mean(values) if values else None


def _p95(values):
    values = sorted(value for value in values if _num(value) is not None)
    if not values:
        return None
    position = (len(values) - 1) * .95
    left, right = math.floor(position), math.ceil(position)
    return values[left] + (values[right] - values[left]) * (position - left)


def _pair(first, second):
    return f"{_fmt(first)} → {_fmt(second)}"


def load_run(run_id, run_root=None):
    """Read one completed, locally saved run without invoking Pilot services."""
    if not isinstance(run_id, str) or not re.fullmatch(r"run_[A-Za-z0-9_-]+", run_id):
        raise ValueError("Invalid run ID.")
    if run_root is None:
        roots = run_read_roots(PILOT_ROOT, 'actual_candidate_injection')
        root = next((p for p, _ in roots if (p / run_id).is_dir()), RUN_ROOT)
    else:
        root = Path(run_root)
    root = root.resolve()
    directory = (root / run_id).resolve()
    if directory.parent != root:
        raise ValueError("Run path escapes experiment storage.")
    manifest = _read(directory / "run_manifest.json")
    if manifest.get("run_id") != run_id or manifest.get("status") != "completed":
        raise ValueError("Report inputs require a matching completed run manifest.")
    results = _read(directory / "student_results.json")
    if not isinstance(results, list) or len(results) != manifest.get("result_case_count"):
        raise ValueError("Saved result count conflicts with the run manifest.")
    keys = [(r["sample_id"], r["candidate_mode"], r["credit_experiment"]) for r in results]
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate student/mode/load result identity.")
    summary_path = directory / "metrics_summary.json"
    summary = _read(summary_path if summary_path.exists() else directory / "diagnostics.json")
    protection_path = directory / "protected_files.json"
    protection = _read(protection_path) if protection_path.exists() else {}
    return {"id": run_id, "directory": directory, "manifest": manifest, "results": results,
            "summary": summary, "protection": protection,
            "budget": manifest.get("generation_settings", {}).get("max_plans")}


def _index(run):
    return {(r["sample_id"], r["candidate_mode"], r["credit_experiment"]): r for r in run["results"]}


def _metrics(row, model):
    return (row or {}).get("experiments", {}).get(model, {}).get("recommendation_metrics", {})


def _ready(row, model):
    return _metrics(row, model).get("status") == "AVAILABLE"


def _overlap(row, model):
    metrics = _metrics(row, model)
    return f"{_fmt(metrics.get('top1_actual_overlap'))}/{_fmt(metrics.get('top3_union_actual_overlap'))}"


def _paired_summary(run):
    stored = run["summary"].get("paired_recommendation_summary")
    if stored is not None:
        return stored
    # Older saved summaries have no paired table; derive it from saved metrics.
    indexed, rows = _index(run), []
    for load in LOADS:
        samples = sorted({r["sample_id"] for r in run["results"] if r["credit_experiment"] == load})
        for model in MODELS:
            pairs = [(indexed.get((s, "original", load)), indexed.get((s, "augmented", load))) for s in samples]
            selected = [(a, b) for a, b in pairs if a is not None and b is not None]
            ready = [(a, b) for a, b in selected if _ready(a, model) and _ready(b, model)]
            row = {"credit_experiment": load, "model": model, "paired_selected_student_count": len(selected),
                   "paired_student_count": len(ready),
                   "became_available_student_count": sum(not _ready(a, model) and _ready(b, model) for a, b in selected)}
            for mode, index in (("original", 0), ("augmented", 1)):
                for metric in ("top1_actual_overlap", "top3_union_actual_overlap"):
                    row[f"{mode}_mean_{metric}"] = _mean(_metrics(pair[index], model).get(metric) for pair in ready)
            rows.append(row)
    return rows


def _coverage_rows(run):
    indexed, selected = _index(run), []
    for sample in sorted({r["sample_id"] for r in run["results"]}):
        candidates = [indexed.get((sample, mode, load)) for mode in ("augmented", "original") for load in LOADS]
        row = next((r for r in candidates if r is not None and r.get("candidate_coverage")), {})
        selected.append((sample, row.get("candidate_coverage", {}), row))
    return selected


def _stage_summary(run):
    """Compare latency only for the same students with both model scores."""
    indexed, rows = _index(run), []
    for load in LOADS:
        samples = sorted({r["sample_id"] for r in run["results"] if r["credit_experiment"] == load})
        for model in MODELS:
            pairs = [(indexed.get((s, "original", load)), indexed.get((s, "augmented", load))) for s in samples]
            pairs = [(a, b) for a, b in pairs if a is not None and b is not None and _ready(a, model) and _ready(b, model)]
            before = [a.get("latency", {}).get("total_request_seconds") for a, _ in pairs]
            after = [b.get("latency", {}).get("total_request_seconds") for _, b in pairs]
            a, b = _mean(before), _mean(after)
            rows.append([load, model, len(pairs), _pair(a, b), _pair(_p95(before), _p95(after)),
                         b / a if a is not None and b is not None and a > 0 else None])
    return rows


def _prefix_checks(runs):
    rows = []
    for first_index, first in enumerate(runs):
        for second in runs[first_index + 1:]:
            if first["budget"] == second["budget"]:
                continue
            small, large = sorted((first, second), key=lambda value: value["budget"])
            left, right = _index(small), _index(large)
            common = sorted(set(left) & set(right))
            streams, matching_ids, matching_predictions = 0, 0, 0
            for key in common:
                for model in MODELS:
                    a = left[key].get("experiments", {}).get(model, {}).get("diagnostic_plans", [])
                    b = right[key].get("experiments", {}).get(model, {}).get("diagnostic_plans", [])
                    if not a or not b:
                        continue
                    streams += 1
                    b = b[:len(a)]
                    def signature(plans, prediction):
                        return [[[(c.get("course_id"), c.get("course_credits"),
                                   c.get("predicted_mark") if prediction else None,
                                   c.get("fail_probability") if prediction else None,
                                   c.get("expected_points") if prediction else None) for c in p.get("courses", [])],
                                 p.get("expected_plan_gpa") if prediction else None] for p in plans]
                    matching_ids += signature(a, False) == signature(b, False)
                    matching_predictions += signature(a, True) == signature(b, True)
            rows.append([f"{small['budget']} → {large['budget']}", len(common), streams,
                         f"{matching_ids}/{streams}", f"{matching_predictions}/{streams}"])
    return rows


def _validation_lines(validation, validation_path):
    if validation is None:
        return ["لم يُمرر ملف تحقق محفوظ إلى مولد التقرير؛ لا يدّعي هذا التقرير نتيجة اختبارات غير مسجلة.\n"]
    lines = ["دليل التحقق المحفوظ: " + _link(validation_path) + ". لا يشغّل مولد التقرير أي اختبار.\n"]
    checks = validation.get("checks", [])
    if isinstance(checks, list) and checks:
        rows = []
        for check in checks:
            if not isinstance(check, dict):
                rows.append([str(check), None, None, None, None])
                continue
            summary, log_label = check.get("summary"), check.get("log_path")
            if log_label:
                path = Path(log_label)
                if not path.is_absolute():
                    path = Path(validation_path).parent / path
                if path.is_file():
                    if summary is None:
                        matches = re.findall(r"^.*\b(?:passed|failed|skipped)\b.*$", path.read_text(encoding="utf-8-sig", errors="replace"), re.MULTILINE)
                        summary = matches[-1] if matches else "Saved log; no pytest summary extracted"
                    log_label = _link(path) + " SHA256=`" + _digest(path) + "`"
                else:
                    log_label = "MISSING_LOG: " + str(path)
            rows.append([check.get("name", "check"), check.get("command"), check.get("exit_code"), summary, log_label])
        lines.append(_table(["الفحص", "الأمر المسجل", "Exit", "النتيجة المسجلة", "السجل"], rows))
    notes = validation.get("notes", [])
    if notes:
        lines.append("\n".join("- " + str(note) for note in (notes if isinstance(notes, list) else [notes])) + "\n")
    return lines


def render_report(runs, *, validation=None, validation_path=None):
    """Create prose/tables exclusively from saved results and supplied logs."""
    if not runs:
        raise ValueError("At least one saved run is required.")
    runs = sorted(runs, key=lambda run: (run["budget"] or 0, run["id"]))
    primary = max(runs, key=lambda run: (run["manifest"].get("student_count", 0), -(run["budget"] or 0)))
    lines = ["# Pilot 20251 — Actual-Course Candidate Injection Results\n",
        "**" + WARNING + "**\n",
        "هذه مقارنة تشخيصية تعتمد على اختيارات الطالب بعد حدوثها. زيادة التقاطع لا تثبت تحسن التوصية أو الأهلية التاريخية، ولا تمثل `Historical Backtest` صالحًا. كل الأرقام أدناه مشتقة من ملفات التشغيل المحفوظة، دون تنبؤ جديد من مولد التقرير.\n",
        "## 1. What Changed\n",
        "أُضيف اتحاد مرشحات مؤقت في الذاكرة إلى موقع Pilot الموجود، مع اختيار `Original API` أو `Actual-Course Augmented` ومقارنة الوضعين للطالب نفسه. استُخدمت النماذج المحفوظة A/B/C وترتيبها المستقل وأفضل ثلاث خطط من المساحة المشتركة.\n",
        _table(["الملف", "الدور"], [[_link(REPO / path), role] for path, role in [
            ("tools/recommendation_pilot_20251/actual_candidates.py", "اتحاد المرشحات، تحقق البنية، التاريخ السابق، مصدر كل حقل"),
            ("tools/recommendation_pilot_20251/actual_experiment.py", "تشغيل معزول، وضعا الساعات، قياس الزمن، بصمات الحماية، حفظ تشغيل جديد"),
            ("tools/recommendation_pilot_20251/actual_metrics.py", "تقاطع التوصيات وأخطاء الخطة الفعلية بمقامين منفصلين"),
            ("tools/recommendation_pilot_20251/actual_report.py", "توليد هذا التقرير من النتائج المحفوظة فقط"),
            ("tools/recommendation_pilot_20251/engine.py", "نقطة إدخال مرشحات وتوقيت مع الاحتفاظ بسلوك الوضع الأصلي"),
            ("tools/recommendation_pilot_20251/app.py", "مسارات محلية خاصة بالتجربة"),
            ("tools/recommendation_pilot_20251/static/app.js", "أدوات المقارنة والتفاصيل والتحذير ضمن الواجهة القائمة"),
            ("tools/recommendation_pilot_20251/static/index.html", "اختيارات التجربة ضمن الموقع نفسه"),
            ("tools/recommendation_pilot_20251/static/style.css", "تنسيق إضافات الواجهة")]]),
        "الاختبارات الجديدة تخص `actual_candidates` و`actual_experiment` و`actual_metrics` وواجهة الحقن. لا تدريب أو دمج نماذج أو تغيير أوزان أو فرض الخطة الفعلية ضمن `Top-3`.\n",
        _table(["Run ID", "الطلاب", "الحالات", "ميزانية الخطط", "حالات البحث القصوى", "مسار النتائج"],
            [["`" + r["id"] + "`", r["manifest"].get("student_count"), len(r["results"]), r["budget"],
              r["manifest"].get("generation_settings", {}).get("max_search_states"), _link(r["directory"], "ملفات التشغيل")]
             for r in runs]),
        "التشغيل ذو عدد طلاب أقل من 30 يمثل النطاق المسجل فقط، ولا يُقدَّم على أنه إعادة تقييم جماعي كامل. تختلف ميزانية 200 عن 2000؛ الجداول تميز كل تشغيل.\n",
        "## 2. Data Integrity\n",
        "يعبر إلى بناء المرشحات من التسجيل الفعلي `course_id` و`course_credits` فقط. لا تعبر `final_mark` أو `actual_mark` أو النقاط أو حالة النجاح/الرسوب أو محاولة الفصل المستهدف. تُستخدم النتائج الحقيقية لاحقًا في حساب الأخطاء فقط.\n",
        "يختار `observed.py` التسجيل بهوية `student_id + degree_id + part_id` ويربط النتيجة عبر `student_course_id` مع المادة والساعات. يطابق الحقن الكتالوج بمفتاح `degree_id + course_id`؛ وتُطبّع المعرفات الرقمية باستخدام `Decimal`. تساوي ساعات الكتالوج ساعات التسجيل شرط لازم، وتُرفض البنية الناقصة أو المتعارضة مع سبب صريح.\n",
        "تُحسب `attempt_number` من أكبر محاولة في CLEANED history سابقة للطالب والمادة عبر الدرجات، بشرط `part_id < 20251`، ثم تُضاف محاولة واحدة. غياب سجل سابق في مصدر سليم يعطي 1 وفق عقد الاستيراد المحلي الموجود؛ لا يثبت اكتمال تاريخ المحاولات الرسمي أو أهلية التسجيل. مصدر غير صالح لا يُستبدل بمحاولة أولى مختلقة. لا تُحتسب حالة أو محاولة أو نتيجة للفصل المستهدف. بيانات C المرجعية وتاريخ النموذج ثابتان حتى `20243`؛ لا تدخل نتائج `20251` في مرجع الأقران، وتوقيت نفاذ الكتالوج غير مثبت.\n",
        "الغائب يُحدد مقابل **API الخام**؛ المادة الموجودة فيه والمرفوضة بقواعد الأهلية الحالية تبقى مرفوضة. الاستثناء التشخيصي للمواد الغائبة المحقونة فقط، مع `historical_eligibility_unverified=true` و`official_requestability=UNVERIFIED`. تبقى حدود الساعات والقيود الأصلية نافذة. مصدر كل حقل محفوظ في `candidate_provenance` خارج مدخلات النموذج.\n",
        "لم تُعد كتابة `courses_response.json` أو `Student API` أو Frozen History أو النماذج. قيم `TOTAL_*` قيم بداية الفصل وفق اتفاق الجامعة، وتُنسخ كما هي؛ لم يتغير معناها ولم تُحسب مجددًا لمطابقة V2. فروق Snapshot مع الميزات التاريخية وتحذيرات عدم التكافؤ باقية.\n"]
    source_rows, protection_rows, git_rows = [], [], []
    for run in runs:
        manifest, protection = run["manifest"], run["protection"]
        provenance = manifest.get("git", {})
        git_rows.append([run["id"], provenance.get("branch"), provenance.get("base_commit"),
                         provenance.get("branch_of_origin"), provenance.get("commits_created"), provenance.get("pushes")])
        protection_rows.append([run["id"], protection.get("status", manifest.get("protection_status")),
            protection.get("file_count"), len(protection.get("changed_files", [])),
            len(protection.get("new_protected_files", [])), _link(run["directory"] / "protected_files.json")])
        for name, source in manifest.get("candidate_sources", {}).items():
            if isinstance(source, dict) and "sha256" in source:
                source_rows.append([run["id"], name, source.get("path"), "`" + source["sha256"] + "`"])
        source_rows.append([run["id"], "students.csv", "قائمة العينة المحفوظة", "`" + str(manifest.get("students_csv_sha256")) + "`"])
        for model, asset in manifest.get("models", {}).items():
            for name, fingerprint in asset.get("artifact_sha256", {}).items():
                source_rows.append([run["id"], model + "/" + name, "نموذج/عقد محفوظ", "`" + str(fingerprint) + "`"])
    lines += [_table(["Run", "Branch", "Base HEAD", "فرع الأصل", "Commits", "Pushes"], git_rows),
        "أقرّ المستخدم اسم `new_branch` للتجربة. فرع الإنتاج السابق غير مثبت في السجل؛ لم يغيّر التشغيل الفرع ولم ينفذ `merge` أو `push` أو Commit. وجود `PASS` أدناه يعني تطابق الملفات المحددة قبل التشغيل وبعده؛ تفاصيل المجموعة والبصمات محفوظة في ملف الحماية، ولا يساوي ذلك اعتمادًا للإنتاج.\n",
        _table(["Run", "الحماية", "ملفات محمية", "متغير", "مضاف للمجموعة", "الدليل"], protection_rows),
        _table(["Run", "المصدر/النموذج", "المرجع", "SHA256"], source_rows),
        "بصمات API لكل طالب، نسخ النماذج، GradeScale، مرجع C، Frozen History، roster والنتائج موجودة تفصيليًا في `run_manifest.json` و`protected_files.json` لكل تشغيل؛ لا يُكتفى ببصمات الجدول المختارة.\n",
        "## 3. Before vs After\n",
        "`Original` هو المصدر الأصلي بقواعده. `Augmented` اتحاد المصدر الخام مع الفعليات الغائبة القابلة لإعادة البناء البنيوي. تغطية الخام لا تساوي تغطية مجموعة النموذج: قد تبقى مادة مستبعدة بسياسة أصلية، وقد يكون طلب الطالب محجوبًا كليًا بسبب `FUTURE_COURSE_SOURCE`. قيمة `N/A` تعني نتيجة غير متاحة؛ لا تُحسب صفر تقاطع.\n"]
    for run in runs:
        coverage = _coverage_rows(run)
        total = sum(c.get("actual_course_count", 0) or 0 for _, c, _ in coverage)
        before = sum(c.get("actual_courses_in_original_candidates", 0) or 0 for _, c, _ in coverage)
        after = sum(c.get("actual_courses_in_augmented_candidates", 0) or 0 for _, c, _ in coverage)
        injected = sum(c.get("number_of_injected_courses", 0) or 0 for _, c, _ in coverage)
        lines += [f"### Run `{run['id']}` — {run['budget']} plans\n",
            f"الفعليات الفريدة: **{total}**؛ تغطية API الخام **{before}/{total} → {after}/{total}**؛ المضاف **{injected}**. العد مرة واحدة لكل طالب، وليس مرة لكل وضع ساعات أو نموذج. التغطية اللاحقة للطلبات المحجوبة وصف لاتحاد بنيوي أُعد في الذاكرة، وليست مجموعة قابلة للتنبؤ.\n",
            _table(["العينة", "الفعلي", "مرشحات API", "الاتحاد الخام", "المحقون", "فعليات داخل الخام O→A", "Model pool", "مستبعد بسياسة أصلية"],
                [[sample, c.get("actual_course_count"), c.get("original_candidate_count"), c.get("augmented_candidate_count"),
                  c.get("number_of_injected_courses"), _pair(c.get("actual_courses_in_original_candidates"), c.get("actual_courses_in_augmented_candidates")),
                  c.get("model_pool_status", _pair(c.get("original_model_candidate_count"), c.get("augmented_model_candidate_count"))),
                  len(c.get("actual_courses_excluded_by_original_policy", [])) if c.get("model_pool_status") is None else None]
                 for sample, c, _ in coverage])]
        indexed = _index(run)
        for load, title in LOADS.items():
            selected = sorted({r["sample_id"] for r in run["results"] if r["credit_experiment"] == load})
            if not selected:
                continue
            rows = []
            for sample in selected:
                a, b = indexed.get((sample, "original", load)), indexed.get((sample, "augmented", load))
                reference = a or b
                rows.append([sample, reference.get("observed_plan", {}).get("total_credits"), reference.get("target_credits"),
                    *[f"{_overlap(a, model)} → {_overlap(b, model)}" for model in MODELS],
                    "; ".join(sorted(set((a or {}).get("issues", []) + (b or {}).get("issues", [])) &
                                      {"FUTURE_COURSE_SOURCE", "REQUESTED_CREDITS_OUTSIDE_EXPLICIT_LIMITS", "NO_EXACT_CREDIT_SUBSET", "SEARCH_BUDGET_EXHAUSTED"})) or "—"])
            lines += ["#### " + title + "\n",
                ("الهدف ثابت 18؛ اختلاف الحمل الفعلي يمنع مقارنة التطابق الكامل.\n" if load == "fixed_18" else
                 "الهدف مأخوذ من التسجيل الفعلي بعد حدوثه، وليس قرار حمل مستقلًا. لا تتجاوز التجربة حدود التسجيل عند تعارضه معها.\n"),
                "كل خلية A/B/C هي `Top-1 overlap / Top-3 union overlap`؛ السهم من Original إلى Augmented.\n",
                _table(["العينة", "الحمل الفعلي", "الهدف", "A: O→A", "B: O→A", "C: O→A", "سبب حجب/تعذر"], rows)]
        lines += ["#### Paired recommendation summary\n",
            "متوسطات التقاطع أدناه تخص الطلاب الذين تتوفر لهم نتيجة في الوضعين معًا. يُعرض من أصبحت نتيجتهم متاحة بعد الإضافة على حدة؛ لا يُخلط تغير المقام بتغير التقاطع.\n",
            _table(["اختبار الساعات", "النموذج", "أزواج متاحة", "متاح حديثًا", "متوسط Top-1 O→A", "متوسط Top-3 O→A"],
                [[r.get("credit_experiment"), r.get("model"), r.get("paired_student_count"), r.get("became_available_student_count"),
                  _pair(r.get("original_mean_top1_actual_overlap"), r.get("augmented_mean_top1_actual_overlap")),
                  _pair(r.get("original_mean_top3_union_actual_overlap"), r.get("augmented_mean_top3_union_actual_overlap"))]
                 for r in _paired_summary(run)])]
    lines += ["## 4. A/B/C Comparison\n",
        "A يستخدم النموذج الأصلي و47 ميزة وتاريخه الفردي. B يستخدم النموذج المحفوظ ذا 44 ميزة وتاريخ الجامعة المجمع. C يستخدم النموذج المحفوظ ذا 47 ميزة، ومنها ميزات التشابه الثلاث. لا تتحد مخرجاتها في نموذج رابع. تتلقى الأنظمة داخل كل حالة هوية ومرشحات وحملًا وحدود بحث ومساحة خطط واحدة قبل ترتيب مستقل.\n",
        "تقييم العلامات أدناه **للخطة الفعلية الكاملة بتوقع مستقل** عبر `observed_prediction.py`، حتى لو لم يولدها البحث. ليس خطأً لتوصيات بديلة لا نملك نتائجها المضادة للواقع. تُزال تكرارات أوضاع المرشحات/الساعات عند العد بمفتاح `sample_id + model`. `Bias = predicted − actual`، و`Micro` يزن كل مادة بالتساوي؛ `Macro` متوسط مقياس كل طالب.\n",
        "مجموعة `low_archived_gpa` تعني GPA في Student Snapshot أقل من 2؛ `low_cohort_gpa` تستخدم قيمة العينة التاريخية أقل من 2. اختلاف المصدرين محفوظ، ولا يعني GPA الصفري أن الطالب جديد. المقاييس مشروطة بهذه اللقطة ولا تُعتمد كدقة تاريخية موثوقة.\n"]
    for run in runs:
        prediction = run["summary"].get("prediction_summary", [])
        lines += [f"### Prediction metrics — `{run['id']}`\n",
            _table(["المجموعة", "النموذج", "طلاب متاحون/مختارون", "مواد", "MAE Micro/Macro", "RMSE Micro/Macro", "Bias Micro/Macro", "توقع مفقود/مرفوض"],
                [[r.get("group"), r.get("model"), f"{r.get('student_count')}/{r.get('selected_student_count')}", r.get("course_count"),
                  f"{_fmt(r.get('micro_mae'),4)}/{_fmt(r.get('macro_mae'),4)}",
                  f"{_fmt(r.get('micro_rmse'),4)}/{_fmt(r.get('macro_rmse'),4)}",
                  f"{_fmt(r.get('micro_bias'),4)}/{_fmt(r.get('macro_bias'),4)}",
                  f"{r.get('missing_prediction_count')}/{r.get('rejected_course_count')}" ] for r in prediction]),
            _table(["المجموعة", "النموذج", "تسميات الرسوب", "رسوب فعلي", "Brier Micro/Macro", "Log loss Micro/Macro", "ROC AUC Micro/Macro"],
                [[r.get("group"), r.get("model"), r.get("micro_fail_count"), r.get("micro_actual_fail_count"),
                  f"{_fmt(r.get('micro_fail_brier'),4)}/{_fmt(r.get('macro_fail_brier'),4)}",
                  f"{_fmt(r.get('micro_fail_log_loss'),4)}/{_fmt(r.get('macro_fail_log_loss'),4)}",
                  f"{_fmt(r.get('micro_fail_roc_auc'),4)}/{_fmt(r.get('macro_fail_roc_auc'),4)}"] for r in prediction])]
        all_rows = [r for r in prediction if r.get("group") == "all" and _num(r.get("micro_mae")) is not None]
        if all_rows:
            winner = min(all_rows, key=lambda r: r["micro_mae"])
            lines.append(f"الأقل في MAE الوصفي الكلي لهذا التشغيل هو **{winner['model']}** ({_fmt(winner['micro_mae'],4)}). هذه مقارنة مشروطة بالمدخلات المحفوظة؛ لا تثبت تفوقًا إنتاجيًا أو تحسنًا سببيًا بسبب الحقن.\n")
    lines += ["## 5. Search Limitations\n",
        "حُفظ التعداد الأصلي: ترتيب `course_id` نصيًا ثم include-first وأول N خطط مطابقة لـ Decimal exact credits، مع ميزانية حالات معلنة. لم يُصلح انحياز البادئة ولم تُضف الخطة الفعلية قسرًا. `search_truncated=true` يعني أن أعلى ثلاث هي الأفضل داخل الجزء المفحوص، وليس ضمانًا للأفضلية العالمية.\n"]
    for run in runs:
        summary = run["summary"].get("recommendation_summary", [])
        lines += [f"### Search — `{run['id']}`\n",
            _table(["الحمل", "الوضع", "النموذج", "طلاب بنتيجة", "خطط مفحوصة", "حالات زيارة", "بحث مبتور", "حمل فعلي متوافق", "الفعلية فُحصت", "الفعلية Top-3"],
                [[r.get("credit_experiment"), r.get("candidate_mode"), r.get("model"), r.get("available_student_count"),
                  r.get("evaluated_plan_count"), r.get("visited_search_states"), r.get("search_truncated_student_count"),
                  r.get("load_compatible_available_student_count"), r.get("actual_plan_examined_student_count"),
                  r.get("actual_plan_top3_student_count")] for r in summary])]
        indexed = _index(run)
        for load, title in LOADS.items():
            samples = sorted({r["sample_id"] for r in run["results"] if r["credit_experiment"] == load})
            rows = []
            for sample in samples:
                a, b = indexed.get((sample, "original", load)), indexed.get((sample, "augmented", load))
                ma, mb = _metrics(a, "A"), _metrics(b, "A")
                def exposed(metrics):
                    values = metrics.get("actual_course_exposure", {})
                    return f"{sum(v.get('examined_plan_count',0)>0 for v in values.values())}/{len(values)}" if values else None
                def ranks(row):
                    return "/".join(_fmt(_metrics(row, model).get("actual_plan_rank")) for model in MODELS)
                rows.append([sample, _pair(ma.get("evaluated_plan_count"), mb.get("evaluated_plan_count")),
                    _pair(ma.get("visited_search_states"), mb.get("visited_search_states")),
                    _pair(ma.get("search_truncated"), mb.get("search_truncated")), _pair(exposed(ma), exposed(mb)),
                    _pair(ma.get("actual_plan_examined"), mb.get("actual_plan_examined")), f"{ranks(a)} → {ranks(b)}"])
            if rows:
                lines += ["#### " + title + " — exposure and full-plan rank\n",
                    "ظهور المواد يعني عدد الفعليات التي ظهرت مرة على الأقل داخل الخطط المفحوصة، لا داخل المرشحات فقط. الإحصاء من A لأن مساحة الخطط واحدة؛ ترتيب الخطة الفعلية يعرض `A/B/C` لكل وضع، و`N/A` عند غيابها أو عدم توفر التنبؤ.\n",
                    _table(["العينة", "خطط O→A", "حالات O→A", "مبتور O→A", "مواد فعلية ظهرت O→A", "الخطة الفعلية فُحصت O→A", "رتبتها A/B/C: O→A"], rows)]
        found = []
        for row in run["results"]:
            for model in MODELS:
                metrics = _metrics(row, model)
                if metrics.get("actual_plan_rank") is not None:
                    found.append([row["sample_id"], row["credit_experiment"], row["candidate_mode"], model,
                        metrics["actual_plan_rank"], metrics.get("actual_plan_top3_rank"), metrics.get("actual_plan_expected_gpa"),
                        metrics.get("best_examined_expected_gpa")])
        lines.append(_table(["العينة", "الحمل", "الوضع", "النموذج", "رتبة الفعلية", "رتبة Top-3", "GPA الفعلية المتوقع", "أفضل GPA مفحوص"], found)
                     if found else "لم تظهر الخطة الفعلية كاملة في أي مساحة مفحوصة متاحة بهذا التشغيل؛ يُراجع جدول الحمل والتعرض قبل نسب السبب إلى ترتيب النموذج.\n")
    checks = _prefix_checks(runs)
    sensitivity = [run for run in runs if run["manifest"].get("student_count", 0) < primary["manifest"].get("student_count", 0)]
    if sensitivity:
        rows = []
        for run in sensitivity:
            for row in run["results"]:
                for model in MODELS:
                    metrics = _metrics(row, model)
                    rows.append([run["id"], run["budget"], row["sample_id"], row["credit_experiment"],
                        row["candidate_mode"], model, metrics.get("top1_actual_overlap"), metrics.get("top3_union_actual_overlap"),
                        metrics.get("search_truncated"), metrics.get("actual_plan_examined")])
        lines += ["### Separate single-student / subset budget sensitivity\n",
            "هذه حساسية ميزانية لعينة أصغر، مستقلة عن جدول الطلاب الثلاثين. لا تُضاف تسجيلاتها أو توقعاتها مرة أخرى إلى المقاييس الجماعية، ولا تمثل نتائج 2000 خطة لجميع الطلاب.\n",
            _table(["Run", "الميزانية", "العينة", "الحمل", "الوضع", "النموذج", "Top-1", "Top-3 union", "مبتور", "الفعلية فُحصت"], rows)]
    if checks:
        lines += ["### 200 / 2000 reproducibility\n",
            "المقارنة التالية بين الحالات المشتركة المسجلة فقط. الحالات بلا خطط لا تُعد دليل تطابق تنبؤات. تطابق البادئة لا يثبت فحص بقية المساحة.\n",
            _table(["الميزانية", "حالات مشتركة", "مسارات نموذج ذات خطط", "بادئة المواد متطابقة", "بادئة التوقعات متطابقة"], checks)]
    lines += ["## 6. Real-Time Performance\n",
        "الأزمنة بالثواني، وكل خلية `mean / p95`. النماذج والمصادر دُفئت قبل الحالات، وتسلسل Original/Augmented متعاكس حسب فهرس الطالب، وبنفس عدد threads والميزانية. هذا قياس واحد لكل حالة، وليس اختبار حمل أو benchmark متكررًا.\n",
        "جدول التشغيل المجمع يشمل الطلبات المحجوبة؛ الصفر في مرحلة متخطاة لا يعني كلفة نموذج صفرية. تجهيز المرشحات والتوليد وإجمالي الطلب مشتركة بين A/B/C، فلا تُجمع عبر النماذج. الميزات تشمل التاريخ والسياق والمصفوفة والتحقق؛ التنبؤ يشمل `Booster.predict` و`GradeScale.convert`؛ الترتيب يشمل التجميع والتسلسل. التوقع المستقل للخطة الفعلية وبصمات الحماية خارج زمن طلب التوصية.\n"]
    for run in runs:
        fields = ["candidate_preparation_seconds", "plan_generation_seconds", "feature_extraction_seconds",
                  "prediction_seconds", "ranking_seconds", "total_request_seconds"]
        rows = [[r.get("credit_experiment"), r.get("candidate_mode"), r.get("model"), r.get("measurement_count"),
                 *[f"{_fmt(r.get(field+'_mean'))}/{_fmt(r.get(field+'_p95'))}" for field in fields]]
                for r in run["summary"].get("latency_summary", [])]
        lines += [f"### Latency — `{run['id']}`\n",
            _table(["الحمل", "الوضع", "النموذج", "N", "تجهيز المرشحات", "توليد الخطط", "استخراج الميزات", "التنبؤ", "الترتيب", "إجمالي الطلب"], rows),
            "للمقارنة الزمنية المقترنة فقط، الجدول التالي يحصر الطلاب الذين توفرت لهم نتيجة النموذج في الوضعين، ويميز الحملين. نسبة أكبر من 1 تعني ارتفاع متوسط زمن الطلب في هذه العينة، دون إسناد سببي مستقل عن حجم الخطط والسياق.\n",
            _table(["الحمل", "النموذج", "طلاب مقترنون", "mean request O→A", "p95 request O→A", "نسبة A/O"], _stage_summary(run)),
            f"زمن التوقع المستقل للفعليات في التشغيل: {_fmt(run['manifest'].get('observed_prediction_seconds'))} ثانية؛ زمن الدفعة المسجل شامل الإعداد/الحماية: {_fmt(run['manifest'].get('elapsed_seconds'))} ثانية.\n"]
    lines += ["## 7. Historical Validity\n",
        "يمكن استنتاج أثر إزالة نقص المواد من المرشحات على إمكانية وصول البحث إليها وعلى ترتيبها داخل الجزء المفحوص. ويمكن مقارنة أخطاء توقع الخطة الفعلية بصورة وصفية مشروطة بلقطة Student API الحالية.\n",
        "لا تثبت التجربة أن المواد المحقونة كانت `IS_REQUESTABLE` تاريخيًا، أو أن الخطة كانت معتمدة أكاديميًا، أو أن أفضل ثلاث بدائل سترفع الأداء الحقيقي. لا تتوفر نتائج مضادة للواقع للمواد التي لم يسجلها الطالب. كتالوج البنية غير مثبت زمنيًا، ولقطات API الحالية لا تعادل تلقائيًا لقطة ما قبل قرار 20251. `official_registration_validated=false` باقٍ.\n",
        "لم يُغيّر الحقن Student Snapshot لحل فروق V2. التفسير المتفق عليه لـ`TOTAL_*` كبداية الفصل باقٍ، لكن تكافؤ كامل اللقطة مع ميزات التدريب غير مثبت. لذلك لا تُستخدم زيادة Overlap وحدها لترقية نموذج أو تغيير قواعد الإنتاج.\n",
        "### Validation evidence\n"]
    lines += _validation_lines(validation, validation_path)
    warnings = sorted({warning for run in runs for warning in run["summary"].get("warnings", [])})
    lines += ["### Saved warnings\n", "\n".join("- `" + str(warning) + "`" for warning in warnings) + "\n",
        "## 8. Next Steps\n",
        "الخطوات المقترحة التالية غير منفذة:\n",
        "1. تثبيت عقد Backend موحد `as_of/effective_time` قبل التسجيل يربط الطالب والدرجة ونسخة المنهج والأهلية والعروض والقواعد؛ حفظ المواد المسموحة والمرفوضة مع الأسباب.\n"
        "2. توثيق مصدر وتوقيت `TOTAL_*` وعدادات الفصول والمحاولات وربط انتقالات الدرجات، مع الاحتفاظ بالقيم الأصلية وعدم استبدالها تلقائيًا ببديل محلي.\n"
        "3. إعادة التقييم على نفس النماذج بعد وصول مرشحات أصلية ثابتة زمنياً؛ فصل توقع الخطة المسجلة عن جودة التوصيات والاعتماد الأكاديمي.\n"
        "4. دراسة انحياز include-first واستقرار Top-3 تحت ميزانيات وترتيبات بحث معلنة في تجربة منفصلة؛ لا يُستنتج أن زيادة الميزانية وحدها تحل نقص المرشحات أو الأهلية.\n",
        "## 9. Branch Exit Instructions\n",
        "الفرع التجريبي المعتمد `new_branch`، وHEAD الأساسي في جدول Git أعلاه. سجل Git يثبت الانتقال من `expirennets` إلى `new_branch` عند الالتزام `19c0870c3bfb2ff7695a45c29ce2bddc3d6690ce`؛ هذا يثبت فرع الرجوع السابق، ولا يغير دور أي فرع آخر اسمه Production. لم يُنفذ هذا العمل Commit أو push أو merge أو تبديل فرع.\n",
        "قائمة النقل المسموح بها إلى فرع الأصل لاحقًا هي التقرير وهذا التصدير المنقح فقط. يجب التحقق من وجود ملفات `portable_results` قبل نسخها؛ مولد التقرير لا يُنشئها تلقائيًا.\n"]
    portable = [[_link(DEFAULT_OUTPUT, "التقرير النهائي"), "نص النتائج والقيود دون كود تجريبي"]]
    for run in runs:
        for name, description in [("metrics_summary.json", "مقاييس مجمعة فقط"), ("latency_summary.json", "أزمنة مجمعة فقط"),
                                   ("student_summary.csv", "معرفات عينات مستعارة وأرقام/حالات فقط؛ بلا مواد أو provenance"),
                                   ("provenance.json", "Branch/HEAD/configuration وSHA256 فقط؛ بلا payload أو سجل هويات")]:
            path = run["directory"] / "portable_results" / name
            portable.append([_link(path), description + (" — موجود" if path.is_file() else " — لم يثبت إنشاؤه بعد")])
    lines += [_table(["مسار النقل المحدد", "المحتوى"], portable),
        "لا تنقل `student_results.json` أو `original_results.json` أو `augmented_results.json` أو `injected_courses.json` أو `protected_files.json` أو `student_metrics.csv` أو exports المواد/الخطط الكاملة؛ هذه ملفات تجربة محلية وقد تحتوي payload أو مرشحات/تفاصيل حقن أو هويات. ولا تنقل `actual_*.py` أو الاختبارات أو تعديلات engine/app/static أو Graphify. تبقى الملفات الكاملة محفوظة في فرع التجربة للتحقق المحلي.\n",
        "قبل الرجوع، انسخ قائمة النتائج المنقحة والتقرير إلى مكان آمن خارج checkout. افحص `git status`، ثم يمكنك يدوياً حفظ تعديلات هذه التجربة بـ`git stash push --include-untracked -m pilot-20251-actual-candidates`، وبعد التحقق من المرجع السابق استخدم `git switch expirennets`. أعد نسخ التقرير والملخصات المحددة فقط من النسخة الخارجية؛ لا تطبق stash على فرع الرجوع. لاستكمال التجربة لاحقاً، ارجع إلى `new_branch` أولاً ثم استعد stash المناسب. ملفات data المتجاهلة من Git لا يحفظها stash وتبقى محلياً؛ احتفظ بنسخة مستقلة منها إن احتجت الأرشيف الكامل. تبديل الفرع وحده لا يعزل التعديلات غير المحفوظة. لم تُنفذ هذه الأوامر هنا.\n"]
    return "\n".join(lines).rstrip() + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", action="append", required=True)
    parser.add_argument("--output", type=Path, help='New report path; existing reports are never overwritten')
    parser.add_argument("--validation", type=Path)
    args = parser.parse_args(argv)
    if len(args.run_id) != len(set(args.run_id)):
        parser.error("Run IDs must be distinct.")
    runs = [load_run(run_id) for run_id in args.run_id]
    if args.output is None:
        from datetime import datetime, timezone
        args.output = DEFAULT_OUTPUT.with_name(DEFAULT_OUTPUT.stem + '_' +
            datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%f') + '.md')
    validation = _read(args.validation) if args.validation else None
    report = render_report(runs, validation=validation, validation_path=args.validation)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as stream:
        stream.write(report)
    print(json.dumps({"report": str(args.output.resolve()), "run_ids": args.run_id, "inference_performed": False}, ensure_ascii=True))


if __name__ == "__main__":
    main()
