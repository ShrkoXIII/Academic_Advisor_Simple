"""Aggregate outputs and descriptive candidate envelopes for the isolated audit."""
import json

import numpy as np
import pandas as pd

from src.diagnostics.repeat_withdrawal_balance import describe_metrics, credit_bins


SEMESTER_METRICS = [
    "available_failed_credits", "available_withdrawn_credits",
    "registered_failed_retake_credits", "registered_withdrawn_retake_credits",
    "registered_new_credits", "registered_other_previous_credits",
    "semester_total_registered_credits", "failed_retake_ratio", "withdrawn_retake_ratio",
    "previously_attempted_ratio", "new_credit_ratio", "other_previous_ratio",
    "failed_backlog_consumption_ratio", "withdrawn_backlog_consumption_ratio",
]


def write_json(path, value):
    def encode(obj):
        if isinstance(obj, np.generic):
            return obj.item()
        raise TypeError(type(obj).__name__)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False,
                               default=encode), encoding="utf-8")


def markdown_table(frame):
    def value(item):
        if pd.isna(item):
            return "NA"
        if isinstance(item, (float, np.floating)):
            return f"{item:.3f}"
        return str(item).replace("|", "/")
    lines = ["| " + " | ".join(frame.columns) + " |", "| " + " | ".join(["---"] * len(frame.columns)) + " |"]
    lines.extend("| " + " | ".join(value(v) for v in row) + " |" for row in frame.itertuples(index=False, name=None))
    return "\n".join(lines)


def cohorts(cases):
    failed = cases.available_failed_credits.gt(0)
    withdrawn = cases.available_withdrawn_credits.gt(0)
    reference = cases.part_type.eq("parts_1_2") & cases.semester_total_registered_credits.between(12, 18) & cases.registered_other_previous_courses.eq(0)
    return {
        "all": cases, "failed_available": cases[failed],
        "withdrawn_available": cases[withdrawn], "both_available": cases[failed & withdrawn],
        "any_available": cases[failed | withdrawn],
        "failed_available_and_repeated": cases[failed & cases.registered_failed_retake_courses.gt(0)],
        "withdrawn_available_and_repeated": cases[withdrawn & cases.registered_withdrawn_retake_courses.gt(0)],
        "policy_reference_any": cases[reference & (failed | withdrawn)],
        "policy_reference_failed": cases[reference & failed],
        "policy_reference_withdrawn": cases[reference & withdrawn],
        "policy_reference_both": cases[reference & failed & withdrawn],
    }


