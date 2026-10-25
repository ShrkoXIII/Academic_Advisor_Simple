"""Offline Pilot presentation for the existing Streamlit console.

Only identifiers and widget scalars survive rerenders. Saved projections, actual
outcomes, models and job state remain owned by PilotService.
"""
from __future__ import annotations

from collections.abc import Mapping
import math

import streamlit as st


MODEL_LABELS = {"A": "A — Historical Baseline / Diagnostic Only", "B": "B", "C": "C"}
SNAPSHOTS = ["after_backend_fix", "before_backend_fix"]


@st.cache_resource(max_entries=1, show_spinner=False)
def get_pilot_service():
    """Keep one bounded worker/model resource across Streamlit rerenders."""
    from pilot_service import PilotService
    return PilotService()


def _number(value, reason=None):
    if value is None or isinstance(value, float) and not math.isfinite(value):
        return "N/A" + (f" — {reason}" if reason else "")
    return f"{value:.3f}" if isinstance(value, (float, int)) and not isinstance(value, bool) else str(value)


def _table(rows):
    """Missing saved fields are visible; never infer, impute or recompute them."""
    if rows:
        display = []
        for row in rows:
            display.append({key: _number(value, row.get(key + "_reason") or row.get("reason") or "SAVED_VALUE_UNAVAILABLE")
                if value is None else f"{value:.1%}" if key.endswith("overlap_fraction") and isinstance(value, (float, int))
                else value for key, value in row.items()
                if not isinstance(value, (dict, list, tuple))})
        st.dataframe(display, hide_index=True, use_container_width=True)
    else:
        st.caption("N/A — لا توجد بيانات محفوظة لهذا القسم.")


def _student_summary(summary):
    if isinstance(summary, Mapping):
        _table([{"الحقل": key, "القيمة": _number(value, summary.get(key + "_reason"))}
                for key, value in summary.items()
                if not isinstance(value, (dict, list, tuple))])
    else:
        st.caption("N/A — STUDENT_SUMMARY_UNAVAILABLE")


