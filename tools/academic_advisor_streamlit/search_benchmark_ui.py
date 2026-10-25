"""Offline search benchmark controls in the existing Streamlit console.

Only explicit Run/Resume buttons start work. Preview, progress and saved-result
reads do not score plans; the benchmark service owns execution and persistence.
"""
from __future__ import annotations

from collections.abc import Mapping
import math

import streamlit as st


SCOPE_LABELS = {
    "FIXED_POOL": "Fixed 2000-plan universe",
    "FULL_SPACE": "Full feasible-space search",
    "EXHAUSTIVE": "Exhaustive Oracle",
}
BUSY_STATUSES = {"PENDING", "QUEUED", "RUNNING"}
COMPLETE_STATUSES = {"COMPLETE", "COMPLETED"}


@st.cache_resource(max_entries=1, show_spinner=False)
def get_search_service():
    """Import the bounded offline worker only when this section is selected."""
    from tools.recommendation_pilot_20251.search_benchmark import SearchBenchmarkService
    return SearchBenchmarkService()


def _finite(value):
    try:
        return value is not None and math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _value(value, reason="SAVED_VALUE_UNAVAILABLE"):
    if value is None or isinstance(value, float) and not math.isfinite(value):
        return "N/A — " + str(reason or "SAVED_VALUE_UNAVAILABLE")
    return value


def _table(rows):
    if rows:
        st.dataframe([{key: _value(value, row.get(key + "_reason") or row.get("reason"))
                       for key, value in row.items() if not isinstance(value, (Mapping, list, tuple))}
                      for row in rows], hide_index=True, use_container_width=True)
    else:
        st.caption("N/A — NO_SAVED_ROWS")


def _progress(service, run_id):
    progress = service.progress(run_id) if run_id else None
    if progress:
        st.caption(f"Run: {run_id} | status: {progress.get('status', 'N/A')} | "
                   f"completed: {progress.get('completed', 0)}/{progress.get('total', 0)} | "
                   f"student: {progress.get('current_sample', progress.get('running', 'N/A'))}")
        total = progress.get("total") or 1
        st.progress(min(1.0, max(0.0, (progress.get("completed") or 0) / total)))
        details = progress.get("details")
        if details:
            with st.expander("تفاصيل تقدم التشغيل"):
                if isinstance(details, list):
                    _table(details)
                else:
                    st.json(details)
        status = str(progress.get("status", "")).upper()
        if status in {"FAILED", "EXHAUSTIVE_INCOMPLETE", "PARTIAL", "INTERRUPTED"}:
            st.warning(f"{status} — {progress.get('reason') or progress.get('error') or 'راجع تفاصيل التشغيل'}")
        st.button("تحديث تقدم Search Benchmark", key="search_benchmark_refresh")
    return progress


def _render_saved(service, run_id):
    """Present persisted scores and details without recomputing inference."""
    saved = service.load_run(run_id)
    manifest = saved.get("run_manifest") or {}
    students = saved.get("student_results") or []
    st.caption(f"Saved Run: {run_id} | snapshot: {manifest.get('snapshot_id', 'N/A')}")
    experiments = [(student, experiment) for student in students
                   for experiment in student.get("experiments", [])]
    rows = []
    for student, experiment in experiments:
        diversity = experiment.get("diversity") or {}
        rows.append({
            "Student": student.get("sample_id"), "Model": experiment.get("model"),
            "Strategy": experiment.get("strategy"), "Budget": experiment.get("budget"),
            "Target Credits": experiment.get("target_credits"),
            "Evaluated Plans": experiment.get("evaluated_plans"), "Best GPA": experiment.get("best_gpa"),
            "Oracle GPA": _value(experiment.get("oracle_gpa"), "COMPLETED_ORACLE_UNAVAILABLE"),
            "GPA Gap": _value(experiment.get("gpa_gap"), "COMPLETED_ORACLE_UNAVAILABLE"),
            "Top-3 Recall": _value(experiment.get("top3_recall"), "COMPLETED_ORACLE_UNAVAILABLE"),
            "Diversity": diversity.get("mean_jaccard") if isinstance(diversity, Mapping) else diversity,
            "Runtime": experiment.get("standalone_runtime_seconds", experiment.get("runtime_seconds")),
            "Status": experiment.get("status", student.get("status")), "Scope": experiment.get("scope"),
        })
    st.caption("Best GPA هو expected semester-plan GPA وفق ترتيب Pilot. Diversity يعرض mean Jaccard؛ الأعلى يعني تشابهًا أكبر.")
    st.caption("Runtime بالثواني يستخدم standalone_runtime_seconds عند توفره: يحتسب تحضير السياق المشترك مرة واحدة تحفظياً لكل صف. "
               "لا تجمع قيم الصفوف بين B/C أو السيناريوهات التي تتشارك الخطط والتحضير؛ زمن التشغيل الكلي محفوظ في manifest.")
    _table(rows)
    statuses = [manifest.get("status")] + [row.get("status") for row in students] + [row.get("status") for _, row in experiments]
    if any(str(status).upper() == "EXHAUSTIVE_INCOMPLETE" for status in statuses):
        st.warning("EXHAUSTIVE_INCOMPLETE — أفضل نتيجة ضمن الخطط المفحوصة فقط؛ لم يكتمل إثبات الأفضلية في كامل الفضاء.")
    for student in students:
        if student.get("reason"):
            st.warning(f"{student.get('sample_id')}: {student.get('status')} — {student['reason']}")
    if experiments:
        options = list(range(len(experiments)))
        selected = st.selectbox("الخطط الثلاث لتجربة محفوظة", options,
            format_func=lambda index: " | ".join(str(value) for value in (
                experiments[index][0].get("sample_id"), experiments[index][1].get("model"),
                experiments[index][1].get("strategy"), experiments[index][1].get("budget"),
                experiments[index][1].get("scope"))), key="search_benchmark_saved_experiment")
        student, experiment = experiments[selected]
        if experiment.get("reason"):
            st.warning(str(experiment["status"]) + " — " + str(experiment["reason"]))
        plans = experiment.get("top_plans") or []
        if not plans:
            st.caption("N/A — NO_MATCHING_PLAN_OR_SAVED_TOP_PLANS")
        for rank, plan in enumerate(plans[:3], 1):
            with st.expander(f"Top {rank} | {plan.get('canonical_id', 'N/A')} | expected GPA: {plan.get('expected_plan_gpa', 'N/A')}"):
                _table([plan])
                balance = plan.get("plan_difficulty_balance") or {}
                if balance:
                    _table([balance])
                _table(plan.get("courses") or plan.get("course_rows") or [])
    with st.expander("تشخيص التشغيل المحفوظ — manifest / coverage / timings"):
        st.json(manifest)
        for student, experiment in experiments:
            st.caption(f"{student.get('sample_id')} | {experiment.get('model')} | {experiment.get('strategy')}")
            st.json({key: value for key, value in experiment.items() if key != "top_plans"})