def policy_candidates(cases):
    """Return conditional, marginal quantile ranges; no optimality or legal inference.

    Component quantiles come from cases with that backlog. Combined/new quantiles
    come from any-backlog cases. These are separate descriptive penalty bands,
    not a simultaneous quota: a plan still needs ratios summing to one.
    """
    groups = cohorts(cases)
    reference = groups["policy_reference_any"]
    failed, withdrawn = groups["policy_reference_failed"], groups["policy_reference_withdrawn"]
    enough = (len(reference) >= 100 and
              failed.registered_failed_retake_courses.gt(0).sum() >= 30 and
              withdrawn.registered_withdrawn_retake_courses.gt(0).sum() >= 30)
    result = dict(evidence="SUFFICIENT_FOR_DESCRIPTIVE_CANDIDATES" if enough else "INSUFFICIENT EVIDENCE",
                  hard_university_limit={"allowed_failed_repeat_credits": "BACKEND_ONLY"},
                  reference="Roster target semesters, parts 1/2, registered credits 12..18, no registered other-prior courses, positive failed/withdrawn backlog",
                  reference_cases=len(reference), reference_students=int(reference.student_id.nunique()),
                  component_reference_cases={"failed": len(failed), "withdrawn": len(withdrawn)},
                  minimum_descriptive_support="100 any-backlog cases and 30 observed repeats per component; operational screen, not statistical proof",
                  interpretation="Marginal conditional quantile envelopes, not quotas. Missing backlog disables its component; new is the feasible residual. Joint combinations must be tested. Student semesters are dependent.",
                  priority="Failure and withdrawal have separate evidence; historical prevalence does not establish academic priority.",
                  policies=[])
    if not enough:
        return result
    for name, lower, upper in [("A_conservative", .25, .5), ("B_observed_middle", .5, .75), ("C_retake_heavier", .75, .9)]:
        def band(frame, column):
            values = frame[column].dropna()
            return [float(values.quantile(lower)), float(values.quantile(upper))]
        policy = dict(name=name, percentile_band=[lower, upper],
                      failed_component={"condition": "available_failed_credits>0", "preferred_ratio": band(failed, "failed_retake_ratio"), "observed_credits": band(failed, "registered_failed_retake_credits")},
                      withdrawn_component={"condition": "available_withdrawn_credits>0", "preferred_ratio": band(withdrawn, "withdrawn_retake_ratio"), "observed_credits": band(withdrawn, "registered_withdrawn_retake_credits")},
                      total_previous_component={"condition": "either backlog>0", "preferred_ratio": band(reference, "previously_attempted_ratio")},
                      new_component={"observed_ratio": band(reference, "new_credit_ratio"),
                                     "preferred_ratio_from_total_residual": [1-float(reference.previously_attempted_ratio.quantile(upper)), 1-float(reference.previously_attempted_ratio.quantile(lower))]},
                      proposed_use="Soft penalty envelope for future testing; no required minimum, no hard ceiling, no promotion")
        result["policies"].append(policy)
    result["recommended_starting_candidate"] = "B_observed_middle"
    return result


def aggregate_outputs(cases, students, output):
    groups = cohorts(cases)
    distributions = pd.concat([describe_metrics(frame, SEMESTER_METRICS, name) for name, frame in groups.items()], ignore_index=True)
    distributions.to_csv(output / "credit_distribution.csv", index=False)
    describe_metrics(students, ["failed_credits", "withdrawn_credits", "failed_credit_ratio", "withdrawn_credit_ratio"]).to_csv(output / "student_history_distribution.csv", index=False)
    cases.to_csv(output / "student_semester_mix.csv", index=False)
    students.to_csv(output / "student_history.csv", index=False)
    buckets = []
    for name, frame in groups.items():
        for label in ["failed", "withdrawn"]:
            buckets.append(credit_bins(frame[f"registered_{label}_retake_credits"]).assign(cohort=name, component=label))
    pd.concat(buckets, ignore_index=True).to_csv(output / "retake_credit_buckets.csv", index=False)
    mixes = cases.groupby("mix_type").agg(case_count=("target_part", "size"),
        median_total_credits=("semester_total_registered_credits", "median"),
        median_failed_credits=("registered_failed_retake_credits", "median"),
        median_withdrawn_credits=("registered_withdrawn_retake_credits", "median"),
        median_new_credits=("registered_new_credits", "median")).reset_index()
    mixes["percentage"] = 100 * mixes.case_count / len(cases)
    mixes = mixes.sort_values("case_count", ascending=False)
    mixes.to_csv(output / "mix_distribution.csv", index=False)
    components = ["registered_failed_retake_credits", "registered_withdrawn_retake_credits", "registered_new_credits", "registered_other_previous_credits", "semester_total_registered_credits"]
    common = cases.groupby(components).size().rename("case_count").reset_index().sort_values("case_count", ascending=False)
    common["percentage"] = 100 * common.case_count / len(cases)
    common.to_csv(output / "common_credit_mixes.csv", index=False)
    typed_mixes = cases.groupby(["mix_type"] + components).size().rename("case_count").reset_index()
    typed_mixes["percentage_within_type"] = 100 * typed_mixes.case_count / typed_mixes.groupby("mix_type").case_count.transform("sum")
    typed_mixes.sort_values(["mix_type", "case_count"], ascending=[True, False]).to_csv(output / "common_credit_mixes_by_type.csv", index=False)
    segments = []
    for name, frame in groups.items():
        for bucket, subset in frame.groupby("load_bucket", sort=True):
            segments.append(describe_metrics(subset, SEMESTER_METRICS, f"{name}/load={bucket}"))
    pd.concat(segments, ignore_index=True).to_csv(output / "load_distribution.csv", index=False)
    segments = []
    for column in ["part_type", "target_part", "degree_id"]:
        for key, subset in cases.groupby(column):
            segments.append(describe_metrics(subset, SEMESTER_METRICS, f"{column}={key}"))
    pd.concat(segments, ignore_index=True).to_csv(output / "semester_and_degree_distribution.csv", index=False)
    probabilities = []
    for name in ["all", "failed_available", "withdrawn_available", "both_available", "policy_reference_any", "policy_reference_both"]:
        frame = groups[name]
        for label in ["failed", "withdrawn"]:
            available = frame[frame[f"available_{label}_credits"].gt(0)]
            repeats = available[f"registered_{label}_retake_courses"].gt(0)
            probabilities.append(dict(cohort=name, component=label, available_cases=len(available),
                available_students=available.student_id.nunique(), repeated_cases=int(repeats.sum()),
                probability_repeat_course=float(repeats.mean()) if len(available) else np.nan,
                probability_positive_repeat_credits=float(available[f"registered_{label}_retake_credits"].gt(0).mean()) if len(available) else np.nan))
    probability_frame = pd.DataFrame(probabilities)
    probability_frame.to_csv(output / "conditional_retake_probabilities.csv", index=False)
    policies = policy_candidates(cases)
    write_json(output / "policy_candidates.json", policies)
    return distributions, mixes, common, probability_frame, policies