def _render_presentation(presentation):
    st.subheader("ملخص الطالب والمودلات")
    st.caption(f"{presentation.get('sample_id', '')} | snapshot: {presentation.get('snapshot_id', 'N/A')}")
    _student_summary(presentation.get("student_summary"))
    summary_rows = presentation.get("summary_rows") or []
    if summary_rows:
        for column, row in zip(st.columns(len(summary_rows)), summary_rows):
            model = row.get("model", "N/A")
            with column:
                st.markdown("**" + MODEL_LABELS.get(model, str(model)) + " · ملخص التوصية**")
                st.metric(f"{model} · أفضل معدل خطة بديلة", _number(row.get("best_predicted_plan_gpa"),
                    row.get("best_predicted_plan_gpa_reason") or row.get("reason") or "SAVED_VALUE_UNAVAILABLE"))
                st.metric(f"{model} · الخطط المفحوصة", _number(row.get("evaluated_plans"),
                    row.get("evaluated_plans_reason") or row.get("reason") or "SAVED_VALUE_UNAVAILABLE"))
                st.caption(f"status: {row.get('status', 'N/A')} | reason: {row.get('reason') or 'N/A'}")
    st.caption("معدل الخطة الموصى بها هو توقع للخطة المرشحة؛ توقع الخطة الفعلية يقاس على مواد الطالب الفعلية. المعدل الفعلي الوصفي مشتق من النتائج المحفوظة المتاحة.")
    _table(summary_rows)
    actual = presentation.get("actual_summary") or {}
    model_metrics = actual.get("models") or {}
    search = presentation.get("search") or {}
    st.caption("حالة البحث المحفوظة: عدد الحالات، ميزانية البحث وحدود القطع. الخطة الأولى هي الأفضل ضمن الخطط المفحوصة المحفوظة؛ لا يثبت البحث المحدود أفضلية عالمية.")
    _table([search] if search else [])
    if search.get("search_budget_exhausted") or search.get("truncated") or search.get("search_truncated"):
        st.warning("البحث مقطوع / الميزانية مستنفدة — نتائج PROVISIONAL ضمن الجزء المفحوص فقط.")
    for model, plans in (presentation.get("plans_by_model") or {}).items():
        st.markdown("**" + MODEL_LABELS.get(model, str(model)) + " · أفضل 3 خطط بالترتيب المحفوظ**")
        st.caption("كل خطة سياق بديل مستقل؛ لا تجمع التوقعات بين البدائل ولا تعاملها كخطة واحدة. التطابق يعرض كنسبة من مواد الخطة الفعلية.")
        if not plans:
            st.caption("N/A — NO_MATCHING_PLAN_OR_SAVED_PLANS")
        for position, plan in enumerate(plans[:3], 1):
            # Position preserves the engine's saved order, independently of rank labels.
            gpa = plan.get("expected_plan_gpa", plan.get("predicted_gpa", plan.get("plan_gpa", plan.get("predicted_term_gpa"))))
            with st.expander(f"{model} · الخطة {position} · معدل متوقع {_number(gpa)}", expanded=False):
                plan_row = {key: value for key, value in plan.items() if key != "course_rows"}
                balance = plan.get("plan_difficulty_balance") or {}
                plan_row["max_fail_probability"] = balance.get("max_fail_probability", plan.get("max_fail_probability"))
                _table([plan_row])
                course_rows = []
                for course in plan.get("course_rows", []):
                    row = dict(course)
                    if row.get("is_actual_course") is not True:
                        row["actual_mark"] = None
                        row["actual_mark_reason"] = "NOT_A_MATCHING_ACTUAL_COURSE"
                    course_rows.append(row)
                st.caption("تفاصيل المواد: العلامة المتوقعة، النقاط، احتمال الرسوب، التطابق مع الفعلي؛ العلامة الفعلية تعرض فقط للمادة المتطابقة الصالحة.")
                _table(course_rows)

    st.subheader("مقارنة توقعات المودل مع نتائج الطالب الفعلية")
    st.caption("الخطة الفعلية كاملة حسب البيانات المحفوظة، بما فيها المواد غير المتنبأ بها. error = predicted − actual؛ MAE/RMSE/Bias تستخدم الأزواج الصالحة فقط.")
    c1, c2, c3 = st.columns(3)
    c1.metric("المعدل الفعلي الوصفي", _number(actual.get("descriptive_gpa")))
    c2.metric("مواد ذات نتيجة / جميع المواد", f"{actual.get('graded_course_count', 'N/A')} / {actual.get('actual_course_count', 'N/A')}")
    c3.metric("المعدل الرسمي", _number(actual.get("official_gpa")))
    for field in ("descriptive_gpa", "partial_graded_gpa", "official_gpa"):
        if actual.get(field + "_reason"):
            st.caption(f"{field}: {_number(actual.get(field), actual[field + '_reason'])}")
    if model_metrics:
        for column, (model, metrics) in zip(st.columns(len(model_metrics)), model_metrics.items()):
            with column:
                st.markdown("**" + MODEL_LABELS.get(model, str(model)) + " · توقع الخطة الفعلية**")
                st.metric(f"{model} · معدل الخطة الفعلية المتوقع", _number(metrics.get("predicted_actual_plan_gpa"), metrics.get("reason")))
                for key, label in (("mae", "MAE"), ("rmse", "RMSE"), ("bias", "Bias")):
                    st.metric(f"{model} · {label}", _number(metrics.get(key), metrics.get("reason")))
                if metrics.get("status") or metrics.get("reason"):
                    st.caption(f"status: {metrics.get('status', 'N/A')} | reason: {metrics.get('reason') or 'N/A'}")
        _table([{"model": model, **metrics} for model, metrics in model_metrics.items()])
    if not model_metrics:
        st.caption("N/A — SAVED_ACTUAL_PLAN_PREDICTIONS_UNAVAILABLE")
    _table(presentation.get("actual_course_rows", []))

    st.subheader("أزمنة التنفيذ ومصدر القياس")
    st.caption("الثواني أدناه قياسات المراحل المحفوظة فقط. cache/hit تعني إعادة استخدام نتيجة؛ لا نجمع مراحل متداخلة ولا ننسب زمن التشغيل الأصلي إلى تحميل نتيجة مخبأة.")
    execution = presentation.get("execution") or {}
    st.metric("زمن التنفيذ الكلي المحفوظ — ثانية", _number(execution.get("total_wall_seconds"), execution.get("total_wall_seconds_reason")))
    st.caption(f"result_source: {execution.get('result_source', 'N/A')} | presentation_load_cache_status: {execution.get('presentation_load_cache_status', 'N/A')} | observed_prediction_cache_status: {execution.get('observed_prediction_cache_status', 'N/A')} | provenance: {execution.get('provenance', 'N/A')}")
    _table(presentation.get("timing_rows", []))
    for warning in presentation.get("warnings", []):
        st.warning(str(warning))