def render_search_benchmark():
    """Render local controls; every expensive execution requires a button click."""
    st.subheader("🔎 Search Benchmark")
    st.info("after_backend_fix — تجربة محلية على البيانات المحفوظة فقط. Before أرشيف معزول؛ لا تشغيل Search Benchmark عليه.")
    st.caption("Fixed Pool يقيس الاختيار داخل أول 2000 خطة فقط. Full Space يبحث الفضاء الضمني. Oracle يثبت أفضل توقع للمودل عند اكتماله، وليس نتيجة الطالب الفعلية.")
    try:
        service = get_search_service()
        students = [str(row["sample_id"]) for row in service.cohort() if row.get("role", "primary") == "primary"]
        if not students:
            st.error("العينة الأساسية المحفوظة غير متاحة.")
            return
        selected = st.selectbox("طالب Search Benchmark", students, key="search_benchmark_student")
        previews = service.inspect([selected])
        preview = previews[0] if previews else {}
        resolution = preview.get("target_resolution") or {}
        automatic = resolution.get("target_credits")
        minimum, maximum = resolution.get("minimum_credits"), resolution.get("maximum_credits")
        resolved = _finite(automatic) and float(automatic) > 0
        c1, c2, c3 = st.columns(3)
        c1.metric("Automatic Target Credits · API", f"{float(automatic):g}" if resolved else "UNRESOLVED")
        c2.metric("API Minimum Credits", f"{float(minimum):g}" if _finite(minimum) else "UNRESOLVED")
        c3.metric("API Maximum Credits", f"{float(maximum):g}" if _finite(maximum) else "UNRESOLVED")
        st.caption(f"target_credits_source: {resolution.get('target_credits_source', 'UNRESOLVED')} | "
                   f"Candidates: {preview.get('candidate_count', 'N/A')} | Feasible plans: {preview.get('feasible_plan_count', 'N/A')} | "
                   f"Previous GPA: {preview.get('previous_gpa', 'N/A')}")
        if resolution.get("reason") or preview.get("reason"):
            st.warning(str(resolution.get("reason") or preview.get("reason")))
        diagnostic = st.checkbox("تفعيل هدف يدوي تشخيصي لهذا الطالب", key=f"search_benchmark_override_{selected}")
        manual = None
        valid_target = resolved
        if diagnostic:
            st.warning("MANUAL DIAGNOSTIC EXPERIMENT — الهدف اليدوي منفصل عن الهدف التلقائي ولا يتجاوز حدود API الصريحة.")
            manual = st.number_input("Diagnostic exact target credits", min_value=0.5,
                value=float(automatic) if resolved else None, step=0.5, key=f"search_benchmark_manual_{selected}")
            valid_target = _finite(manual) and float(manual) > 0
            if valid_target and (_finite(maximum) and manual > float(maximum) or _finite(minimum) and manual < float(minimum)):
                valid_target = False
                st.warning("MANUAL_TARGET_OUTSIDE_API_BOUNDS")
        batch = st.checkbox("اختيار مجموعة صغيرة صراحةً (حتى 5 طلاب)", key="search_benchmark_batch_enabled")
        sample_ids = [selected]
        if batch:
            sample_ids = st.multiselect("طلاب المجموعة — الهدف يحسب لكل طالب من API", students,
                default=[selected], max_selections=5, key="search_benchmark_batch_students")
            if diagnostic:
                st.warning("الهدف اليدوي التشخيصي لطالب واحد فقط؛ ألغِ المجموعة أو الهدف اليدوي.")
        models = st.multiselect("Search Models", ["B", "C"], default=["B", "C"], key="search_benchmark_models")
        strategies = st.multiselect("Search Strategies", ["FIRST_N", "DIVERSE_N", "SMART_SEARCH"],
            default=["FIRST_N", "DIVERSE_N", "SMART_SEARCH"], key="search_benchmark_strategies")
        budgets = st.multiselect("Full-plan evaluation budgets", [200, 1000, 2000],
            default=[200, 1000, 2000], key="search_benchmark_budgets")
        scopes = st.multiselect("Experiment scopes", list(SCOPE_LABELS), default=["FIXED_POOL", "FULL_SPACE"],
            format_func=lambda value: SCOPE_LABELS[value], key="search_benchmark_scopes")
        seed = st.number_input("Random seed", min_value=0, value=42, step=1, key="search_benchmark_seed")
        if "EXHAUSTIVE" in scopes:
            st.warning("Exhaustive Oracle اختيار صريح: قد يتوقف بأمان عند الحدود ويُحفظ EXHAUSTIVE_INCOMPLETE. ابدأ بعينة صغيرة.")
        with st.expander("حدود الموارد — checkpoint / resume"):
            limits = {
                "max_seconds": st.number_input("Maximum wall-clock seconds", min_value=1, value=300, key="search_benchmark_seconds"),
                "max_oracle_plans": st.number_input("Maximum oracle plans per model", min_value=1, value=50000, key="search_benchmark_oracle_plans"),
                "chunk_size": st.number_input("Scoring chunk size", min_value=1, max_value=512, value=128, key="search_benchmark_chunk"),
                "max_space_states": st.number_input("Maximum search states", min_value=1, value=2000000, key="search_benchmark_states"),
                "max_disk_mb": st.number_input("Maximum run disk MB", min_value=1, value=512, key="search_benchmark_disk"),
            }
        active_id = st.session_state.get("search_benchmark_active_run_id")
        progress = service.progress(active_id) if active_id else None
        busy = bool(progress and str(progress.get("status", "")).upper() in BUSY_STATUSES)
        valid = (bool(models and scopes and sample_ids) and valid_target and len(sample_ids) <= 5
                 and not (batch and diagnostic) and (scopes == ["EXHAUSTIVE"] or bool(strategies and budgets)))
        if st.button("تشغيل Search Benchmark", type="primary", key="search_benchmark_run", disabled=busy or not valid):
            active_id = service.start(sample_ids, models=models, strategies=strategies, budgets=budgets,
                scopes=scopes, seed=int(seed), manual_target=manual, diagnostic_override=diagnostic, limits=limits)
            st.session_state["search_benchmark_active_run_id"] = active_id
            st.session_state.pop("search_benchmark_loaded_run_id", None)
        progress = _progress(service, active_id)
        if active_id and progress and str(progress.get("status", "")).upper() in COMPLETE_STATUSES:
            st.session_state.setdefault("search_benchmark_loaded_run_id", active_id)
        st.divider()
        st.subheader("نتائج Search Benchmark المحفوظة")
        runs = service.list_runs()
        run_lookup = {row["run_id"]: row for row in runs}
        if runs:
            saved_id = st.selectbox("تشغيل Search Benchmark محفوظ", list(run_lookup),
                format_func=lambda rid: f"{rid} | {run_lookup[rid].get('status', 'N/A')} | {run_lookup[rid].get('created_at', 'N/A')}",
                key="search_benchmark_saved_run")
            load, resume = st.columns(2)
            if load.button("تحميل Search Benchmark محفوظ", key="search_benchmark_load"):
                st.session_state["search_benchmark_loaded_run_id"] = saved_id
            saved_status = str(run_lookup[saved_id].get("status", "")).upper()
            if resume.button("استئناف التشغيل غير المكتمل", key="search_benchmark_resume",
                             disabled=busy or saved_status in COMPLETE_STATUSES | BUSY_STATUSES):
                active_id = service.start([], resume_run_id=saved_id, limits=limits)
                st.session_state["search_benchmark_active_run_id"] = active_id
                st.session_state.pop("search_benchmark_loaded_run_id", None)
                st.rerun()
        else:
            st.caption("لا توجد تشغيلات Search Benchmark محفوظة.")
        loaded_id = st.session_state.get("search_benchmark_loaded_run_id")
        if loaded_id:
            _render_saved(service, loaded_id)
    except (OSError, ValueError, RuntimeError, ImportError) as exc:
        st.error(str(exc))