def outlier_outputs(cases, audit, output):
    rules = {
        "very_high_failed_backlog_above_p99": cases.available_failed_credits.gt(cases.available_failed_credits.quantile(.99)),
        "very_high_withdrawn_backlog_above_p99": cases.available_withdrawn_credits.gt(cases.available_withdrawn_credits.quantile(.99)),
        "retakes_at_least_90_percent": cases.previously_attempted_ratio.ge(.9),
        "zero_new_credits": cases.registered_new_credits.eq(0),
        "zero_total_credits": cases.semester_total_registered_credits.eq(0),
        "high_load_above_24": cases.semester_total_registered_credits.gt(24),
        "course_credits_24_or_more": cases.max_course_credits.ge(24),
        "failed_consumption_above_one": cases.failed_backlog_consumption_ratio.gt(1),
        "withdrawn_consumption_above_one": cases.withdrawn_backlog_consumption_ratio.gt(1),
    }
    flagged, summaries = [], []
    for name, mask in rules.items():
        subset = cases[mask].copy()
        subset["outlier_reason"] = name
        flagged.append(subset)
        summaries.append(dict(issue=name, affected_cases=len(subset),
            affected_students=subset.student_id.nunique(), part_3_cases=int(subset.part_type.eq("part_3").sum()),
            zero_credit_course_cases=int(subset.zero_credit_courses.gt(0).sum()),
            assessment="Retained observed registrations; not an invalid case solely because extreme. Part 3 timing is known; summer label unverified."))
    pd.concat(flagged, ignore_index=True).to_csv(output / "outlier_cases.csv", index=False)
    change = audit.previous_course_credits.notna() & ~np.isclose(audit.course_credits, audit.previous_course_credits.fillna(audit.course_credits))
    audit[change].to_csv(output / "credit_change_cases.csv", index=False)
    return pd.DataFrame(summaries)