def _render_saved(service, run_id, family):
    saved = service.load_run(run_id, family=family)
    manifest = saved.get("run_manifest", {})
    results = saved.get("student_results", [])
    st.caption(f"Run: {run_id} | {saved.get('snapshot_id', manifest.get('snapshot_id', 'N/A'))} | family: {family} | تحميل محفوظ دون إعادة توقع")
    # One compact row per student; expand only the chosen student's top-three projection.
    rows = []
    for result in results:
        row = {"sample_id": result.get("sample_id"), "candidate_mode": result.get("candidate_mode"),
               "target_credits": result.get("target_credits"), "target_credits_source": result.get("target_credits_source"),
               "credit_experiment": result.get("credit_experiment"), "status": result.get("status", "N/A"),
               "reason": result.get("reason")}
        for model, experiment in (result.get("experiments") or {}).items():
            plans = experiment.get("analytical_plans", experiment.get("plans")) or []
            row[model + "_status"] = experiment.get("status", experiment.get("prediction_status", "N/A"))
            row[model + "_best_predicted_plan_gpa"] = plans[0].get("expected_plan_gpa") if plans else None
        rows.append(row)
    st.subheader("ملخص الطلاب وحالة كل سيناريو محفوظ")
    _table(rows)
    samples = list(dict.fromkeys(str(row["sample_id"]) for row in results if row.get("sample_id")))
    if not samples:
        samples = [str(v) for v in manifest.get("sample_ids", [])]
    if not samples:
        st.caption("N/A — NO_SAVED_STUDENT_RESULTS")
        return
    selected = st.selectbox("تفاصيل طالب من التشغيل المحفوظ", samples, key="pilot_compare_saved_student")
    matching = [row for row in results if str(row.get("sample_id")) == selected]
    if len(matching) > 1:
        scenarios = list(dict.fromkeys((row.get("candidate_mode"), row.get("credit_experiment")) for row in matching))
        scenario = st.selectbox("سياق السيناريو المحفوظ — candidate_mode / credit_experiment", scenarios,
            format_func=lambda value: f"{value[0] or 'N/A'} / {value[1] or 'N/A'}", key="pilot_compare_saved_scenario")
        _render_presentation(service.presentation(saved, selected, scenario=scenario))
    else:
        _render_presentation(service.presentation(saved, selected))


