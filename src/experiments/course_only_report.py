"""Render measured experiment evidence, including limitations and no-promotion status."""
import json

import pandas as pd

from src.paths import (
    COURSE_ONLY_DEBUG_DIR, COURSE_ONLY_EVALUATION_DIR, COURSE_ONLY_MODEL_DIR,
    COURSE_ONLY_REPORT_PATH, PROJECT_ROOT,
)
from .course_only_core import COURSE_ONLY_FEATURES, REMOVED_CONTEXT_FEATURES


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def table(frame):
    """Small Markdown table without requiring optional tabulate."""
    def cell(value):
        if isinstance(value, float):
            return f"{value:.9f}"
        return str(value).replace("|", "\\|").replace("\n", " ")
    header = "| " + " | ".join(str(c) for c in frame.columns) + " |\n"
    header += "| " + " | ".join("---" for _ in frame.columns) + " |\n"
    return header + "\n".join("| " + " | ".join(cell(v) for v in row) + " |" for row in frame.itertuples(index=False, name=None))


def plan_table(plans, *, official=False):
    columns = ["rank", *( ["trace_plan_id"] if official else []), "course_ids", "total_credits",
               "expected_quality_points", "expected_plan_gpa", "projected_cumulative_gpa", "expected_failed_credits"]
    rows = []
    for rank, plan in enumerate(plans, 1):
        row = {name: plan[name] for name in columns if name not in ["rank", "course_ids", "trace_plan_id"]}
        row.update({"rank": rank, "course_ids": ", ".join(plan["course_ids"])})
        if official:
            row["trace_plan_id"] = plan["plan_id"]
        rows.append(row)
    return table(pd.DataFrame(rows)[columns])