def render_summary(output, cases, status_mapping, distributions, mixes, common, probabilities, policies, metadata, issues):
    all_cases = distributions[distributions.cohort.eq("all")].set_index("metric")
    n = lambda column, percentile="median": float(all_cases.loc[column, percentile])
    crosscheck = pd.read_csv(output / "status_mark_crosscheck.csv")
    f_ge50 = int(crosscheck.loc[crosscheck.finish_status.eq("F"), "marks_ge50"].sum())
    components = ["registered_failed_retake_credits", "registered_withdrawn_retake_credits", "registered_new_credits", "semester_total_registered_credits"]
    mixed = cases[cases.mix_type.isin(["FAILED_AND_NEW", "WITHDRAWN_AND_NEW", "FAILED_WITHDRAWN_AND_NEW"])].groupby(["mix_type"] + components).size().rename("case_count").reset_index()
    top_mixed = mixed.sort_values("case_count", ascending=False).groupby("mix_type", sort=False).head(3)
    lines = [
        f"Students analyzed: {cases.student_id.nunique():,}", f"Student-semesters analyzed: {len(cases):,}",
        f"Students with previous FAILED courses: {cases.loc[cases.available_failed_courses.gt(0), 'student_id'].nunique():,}",
        f"Students with previous WITHDRAWN courses: {cases.loc[cases.available_withdrawn_courses.gt(0), 'student_id'].nunique():,}",
        f"Median failed credits available: {n('available_failed_credits'):.3f}",
        f"Median failed credits actually repeated: {n('registered_failed_retake_credits'):.3f}",
        f"Median withdrawn credits available: {n('available_withdrawn_credits'):.3f}",
        f"Median withdrawn credits actually repeated: {n('registered_withdrawn_retake_credits'):.3f}",
        f"Median new credits per semester: {n('registered_new_credits'):.3f}",
        f"Median previously-attempted ratio: {n('previously_attempted_ratio'):.4f}",
        f"P75 previously-attempted ratio: {n('previously_attempted_ratio','p75'):.4f}",
        f"P90 previously-attempted ratio: {n('previously_attempted_ratio','p90'):.4f}",
        "", "هذه أرقام جميع الفصول؛ نطاقات الاختبار أدناه مشروطة بوجود ساعات لإعادة فعلية.",
        "", "## Most common plan mixes", "", markdown_table(mixes), "",
        "التراكيب الفعلية الأكثر تكرارًا بالساعات (Failed / Withdrawn / New / Other / Total):", "", markdown_table(common.head(10)),
        "", "وسائط المكونات مستقلة، فلا تجمعها لتكوين خطة. هذه أكثر التراكيب المختلطة الفعلية تكرارًا:", "", markdown_table(top_mixed),
        "", "## Status meaning and source evidence", "",
        markdown_table(status_mapping[["finish_status", "semantic_category", "verification", "meaning", "count", "percentage"]]),
        "", "المصدر `v_acs_grade.parquet` يعرّف الرموز بالعربية، و`src/data/clean_student_course.py:16` يصنف F/FE/FA رسوبًا وP نجاحًا. تستخدم العلامات والنقاط للفحص فقط.",
        f"F/FE/FA هنا حالات رسوب المصدر، وتختلف عن هدف المودل `final_mark<50`. في الـRoster {f_ge50} تسجيلًا F بعلامة >=50؛ فحص نطاق grade_id في `grade_range_disagreements.csv` يوثق التعارض، ولا ينسبه تلقائيًا للسلم القديم. كذلك FE قد يحمل علامة >=50 مع صفر نقاط بوصفه رسوب امتحان نهائي. W ليس رسوبًا رغم علامته صفر.",
        "", markdown_table(pd.read_csv(output / "grade_range_disagreements.csv")),
        "D/Z حرمان موثق، لكن لم يثبت دخولهما ضمن إذن إعادة الرسوب الرسمي: OTHER. ST تدريب سريري: OTHER. I/IP حالة غير نهائية: UNRESOLVED. X/L غير موثقين: UNVERIFIED/UNRESOLVED. القيمة المفقودة UNKNOWN. T معادل: OTHER وليس نجاح امتحان مستنتجًا.",
        "", "## Actual availability-conditioned behavior", "",
        markdown_table(probabilities[probabilities.cohort.isin(["failed_available", "withdrawn_available", "both_available"])]),
        "", "التوزيع المشروط: Median / P75 / P90 للساعات والنسب؛ الجدول الكامل مع mean/std/min/p10/p25/p95/max ونسبة الصفر في CSV.", "",
        markdown_table(distributions[distributions.cohort.isin(["failed_available", "withdrawn_available", "both_available"]) & distributions.metric.isin([
            "available_failed_credits", "available_withdrawn_credits", "registered_failed_retake_credits", "registered_withdrawn_retake_credits", "registered_new_credits", "previously_attempted_ratio", "failed_backlog_consumption_ratio", "withdrawn_backlog_consumption_ratio"
        ])][["cohort", "metric", "sample_count", "median", "p75", "p90", "zero_percentage"]]),
        "", "## Suggested candidate balance", "",
        f"مرجع السياسات: {policies['reference_cases']:,} فصلًا لـ{policies['reference_students']:,} طالبًا؛ الفصول 1/2، حمل 12–18، يوجد رصيد Failed أو Withdrawn، ولا توجد مواد مسجلة ذات حالة سابقة أخرى.",
        "هذه نطاقات مرشحة لسلوك مرصود؛ ليست حدودًا جامعية أو دليلًا على سياسة مثلى. Failed وWithdrawn لهما عينتان مشروطتان منفصلتان؛ لا تفترض أولوية متساوية.",
    ]
    for policy in policies["policies"]:
        lines += ["", f"**{policy['name']}**", "",
            f"Failed ratio / credits: {policy['failed_component']['preferred_ratio']} / {policy['failed_component']['observed_credits']}",
            f"Withdrawn ratio / credits: {policy['withdrawn_component']['preferred_ratio']} / {policy['withdrawn_component']['observed_credits']}",
            f"Total previous ratio: {policy['total_previous_component']['preferred_ratio']}",
            f"New feasible residual ratio: {policy['new_component']['preferred_ratio_from_total_residual']}"]
    suggestion = "اقتراح البداية: B_observed_middle (Median–P75)، فقط عند تحقق شروط المرجع ووجود الرصيد المناسب. تفضيلات المكونات هوامش كمية مشروطة، وليست حصصًا تُجمع تلقائيًا؛ new هو الباقي بعد Failed وWithdrawn في الخطة الممكنة. لا تفرض حدًا أدنى للإعادة إذا لم توجد مادة مؤهلة." if policies["policies"] else "INSUFFICIENT EVIDENCE: عينة السياسات لا تستوفي شرط الدعم الوصفي؛ لا يقترح نطاق بداية."
    lines += ["", suggestion,
        "", "HARD UNIVERSITY LIMIT: `allowed_failed_repeat_credits` يأتي من Backend حصريًا، ولا يستنتج من هذه البيانات.",
        "SOFT RECOMMENDATION BALANCE: القيم الرقمية المرشحة محفوظة في `policy_candidates.json`؛ لا يتغير نظام التوصية في هذا التحليل.",
        "", "## Data quality and outliers", "", markdown_table(issues),
        "", "الحالات الشاذة محفوظة في `outlier_cases.csv` مع سببها. التكرارات المتطابقة تدمج في نسخة التحليل مع عدّها؛ المحاولات المتعارضة لنفس الطالب/المادة/الفصل توقف التحليل. ساعات 0 و4.5 و24 محفوظة، ولم تقرب إلى مضاعفات 3.",
        "", "## Limitations", "",
        "- available = أحدث حالة تاريخية Failed/Withdrawn، وليست قائمة مواد مؤهلة في الفصل المستهدف. لا تتوفر عروض أو متطلبات أو أذونات تاريخية لكل فصل؛ دليل سياسة قابلة للتطبيق بالكامل غير كافٍ.",
        "- الهدف هو جميع تسجيلات الـRoster V2 المحتفظ بها، وليس جميع تسجيلات الجامعة. النسب التراكمية في student_history مبنية على محاولات نافذة الـRoster؛ ليست سجل حياة كاملًا أو مواد فريدة.",
        "- التاريخ السابق استكمل من R/E الخام لنفس الطلاب، عبر الاختصاصات، وبشرط part<T. لا يعني NEVER_TAKEN أكثر من عدم وجود محاولة في السجل القابل للرصد. توجد تواريخ أقدم/مفاتيح ناقصة خارج السجل؛ لا نفترض اكتماله.",
        "- الفصول الخام القديمة ذات الرقم الأخير 4 خارج عقد YYYY{1,2,3} الحالي. استبعدت من التحليل الأساسي مع توثيقها؛ قياس حساسيتها باعتبار ترتيبها الرقمي فقط محفوظ في `nonstandard_part_policy_sensitivity.json` و`nonstandard_part_sensitivity_summary.csv`، ولا يثبت معناها التقويمي.",
        "- البيانات لقطة نهائية؛ لا توجد تواريخ إعلان/تعديل نتائج تثبت أن كل نتيجة سابقة كانت قد اعتمدت قبل بداية T. منع تسرب part مثبت، لكن معرفة زمن النشر الدقيقة غير مثبتة.",
        "- انتقال الاختصاص وتغير ساعات المادة موثقان في ملفات الفحص. مقام available ساعات آخر محاولة سابقة، والبسط ساعات التسجيل الحالي؛ لذلك قد تتجاوز نسبة استهلاك الرصيد 1 دون تكرار صفوف، ولا تقص هذه النسب.",
        "- الفصل ذو الرقم الأخير 3 مفصول، لكن وصفه صيفيًا غير مثبت من تقويم جامعي. 20253 يحتوي نتائج كثيرة غير مكتملة؛ لا تستخدم نتيجة T لتصنيف تاريخ T، ولا تفسر نتيجته أكاديميًا هنا.",
        "- previously_attempted في الطلب = Failed+Withdrawn فقط؛ إعادة مواد ناجحة أو OTHER محفوظة في other_previous. لذلك هذه النسبة مع new لا تجمع دائمًا إلى 1؛ الأقسام الأربعة تجمع إلى الحمل الكامل.",
        "- الطلاب يتكررون عبر الفصول، وبعضهم خارج السياسة المستقبلية أو اختصاصات مختلفة. النسب وصفية موزونة بالفصل، وليست آثارًا سببية أو ضمان تحسن المعدل/التخرج. يلزم اختبار سياسات مستقل ثم تقييم زمني بعد تثبيتها؛ لا تسم هذه البيانات holdout غير مستخدم لاحقًا.",
        "", "## Reproduction and preserved artifacts", "",
        "```powershell", f'.\\.venv\\Scripts\\python.exe -m src.diagnostics.analyze_repeat_withdrawal_balance --output-dir reports/repeat_withdrawal_analysis_NEW --graph "{metadata["graph_path"]}"', "```", "",
        "التشغيل يرفض مجلد نتائج موجودًا. جميع CSV الكبيرة التي تحتوي معرفات طلاب محلية ومستبعدة من Git بواسطة .gitignore داخل مجلد التقرير.",
        f"الخريطة المستخدمة: `{metadata['graph_path']}`؛ نتائج التنقل ومواضع المصدر في `graph_navigation.json`. مصادر البيانات وأعداد المصالحة في `analysis_metadata.json`.",
        "بصمات SHA-256 قبل/بعد لجميع الملفات الموجودة في data وmodels وsrc والـParquet الجذرية موثقة في `protected_before_sha256.json` و`protected_after_sha256.json`، مع نتيجة المقارنة في `artifact_integrity.json`.",
        "التحقق المستقل بطريقة merge_asof على جميع التسجيلات في `independent_verification.json`، ونتائج الاختبارات وتحديث الخريطة المحلي في `verification.md`.",
    ]
    (output / "summary.md").write_text("\n".join(lines), encoding="utf-8")