def render_pilot():
    """Render local saved-data controls; starts happen only on explicit buttons."""
    st.subheader("Pilot 20251 — Model Comparison")
    st.info("تشغيل محلي على الاستجابات المحفوظة: لا اتصال بالجامعة. جمع Courses يتم من تبويب جمع وحفظ بيانات التجربة.")
    st.warning("النتائج PROVISIONAL: البحث المحدود يعرض prefix حتمياً ولا يثبت أفضل خطة عالمياً. دقة توقع الخطة الفعلية وجودة التوصية والسياسة الأكاديمية مقاييس منفصلة.")
    try:
        service = get_pilot_service()
        left, right = st.columns(2)
        snapshot = left.selectbox("Snapshot للمقارنة", SNAPSHOTS, key="pilot_compare_snapshot")
        include_reserve = right.checkbox("إظهار طلاب الاحتياط أيضاً", value=False, key="pilot_compare_reserve")
        readonly = snapshot == "before_backend_fix"
        if readonly:
            st.info("before_backend_fix — أرشيف للقراءة فقط؛ تصفح النتائج المحفوظة أدناه. التشغيل الجديد متاح في After فقط.")
        cohort = service.cohort(include_reserve=include_reserve)
        complete = service.completeness(snapshot_id=snapshot, include_reserve=include_reserve)
        primary = [str(row["sample_id"]) for row in cohort if row.get("role") == "primary"]
        c1, c2, c3 = st.columns(3)
        count = len(cohort)
        c1.metric("Student المحفوظ", f"{complete.get('student_saved', 0)}/{count}")
        c2.metric("Courses المحفوظة", f"{complete.get('courses_saved', 0)}/{count}")
        c3.metric("Frozen History المحفوظ", f"{complete.get('history_saved', 0)}/{complete.get('history_total', 0)}")
        if complete.get('history_status'):
            st.caption(f"Frozen History: {complete['history_status']} | usable_for_b_c: {complete.get('history_usable_for_b_c', 'N/A')}. جودة الصفوف تخضع لمسار Pilot الحالي وعزل الصفوف غير الصالحة.")
        ready = set(map(str, complete.get("ready_sample_ids", [])))
        blocked = complete.get("blocked", [])
        if blocked:
            st.warning("البيانات غير مكتملة. اجمع Courses الناقصة من تبويب الجمع؛ لا يجري جلبها أو تعويضها هنا.")
            with st.expander("تفاصيل Student / Courses / History والحظر"):
                _table(blocked)
        students = [str(row["sample_id"]) for row in cohort]
        if not students:
            st.error("العينة المحفوظة غير متاحة.")
            return
        selected = st.selectbox("طالب من العينة الأساسية الـ30", students, key="pilot_compare_student")
        resolution = {}
        if not readonly:
            with st.expander("معاينة الطالب المحفوظة قبل التشغيل"):
                try:
                    preview = service.preview(selected, snapshot_id=snapshot)
                    resolution = preview.get('credit_target_resolution') or {}
                    _student_summary(preview.get("student_summary", preview))
                    if preview.get("reason"):
                        st.caption(str(preview["reason"]))
                except (OSError, ValueError, RuntimeError) as exc:
                    st.caption("N/A — " + str(exc))
        models = st.multiselect("النماذج", ["A", "B", "C"], default=["B", "C"],
                               format_func=lambda model: MODEL_LABELS[model], key="pilot_compare_models")
        c1, c2 = st.columns(2)
        minimum, maximum = resolution.get('minimum_credits'), resolution.get('maximum_credits')
        automatic = resolution.get('target_credits')
        st.caption(f"API | الحد الأدنى: {_number(minimum)} | الحد الأقصى: {_number(maximum)} | الهدف الدقيق: {_number(automatic)}")
        manual = c1.checkbox('تفعيل هدف يدوي تشخيصي لهذا الطالب', value=False,
            key=f'pilot_compare_manual_enabled_{snapshot}_{selected}', disabled=readonly)
        credits = None
        valid_credits = resolution.get('status') == 'RESOLVED'
        if manual:
            st.warning('MANUAL_DIAGNOSTIC — تجربة يدوية مستقلة؛ لا تتجاوز حدود API المعروفة. التشغيل لطالب واحد فقط.')
            if minimum is not None and maximum is not None and minimum > maximum:
                valid_credits = False
                st.error('CONFLICTING_CREDIT_LIMITS')
            else:
                lower = max(float(minimum or 0), 0.5)
                upper = float(maximum) if maximum is not None else max(36., lower)
                if upper < lower:
                    valid_credits = False
                else:
                    initial = max(lower, min(float(automatic or maximum or lower), upper))
                    credits = c1.number_input('الهدف اليدوي الدقيق — MANUAL_DIAGNOSTIC',
                        min_value=lower, max_value=upper, value=initial, step=0.5,
                        key=f'pilot_compare_credits_{snapshot}_{selected}')
                    valid_credits = math.isfinite(credits) and 0 < credits <= 36
        elif not valid_credits and not readonly:
            st.error('تعذر تحديد الهدف تلقائياً: ' + str(resolution.get('reason') or 'CREDIT_TARGET_UNRESOLVED'))
        max_plans = c2.selectbox("الحد الأقصى للخطط", [200, 1000, 2000], key="pilot_compare_max_plans")
        active_id = st.session_state.get("pilot_compare_active_run_id")
        progress = service.progress(active_id) if active_id else None
        busy = bool(progress and progress.get("status") in {"pending", "queued", "running"})
        disabled = readonly or not models or busy or not valid_credits
        one, batch = st.columns(2)
        manual_ready = manual and any(r.get('sample_id') == selected and r.get('field') == 'credit_target'
                                     for r in complete.get('records', []))
        run_one = one.button("تشغيل مقارنة النماذج", key="pilot_compare_one", type="primary",
                             disabled=disabled or not (selected in ready or manual_ready))
        run_batch = batch.button("تشغيل مقارنة كامل العينة الأساسية (30)", key="pilot_compare_batch",
                                  disabled=disabled or manual or len(primary) != 30 or not set(primary).issubset(ready))
        subset = [sample for sample in primary if sample in ready]
        run_subset = False
        if 0 < len(subset) < len(primary):
            run_subset = st.button(f"تشغيل المجموعة الصالحة فقط ({len(subset)}/{len(primary)})", key="pilot_compare_subset", disabled=disabled or manual)
        if run_one or run_batch or run_subset:
            ids = [selected] if run_one else primary if run_batch else subset
            manual_args = {'diagnostic_override': True} if manual else {}
            active_id = service.start(ids, models=models, snapshot_id=snapshot,
                target_credits=credits, max_plans=max_plans, include_reserve=include_reserve, **manual_args)
            st.session_state["pilot_compare_active_run_id"] = active_id
            st.session_state.pop("pilot_compare_loaded_run_id", None)
            st.session_state["pilot_compare_loaded_family"] = "comparison"
            progress = service.progress(active_id)
        if active_id and progress:
            st.caption(f"Run: {active_id} | status: {progress.get('status', 'N/A')} | completed: {progress.get('completed', 0)}/{progress.get('total', 0)}")
            total = progress.get("total", 0) or 1
            st.progress(min(1.0, max(0.0, progress.get("completed", 0) / total)))
            _table(progress.get("sample_statuses", []))
            st.button("تحديث تقدم التشغيل", key="pilot_compare_refresh")
            if progress.get("status") == "failed":
                st.error("فشل التشغيل: " + str(progress.get("error") or progress.get("reason") or "RUN_FAILED"))
            elif progress.get("status") == "partial":
                st.warning("التشغيل جزئي؛ راجع حالة كل طالب وأسباب عدم الاكتمال.")
            if progress.get("status") in {"completed", "complete"} and not st.session_state.get("pilot_compare_loaded_run_id"):
                st.session_state["pilot_compare_loaded_run_id"] = active_id
                st.session_state["pilot_compare_loaded_family"] = "comparison"

        st.divider()
        st.subheader("تصفح النتائج المحفوظة")
        runs = service.list_runs()
        run_lookup = {row["run_id"]: row for row in runs}
        if runs:
            saved_id = st.selectbox("التشغيل المحفوظ — snapshot / family", list(run_lookup),
                format_func=lambda rid: f"{rid} | {run_lookup[rid].get('snapshot_id', 'N/A')} | {run_lookup[rid].get('family', 'comparison')}",
                key="pilot_compare_saved_run")
            if st.button("تحميل نتيجة محفوظة", key="pilot_compare_load"):
                st.session_state["pilot_compare_loaded_run_id"] = saved_id
                st.session_state["pilot_compare_loaded_family"] = run_lookup[saved_id].get("family", "comparison")
        else:
            st.caption("لا توجد تشغيلات محفوظة.")
        loaded_id = st.session_state.get("pilot_compare_loaded_run_id")
        if loaded_id:
            family = st.session_state.get("pilot_compare_loaded_family", "comparison")
            if family == "actual_candidate_injection":
                st.warning("نتيجة تشخيصية محفوظة — actual_candidate_injection. لا تثبت جودة التوصية ولا تغير إعداد التشغيل العادي.")
            _render_saved(service, loaded_id, family)
    except (OSError, ValueError, RuntimeError) as exc:
        st.error(str(exc))