def build_report(metadata, primary, batch, verified):
    """Build the user's requested summary plus complete audit tables from saved runs."""
    official = read_json(COURSE_ONLY_DEBUG_DIR / "official_top10.json")
    experimental = read_json(COURSE_ONLY_DEBUG_DIR / "experimental_top10.json")
    sensitivity = read_json(COURSE_ONLY_DEBUG_DIR / "sensitivity_summary.json")
    selection = read_json(COURSE_ONLY_EVALUATION_DIR / "batch_selection.json")
    dist = batch["distributions"]
    grade, fail = metadata["grade"], metadata["fail"]
    gm47, gm33 = grade["official_test_metrics_fresh"], grade["experimental_test_metrics"]
    fm47, fm33 = fail["official_test_metrics_fresh"], fail["experimental_test_metrics"]
    bool_text = lambda x: "YES" if x else "NO"
    lines = ["# COURSE-ONLY 33-FEATURE EXPERIMENT", "",
             "**Recommendation: KEEP EXPERIMENTAL.** أثر حذف السياق على مقاييس المودلين صغير، وتقليل صفوف التنبؤ كبير. "
             "لكن تطابق أفضل الخطط منخفض، والتسريع الفعلي محدود بكلفة البحث الشامل. لا تكفي هذه العينة لترقية النظام. "
             "لم تتم أي promotion أو كتابة فوق artifacts رسمية.", "",
             "## Requested final summary", "", "```text", "COURSE-ONLY 33-FEATURE EXPERIMENT", "",
             "Features:", "Official: 47", "Experimental: 33", "Removed plan/peer features: 14", "",
             "Grade:", f"Official test MAE: {gm47['mae']:.9f}", f"Experimental test MAE: {gm33['mae']:.9f}",
             f"Delta: {gm33['mae'] - gm47['mae']:+.9f}", "",
             "Fail:", f"Official LogLoss: {fm47['log_loss']:.9f}", f"Experimental LogLoss: {fm33['log_loss']:.9f}",
             f"Delta: {fm33['log_loss'] - fm47['log_loss']:+.9f}",
             f"Official PR-AUC: {fm47['pr_auc']:.9f}", f"Experimental PR-AUC: {fm33['pr_auc']:.9f}",
             f"Delta: {fm33['pr_auc'] - fm47['pr_auc']:+.9f}", "",
             "Plan-context sensitivity (80 student-course pairs in six additional test scenarios):",
             f"Median predicted-mark range: {batch['sensitivity']['predicted_mark_range']['median']:.9f}",
             f"P90: {batch['sensitivity']['predicted_mark_range']['p90']:.9f}",
             f"P95: {batch['sensitivity']['predicted_mark_range']['p95']:.9f}", "",
             "Student 29485.111:", f"Candidates: {primary['candidate_courses']}",
             f"Official course-in-plan prediction rows: {primary['official_course_in_plan_prediction_rows']}",
             f"Experimental course prediction rows: {primary['experimental_course_prediction_rows']}", "", "Official Top 3:"]
    lines.extend(f"{i}. {', '.join(plan['course_ids'])}" for i, plan in enumerate(official[:3], 1))
    lines.extend(["", "Experimental Top 3:"])
    lines.extend(f"{i}. {', '.join(plan['course_ids'])}" for i, plan in enumerate(experimental[:3], 1))
    lines.extend(["", f"Exact Top-1 match: {bool_text(primary['top1_recall_at_1'])}",
                  f"Official Top-1 in experimental Top-3: {bool_text(primary['top1_recall_at_3'])}",
                  f"Official Top-3 recall@3: {primary['top3_recall_at_3']:.9f}",
                  f"Official Top-3 recall@10: {primary['top3_recall_at_10']:.9f}", "",
                  f"Official best projected GPA: {primary['official_best_projected_gpa']:.9f}",
                  f"Experimental best projected GPA: {primary['experimental_best_projected_gpa']:.9f}",
                  f"Regret (requested cross-model gap): {primary['projected_gpa_regret_cross_model']:.9f}", "",
                  f"Runtime official: {primary['official_runtime_seconds']:.9f} seconds",
                  f"Runtime experimental: {primary['experimental_runtime_seconds']:.9f} seconds",
                  f"Speedup: {primary['runtime_speedup']:.3f}x", "", f"Batch: {batch['cases']} additional cases",
                  f"Top-1 recall@1: {dist['top1_recall_at_1']['mean']:.9f}",
                  f"Top-1 recall@3: {dist['top1_recall_at_3']['mean']:.9f}",
                  f"Top-1 recall@10: {dist['top1_recall_at_10']['mean']:.9f}",
                  f"Top-3 recall@10: {dist['top3_recall_at_10']['mean']:.9f}",
                  f"Median projected-GPA regret: {dist['projected_gpa_regret_cross_model']['median']:.9f}",
                  f"P95 regret: {dist['projected_gpa_regret_cross_model']['p95']:.9f}",
                  f"Prediction reduction (median): {dist['prediction_row_reduction_percent']['median']:.6f}%",
                  f"Runtime speedup (median): {dist['runtime_speedup']['median']:.3f}x", "",
                  f"Official artifacts modified: {bool_text(verified['official_artifacts_modified'])}",
                  f"Official Recommendation modified: {bool_text(verified['official_recommendation_modified'])}", "",
                  "Recommendation: KEEP EXPERIMENTAL", "```", "",
                  "## Training and feature contract", "",
                  f"Train: **{metadata['train_rows']:,}** rows through **{metadata['training_as_of_part']}**; "
                  f"holdout: **{metadata['test_rows']:,}** rows in 20251/20252. المصدران هما "
                  "`data/features/temporal_train_features_v2.parquet` و`data/features/temporal_test_features_v2.parquet`. "
                  "لم نعد بناء البيانات أو Frozen History؛ نستعمل الخصائص الزمنية الرسمية كما هي، مع بروتوكول الاختبار sequential roll-forward.", "",
                  "الأهداف: Grade=`final_mark` وFail=`is_fail`. نفس folds: حتى 20223→20231–20233، وحتى 20233→20241–20243. "
                  "نفس weights: 0.25 قبل 2022 و1.0 بعدها أثناء fit فقط. نفس seed=42 وlearning_rate=0.04، "
                  "سقف 900 boosting rounds وearly stopping=75، ونفس configs الثلاثة والفئات مع missing/unknown. "
                  "لم نجرب hyperparameters خارج الشبكة الرسمية. الاختيار من CV فقط، قبل تقييم holdout.", "",
                  f"Experimental Grade winner: **{grade['selected_candidate']['candidate']['name']}**, "
                  f"{grade['final_boost_rounds']} rounds; Fail winner: **{fail['selected_candidate']['candidate']['name']}**, "
                  f"{fail['final_boost_rounds']} rounds. الزمن الكلي للتدريب والتقييم: {metadata['training_seconds']:.2f} seconds. "
                  "الاسم `capaciy_63` في كود التدريب الحالي يحمل typo؛ قيمه العددية هي config الـ63 الرسمية. حافظنا على الكود الرسمي.", "",
                  "القائمة مشتقة برمجيًا من BASE_FEATURES مع الحفاظ على ترتيبها. الحارس يثبت 47−14=33 "
                  "ويثبت أن الفرق الوحيد هو مجموعة الـ14 المطلوبة. لا يحتاج بناء مصفوفة inference إلى أي plan/peer columns.", "",
                  "```text", *COURSE_ONLY_FEATURES, "```", "", "Removed:", "", "```text", *sorted(REMOVED_CONTEXT_FEATURES), "```", "",
                  "## Grade and Fail holdout comparisons", "",
                  "كل أرقام holdout أدناه حُسبت مجددًا من المودلين الرسميين والتجريبيين على الصفوف نفسها. "
                  "الأرقام غير موزونة عند التقييم، مثل التدريب الرسمي، والعلامات clipped إلى [0,100]. "
                  "أما Official CV فهو محفوظ في metadata الرسمية ولم نعد تدريب baseline. Experimental CV جديد. "
                  "لا نسمي CV الرسمي إعادة قياس جديدة.", ""])
    rows = [{"Grade metric": name, "Official 47": gm47[name], "Experimental 33": gm33[name],
             "Delta 33 minus 47": gm33[name] - gm47[name]} for name in ["mae", "rmse", "within_5", "within_10"]]
    rows.append({"Grade metric": "CV mean MAE (official saved)", "Official 47": grade["official_cv_mean_saved"],
                 "Experimental 33": grade["selected_candidate"]["mean_primary_metric"],
                 "Delta 33 minus 47": grade["selected_candidate"]["mean_primary_metric"] - grade["official_cv_mean_saved"]})
    lines.extend([table(pd.DataFrame(rows)), ""])
    rows = [{"Fail metric": name, "Official 47": fm47[name], "Experimental 33": fm33[name],
             "Delta 33 minus 47": fm33[name] - fm47[name]} for name in ["pr_auc", "roc_auc", "brier", "log_loss", "calibration_error_10_bins"]]
    rows.append({"Fail metric": "CV mean LogLoss (official saved)", "Official 47": fail["official_cv_mean_saved"],
                 "Experimental 33": fail["selected_candidate"]["mean_primary_metric"],
                 "Delta 33 minus 47": fail["selected_candidate"]["mean_primary_metric"] - fail["official_cv_mean_saved"]})
    lines.extend([table(pd.DataFrame(rows)), "", "## Direct plan-context sensitivity", "",
                  "التجميع لكل (student_id, course_id) عبر جميع الخطط المطابقة، وليس Top K فقط. "
                  "std يستخدم population ddof=0. العينة الرئيسية منفصلة عن عينة batch لتجنب مضاعفة الطالب.", ""])
    rows = [{"cohort": cohort, "metric": metric, **summary[metric]}
            for cohort, summary in [("student 29485.111 (15 pairs)", sensitivity), ("batch (80 pairs)", batch["sensitivity"])]
            for metric in ["predicted_mark_range", "fail_probability_range"]]
    lines.extend([table(pd.DataFrame(rows)), "",
                  table(pd.read_parquet(COURSE_ONLY_DEBUG_DIR / "official_plan_context_sensitivity.parquet")), "",
                  "**السياق الصغير قد يغيّر نقاط السلم.** للمادة `311.111` يتراوح التوقع الرسمي بين "
                  "84.919151 و85.012568، فينتقل expected_points من 3.00 إلى 3.25 عند threshold=85. "
                  "توقع 33-feature للمادة 84.746962، أي 3.00 points. فرق 0.25 quality points لمادة ساعة واحدة "
                  "يكفي هنا لفرق projected GPA يساوي 0.25/86=0.002906977. لذلك range صغير في العلامة لا يعني "
                  "أن Plan Context بلا أثر على ترتيب الخطط.", "", "## Student 29485.111: all 15 course predictions", "",
                  "الطلب نفسه: degree=42.111، target=20251، exportdata (7).json، مطلوب 12–18→exact18، "
                  "history_v2/as_of_20243، current GPA=3.12 وprior registered credits=68. "
                  "GradeScale الرسمي باستخدام grade_version_id=3.111 بعد clip، دون direct-points model.", "",
                  table(pd.read_csv(COURSE_ONLY_DEBUG_DIR / "course_scores_33.csv", dtype={"course_id": str})), "",
                  "## Official Top 3 versus experimental Top 10", "",
                  "plan_id أدناه للتتبع فقط؛ كل التطابقات محسوبة من مجموعات course_ids.", "",
                  plan_table(official[:3], official=True), "", plan_table(experimental), "",
                  "جميع الخطط 18 ساعة؛ تعظيم Q يعظم المعدل الفصلي والتراكمي لنفس الطالب. "
                  "محسّن التجربة يبحث في جميع المرشحين وجميع 2,503 combinations، ثم يرتب Q DESC، "
                  "expected_failed_credits ASC، ثم tuple معرّفات المواد ترتيبًا ثابتًا. يحتفظ بـTop 10 ويصدر Top 3 منفصلًا. "
                  "الحساب الدقيق يحافظ على الساعات الكسرية والمواد الاختيارية ذات الصفر ساعة.", "",
                  table(pd.DataFrame([{"comparison": key, "value": primary[key]} for key in [
                      "top1_recall_at_1", "top1_recall_at_3", "top1_recall_at_10", "top3_recall_at_3", "top3_recall_at_10",
                      "projected_gpa_regret_cross_model", "expected_plan_gpa_regret_cross_model",
                      "expected_failed_credits_difference_exp_minus_official", "official_rescored_projected_gpa_regret", "official_rescored_plan_gpa_regret"]])), "",
                  "## Runtime", "",
                  "الزمن هو median لثلاث تشغيلات in-memory لكل سيناريو، بترتيب رسمي/تجريبي متناوب، "
                  "4 inference threads لكلا المسارين. يدخل بناء rows/السياق والتنبؤ وتلخيص/ترتيب الخطط؛ "
                  "يستثني تحميل المدخلات والمودلز والتاريخ والكتابة على القرص لأنها مشتركة/خارج hot path. "
                  "هذا ليس قياس latency شاملًا للـCLI. صفوف التنبؤ محسوبة لكل مودل: الرسمي 21,235 Grade و21,235 Fail؛ "
                  "التجريبي 15 Grade و15 Fail. لا نقارن عددًا مضاعفًا في جانب بغير مضاعف في الآخر.", "",
                  table(pd.DataFrame([
                      {"metric": "candidate courses", "Official": primary["candidate_courses"], "Experimental": primary["candidate_courses"]},
                      {"metric": "prediction rows per model", "Official": primary["official_course_in_plan_prediction_rows"], "Experimental": primary["experimental_course_prediction_rows"]},
                      {"metric": "model prediction calls", "Official": primary["official_model_prediction_calls"], "Experimental": primary["experimental_model_prediction_calls"]},
                      {"metric": "matching combinations", "Official": primary["official_matching_plans"], "Experimental": primary["optimizer_combinations"]},
                      {"metric": "runtime seconds median", "Official": primary["official_runtime_seconds"], "Experimental": primary["experimental_runtime_seconds"]},
                  ])), "",
                  f"Prediction row reduction: **{primary['prediction_row_reduction_factor']:.3f}× / {primary['prediction_row_reduction_percent']:.6f}%**; "
                  f"runtime speedup: **{primary['runtime_speedup']:.3f}×**. "
                  "البحث الشامل نفسه ما زال موجودًا؛ لا نتوقع أن تنخفض كلفة end-to-end بنسبة صفوف المودل نفسها.", "",
                  "Measured runtime repetitions:", "", "```json",
                  json.dumps({"official_seconds": primary["official_runtime_repeats"], "experimental_seconds": primary["experimental_runtime_repeats"]}, indent=2), "```", "",
                  "## Batch distributions", "",
                  "ستة طلاب إضافيين من test 20251؛ عينة convenience حتمية من قوائم export المتاحة، "
                  "وليست عينة عشوائية من الجامعة. الطالب الرئيسي خارج إحصاءات batch. المقبول 2–18 candidates "
                  "مع snapshot صالح وخطة exact18؛ تفاصيل اختيار/استبعاد جميع المصادر محفوظة في batch_selection.json.", "",
                  table(pd.read_parquet(COURSE_ONLY_EVALUATION_DIR / "batch_comparisons.parquet")[[
                      "student_id", "degree_id", "candidate_courses", "official_matching_plans", "top1_recall_at_1",
                      "top1_recall_at_3", "top1_recall_at_10", "top3_recall_at_10", "projected_gpa_regret_cross_model",
                      "official_rescored_projected_gpa_regret", "runtime_speedup", "prediction_row_reduction_percent"]]), "",
                  table(pd.DataFrame([{"metric": name, **value} for name, value in dist.items()])), "",
                  "الأعمدة cross_model تحقق الفرق المطلوب: official_best − experimental_best باستخدام "
                  "توقعات كل مودل نفسه؛ قد يكون الفرق سالبًا ولا يعد تقدير خسارة فعلية. "
                  "لذلك أضفنا official_rescored: قيّمنا خطة التجربة الأفضل تحت المودل الرسمي نفسه، "
                  "ثم طرحناها من optimum الرسمي. هذا يعزل خسارة اختيار خطة وفق criterion رسمي، "
                  "ولا يجعله حقيقة مستقبلية للطالب. Quantiles لعينة من ستة أرقام وصفية وغير مستقرة إحصائيًا.", "",
                  "Excluded during candidate/snapshot selection:", "", table(pd.DataFrame(selection["excluded"])), "",
                  "No-feasible-plan cases (excluded from ranking overlap, retained in audit):", "", table(pd.DataFrame(batch["failures"])), "",
                  "## Decision evidence", "",
                  f"**A — Model loss:** Grade MAE +{gm33['mae'] - gm47['mae']:.6f}; Fail LogLoss "
                  f"+{fm33['log_loss'] - fm47['log_loss']:.6f}; PR-AUC {fm33['pr_auc'] - fm47['pr_auc']:+.6f}. "
                  "خسارة صغيرة على holdout نفسه، دون مجال ثقة أو تحقق إضافي يثبت تكافؤًا إحصائيًا.", "",
                  "**B — Context effect:** primary median mark range=0.127520 وP95=0.271346؛ "
                  "batch median=0.444743 وP95=2.295168. عبور حدود GradeScale يفسر أهمية تغيرات صغيرة لبعض المواد.", "",
                  "**C — Same best plan:** primary Top-1 غير موجود حتى في Experimental Top-10؛ "
                  "batch التطابق exact Top-1 في 1/6، ووجوده في Top-3 في 3/6، وTop-10 في 5/6. "
                  "تطابق course sets صارم وقد ينخفض بين خطط متعادلة GPA لكن مختلفة المخاطر.", "",
                  "**D — Difference cost:** primary projected GPA gap=0.002906977. Batch cross-model median=0.002739461 "
                  "وP95=0.015543559؛ official-rescored median=0.000336927 وP95=0.007970593. "
                  "الأرقام توقعات نماذج وسيناريو additive؛ سياسة إعادة المواد وتحقق النتائج الفعلية غير مقاسين هنا.", "",
                  f"**E — Runtime:** primary {primary['runtime_speedup']:.3f}×؛ batch median "
                  f"{dist['runtime_speedup']['median']:.3f}×. تقليل صفوف التنبؤ ممتاز لكن search exhaustive يحد كسب الزمن. "
                  "هذه النسخة البسيطة مناسبة لهذه الأعداد؛ لا توجد دعوى scalability على عشرات كثيرة من المرشحين.", "",
                  "**الحكم: KEEP EXPERIMENTAL.** هناك دليل يدعم متابعة architecture الأبسط، لكن overlap المنخفض "
                  "والعينة الصغيرة يمنعان اعتماد بديل رسمي تلقائيًا. لا تغيير في Recommendation V2 ولا proposal لتنفيذ promotion.", "",
                  "## Isolation, provenance and validation", "",
                  f"تمت مقارنة SHA-256 قبل/بعد لـ**{verified['protected_files']}** ملفًا محميًا؛ changed={verified['changed']}. "
                  "يشمل المصدر الرسمي والمودلز V1/V2 والمدخلات وcategory artifacts وFrozen History والـtrace السابق. "
                  "التعديلات السابقة في working tree حافظنا عليها. المضاف في src/paths.py ثوابت namespace التجربة فقط.", "",
                  "Dependency test يسمح فقط لثلاث ملفات workflow تجريبية جديدة بقراءة src/recommendation، "
                  "مثل استثناء XML evaluator الحالي. لم نخف الاستيراد ولم نغير اعتماد Features أو Modeling على التجارب.", "",
                  "Validation: انظر `validation_summary.json` وlogs في مجلد نتائج التجربة. "
                  "الفشل السابق في اختبار trainer بسبب capaciy_63 محفوظ ومذكور منفصلًا؛ لم نعدل config الرسمي لحل typo.", "",
                  "Provenance: training_signature يسجل SHA-256 لملفي features، المصدر التدريبي الرسمي، "
                  "العقد الرسمي، كود التدريب/المصفوفة التجريبي، والـbaseline الرسمي وفئاته. "
                  "مدخل JSON له بصمة في import_report.json لكل حالة. إعادة التحميل --skip-training ترفض تغير signature أو model headers/hashes. "
                  "استقلال المسارات لا يلغي أي selection bias موروث في البيانات الرسمية؛ لا ندعي معالجة cleaning أو قياس causal outcomes.", "",
                  "```powershell", r".\.venv\Scripts\python.exe -m src.experiments.course_only_recommendation --skip-training", "```", "",
                  "Artifacts and evidence:", ""])
    for label, path in [("Report", COURSE_ONLY_REPORT_PATH), ("Experimental models", COURSE_ONLY_MODEL_DIR),
                        ("Evaluation results", COURSE_ONLY_EVALUATION_DIR), ("Student details / CSV / Top 3 / Top 10", COURSE_ONLY_DEBUG_DIR)]:
        relative = path.relative_to(PROJECT_ROOT).as_posix()
        lines.append(f"- {label}: `{relative}`")
    validation_path = COURSE_ONLY_EVALUATION_DIR / "validation_summary.json"
    if validation_path.exists():
        validation = read_json(validation_path)
        focused, full = validation["focused_tests"], validation["full_suite"]
        lines.extend(["", "Fresh verification results:", "",
                      f"Focused: **{focused['passed']} passed, {focused['failed']} failed**. "
                      f"Full suite: **{full['passed']} passed, {full['failed']} failed**, {full['subtests_passed']} subtests passed.", "",
                      f"Remaining pre-existing failure: `{full['failure']}`. {full['cause']}.", ""])
    COURSE_ONLY_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    COURSE_ONLY_REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Report: {COURSE_ONLY_REPORT_PATH}", flush=True)
    return COURSE_ONLY_REPORT_PATH
