"""Local developer playground for the existing Academic Advisor FastAPI endpoints.

Launch from the project root: streamlit run tools/academic_advisor_streamlit/streamlit_app.py
"""
from __future__ import annotations

from decimal import Decimal
import json
from pathlib import Path
import sys
from uuid import uuid4

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from ui_client import (ClientError, Config, HttpClient, encode_json, load_context, make_payloads,
                       previous_academic_part, student_degree_id)
from pilot_collection_store import PilotCollectionStore, CollectionError, history_parts

st.set_page_config(page_title="Academic Advisor · Test Console", page_icon="🎓", layout="wide")


def view_json(value):
    st.json(encode_json(value), expanded=False)


def show_api_status(code: int, response: dict, *, label: str):
    if 200 <= code < 300:
        st.success(f"{label} — HTTP {code}")
    else:
        st.error(f"{label} — HTTP {code}")
    view_json(response)


@st.cache_resource(show_spinner=False)
def config_from_file() -> Config:
    return Config.from_env()


try:
    config = config_from_file()
except ClientError as exc:
    st.title("🎓 Academic Advisor — Test Console")
    st.error(str(exc))
    tab_recommend, tab_history, tab_collection = st.tabs([
        "👨‍🎓 تجربة توصية طالب", "🗂️ تحديث Frozen History", "📥 جمع وحفظ بيانات التجربة",
    ])
    with tab_recommend:
        operating_mode = st.radio(
            "وضع التشغيل", ["Production FastAPI", "Pilot 20251 — Model Comparison"],
            horizontal=True, key="advisor_operating_mode")
        if operating_mode == "Pilot 20251 — Model Comparison":
            from pilot_ui import render_pilot
            render_pilot()
        else:
            st.warning("إعدادات Production غير متاحة؛ صحّح إعدادات الاتصال لإتاحة جلب البيانات والتوصية.")
    with tab_history:
        st.warning("إعدادات الاتصال غير متاحة؛ تحديث Frozen History متوقف حتى تصحيحها.")
    with tab_collection:
        st.warning("إعدادات الاتصال غير متاحة؛ جمع بيانات API متوقف حتى تصحيحها.")
    st.stop()

client = HttpClient(config)
status_placeholders = {}

# Only an observed, valid HTTP response can produce the green check mark.
# Store no secrets or student JSON in this diagnostic state.
def record_connection(name: str, url: str, *, success: bool, detail: str) -> None:
    st.session_state.setdefault("connection_tests", {})[name] = {
        "url": url, "success": success, "detail": detail,
    }
    if name in status_placeholders:
        labels = {"fastapi": "FastAPI", "student": "Student API", "courses": "Courses API",
                  "history": "Frozen History API"}
        status_placeholders[name].write(labels[name] + ": " + connection_label(name, url))


def connection_label(name: str, url: str) -> str:
    if not url:
        return "⚪ غير مضبوط"
    result = st.session_state.get("connection_tests", {}).get(name)
    if result is None or result["url"] != url:
        return "🟡 لم يُختبر"
    return ("✅ " if result["success"] else "❌ ") + result["detail"]


st.title("🎓 Academic Advisor — Test Console")
if config.dev_insecure_tls_host:
    st.warning("⚠️ وضع اختبار مؤقت: التحقق من شهادة HTTPS معطّل لاتصالات الجامعة مع "
               f"{config.dev_insecure_tls_host} فقط. لا تستخدم بيانات اعتماد حساسة على شبكة غير موثوقة. "
               "احذف ADVISOR_UI_DEV_INSECURE_TLS_HOST من .env قبل التشغيل الفعلي.")
st.caption("واجهة محلية للتجربة: لا تغيّر المودل أو قواعد التوصية أو حالة Frozen History من تلقاء نفسها.")
with st.sidebar:
    st.subheader("الاتصالات — نتائج اختبار فعلية")
    for name, label, url in (
        ("fastapi", "FastAPI", config.fastapi_base),
        ("student", "Student API", config.student_url),
        ("courses", "Courses API", config.courses_url),
        ("history", "Frozen History API", config.history_url),
    ):
        status_placeholders[name] = st.empty()
        status_placeholders[name].write(label + ": " + connection_label(name, url))
    st.caption(config.fastapi_base or "لا يوجد رابط FastAPI")
    model_state = st.session_state.get("model_readiness")
    if model_state is None or model_state["url"] != config.fastapi_base:
        st.write("محرك التوصية: 🟡 لم يُفحص")
    else:
        st.write("محرك التوصية: " + ("✅ جاهز" if model_state["ready"] else "❌ غير جاهز"))
    st.caption("🟡 يعني لم نُرسل طلباً فعلياً. ✅ تظهر بعد نجاح الطلب واستلام JSON متوقع فقط.")
    if st.button("فحص اتصال FastAPI", use_container_width=True):
        try:
            code, result = client.health()  # /health is public; no service key needed.
            healthy = code == 200 and result.get("api_health") == "healthy"
            record_connection("fastapi", config.fastapi_base, success=healthy,
                              detail="متصل — /health نجح" if healthy else f"فشل فحص /health — HTTP {code}")
            if healthy:
                st.success("FastAPI يعمل ويستجيب.")
                readiness = result.get("recommendation_readiness", {}).get("ready")
                st.session_state["model_readiness"] = {"url": config.fastapi_base, "ready": readiness is True}
                if readiness is True:
                    st.success("محرك التوصية: جاهز ✅")
                else:
                    st.warning("FastAPI يعمل، لكن محرك التوصية غير جاهز. افحص recommendation_readiness في JSON.")
            else:
                st.session_state.pop("model_readiness", None)
                st.error("الرد لا يطابق Health API المتوقع.")
            view_json(result)
        except ClientError as exc:
            st.session_state.pop("model_readiness", None)
            record_connection("fastapi", config.fastapi_base, success=False, detail=str(exc))
            st.error(str(exc))
    st.caption("تغيير .env يحتاج إعادة تشغيل Streamlit؛ ويمكن أيضاً مسح Cache عندما تتغير الإعدادات.")

tab_recommend, tab_history, tab_collection = st.tabs([
    "👨‍🎓 تجربة توصية طالب", "🗂️ تحديث Frozen History", "📥 جمع وحفظ بيانات التجربة",
])

with tab_recommend:
    operating_mode = st.radio(
        "وضع التشغيل", ["Production FastAPI", "Pilot 20251 — Model Comparison"],
        horizontal=True, key="advisor_operating_mode")
    if operating_mode == "Pilot 20251 — Model Comparison":
        from pilot_ui import render_pilot
        render_pilot()
    else:
        st.info("أدخل معرف الطالب والفصل. سنجلب Student API أولاً، نقرأ degree_id منه، ثم نجلب Courses API. جلب البيانات وحده لا يشغّل المودل.")
        with st.form("student_form"):
            a, b = st.columns(2)
            with a:
                student_id = st.text_input("Student ID", placeholder="27700.111")
            with b:
                term_text = st.text_input("الفصل المطلوب (part_id)", placeholder="20262")
            with st.expander("خيارات التوصية (اختيارية)"):
                exact_credits = st.text_input("ساعات الخطة المطلوبة", value="18")
                top_k = st.number_input("عدد الخطط", min_value=1, max_value=50, value=3, step=1)
                st.caption("سيُحسب history_as_of_part تلقائياً من الفصل السابق وفق التقويم الأكاديمي في مشروعك.")
            fetch_only = st.form_submit_button("1 · جلب وعرض JSON فقط")
            run_recommend = st.form_submit_button("2 · جلب + إرسال طلبَي FastAPI + توصية", type="primary")

        if fetch_only or run_recommend:
            phase = "inputs"
            try:
                sid = student_id.strip()
                if not sid:
                    raise ClientError("أدخل Student ID.")
                term = int(term_text)
                cutoff = previous_academic_part(term)
                if not Decimal(exact_credits).is_finite() or Decimal(exact_credits) <= 0:
                    raise ClientError("ساعات الخطة يجب أن تكون رقماً موجباً.")
                phase = "student"
                with st.spinner("جلب بيانات الطالب من الجامعة..."):
                    student_json = client.student(sid, term)
                    degree_id = student_degree_id(student_json, sid, term)
                record_connection("student", config.student_url, success=True, detail="رد صالح للطالب والفصل")
                phase = "courses"
                with st.spinner("جلب المواد المتاحة من الجامعة..."):
                    courses_json = client.courses(sid, degree_id, term)
                record_connection("courses", config.courses_url, success=True, detail="رد صالح يحتوي المواد وقواعد التسجيل")
                st.session_state["student_raw"] = student_json
                st.session_state["courses_raw"] = courses_json
                st.session_state["identity"] = {"student_id": sid, "degree_id": degree_id, "part_id": term, "history_as_of_part": cutoff}
                st.success(f"تم الجلب. degree_id = {degree_id} | history_as_of_part = {cutoff}")
                if run_recommend:
                    student_context, courses_context = load_context(config)
                    rid = uuid4().hex
                    student_req, courses_req = make_payloads(
                        student_id=sid, degree_id=degree_id, part_id=term, cutoff=cutoff,
                        student_response=student_json, courses_response=courses_json,
                        student_context=student_context, courses_context=courses_context,
                        target_credits=exact_credits, top_k=int(top_k), request_id=rid)
                    st.session_state["request_id"] = rid
                    phase = "fastapi"
                    with st.spinner("إرسال الطلبين إلى FastAPI ثم تشغيل التوصية..."):
                        responses = client.submit_pair(student_req, courses_req)
                    if responses:
                        label, code, response = responses[-1]
                        ok = all(200 <= c < 300 for _, c, _ in responses)
                        record_connection("fastapi", config.fastapi_base, success=ok,
                                          detail="استقبل طلبَي الإدخال" if ok else f"استجاب مع خطأ HTTP {code} ({label})")
                    st.session_state["submit_responses"] = responses
                    st.session_state["student_sent"] = student_req
                    st.session_state["courses_sent"] = courses_req
            except (ClientError, ValueError, ArithmeticError) as exc:
                if phase in {"student", "courses", "fastapi"}:
                    urls = {"student": config.student_url, "courses": config.courses_url,
                            "fastapi": config.fastapi_base}
                    record_connection(phase, urls[phase], success=False, detail=str(exc))
                st.error(str(exc))

        if "identity" in st.session_state:
            with st.expander("هوية الطلب", expanded=False):
                view_json(st.session_state["identity"])
        x, y = st.columns(2)
        with x:
            if "student_raw" in st.session_state:
                with st.expander("Student API — JSON الأصلي", expanded=True):
                    view_json(st.session_state["student_raw"])
        with y:
            if "courses_raw" in st.session_state:
                with st.expander("Courses API — JSON الأصلي", expanded=True):
                    view_json(st.session_state["courses_raw"])

        if "submit_responses" in st.session_state:
            st.subheader("FastAPI responses")
            st.code("request_id = " + st.session_state.get("request_id", ""))
            for label, status, response in st.session_state["submit_responses"]:
                show_api_status(status, response, label=label)
            with st.expander("JSON المرسل إلى FastAPI (للتشخيص فقط)"):
                st.warning("تحتوي هذه البيانات على معلومات طالب؛ استخدم الواجهة محلياً فقط.")
                st.write("Student input")
                view_json(st.session_state.get("student_sent", {}))
                st.write("Courses input")
                view_json(st.session_state.get("courses_sent", {}))

        with st.expander("استعلام عن نتيجة طلب سابق"):
            rid = st.text_input("request_id", value=st.session_state.get("request_id", ""), key="lookup_id")
            if st.button("استعلام عن الحالة"):
                try:
                    if not rid or not all(c.isalnum() or c in "_.-" for c in rid):
                        raise ClientError("request_id غير صالح.")
                    code, data, _ = client.advisor("GET", "/api/v1/recommendation-requests/" + rid)
                    show_api_status(code, data, label="Request status")
                except ClientError as exc:
                    st.error(str(exc))

with tab_history:
    st.info("أدخل رقم الفصل المنتهي فقط لجلب Delta من PHP؛ الجلب والفحص والمعاينة لا يضيفان البيانات تلقائياً. الاعتماد والتفعيل يحتاجان صلاحيات وتأكيداً منفصلين.")
    with st.form("history_form"):
        finished_part = st.text_input("الفصل المُعتمد الذي نريد جلب Delta له", placeholder="20261")
        fetch_delta = st.form_submit_button("جلب Delta + فحص + معاينة", type="primary")
    if fetch_delta:
        phase = "inputs"
        try:
            semester = int(finished_part)
            previous_academic_part(semester)
            phase = "history"
            delta = client.frozen_history(semester)
            record_connection("history", config.history_url, success=True, detail="رد صالح للفصل المحدد")
            phase = "admin"
            st.session_state["history_delta"] = delta
            st.session_state.pop("history_preview", None)
            st.session_state.pop("history_commit", None)
            st.success(f"تم جلب {len(delta['rows'])} مجموعات تاريخية للفصل {semester}.")
            if config.admin_key:
                for label, endpoint in (("validate", "/api/v1/history/deltas/validate"),
                                        ("preview", "/api/v1/admin/history/preview")):
                    code, result, _ = client.advisor("POST", endpoint, data=delta, admin=True)
                    st.session_state["history_" + label] = (code, result)
                    if code >= 400:
                        break
            else:
                st.warning("مفتاح الإدارة غير موجود: تم جلب JSON، لكن لم يُرسل فحص أو معاينة إلى FastAPI.")
        except (ClientError, ValueError) as exc:
            if phase == "history":
                record_connection("history", config.history_url, success=False, detail=str(exc))
            st.error(str(exc))

    if "history_delta" in st.session_state:
        with st.expander("Frozen History Delta — JSON المستلم", expanded=True):
            view_json(st.session_state["history_delta"])
        for label in ("validate", "preview"):
            if "history_" + label in st.session_state:
                code, result = st.session_state["history_" + label]
                with st.expander(f"{label} — FastAPI (HTTP {code})", expanded=(code >= 400)):
                    view_json(result)

        st.divider()
        st.subheader("الاعتماد والتفعيل — خطوة إدارية اختيارية")
        st.caption("لن تُنفَّذ تلقائياً. إذا أعاد PHP rows فقط بلا finalization موثوق، نكتفي بالمعاينة ولا نختلق شهادة اعتماد.")
        delta = st.session_state["history_delta"]
        preview = st.session_state.get("history_preview", (None, {}))[1]
        preview_token = preview.get("preview_token", "") if isinstance(preview, dict) else ""
        with st.expander("Commit بعد المعاينة", expanded=False):
            token = st.text_input("preview_token من استجابة المعاينة", value=preview_token, key="history_token")
            confirmed = st.checkbox("أؤكد أن الفصل انتهى رسمياً وأوافق على اعتماد نسخة تراكمية جديدة", key="history_commit_confirm")
            can_commit = bool(delta.get("finalization") and token and confirmed and config.admin_key)
            if not delta.get("finalization"):
                st.warning("History API لم يرجع finalization: {finalized_part_id, approval_reference}. لا يمكن عمل commit آمن حتى يوفّره المصدر المعتمد.")
            if st.button("اعتماد Commit", disabled=not can_commit):
                code, data, _ = client.advisor("POST", "/api/v1/admin/history/commit",
                                               data={**delta, "preview_token": token, "confirmation": True}, admin=True)
                st.session_state["history_commit"] = (code, data)
                show_api_status(code, data, label="commit")
        if "history_commit" in st.session_state:
            st.write("Commit response")
            view_json(st.session_state["history_commit"][1])
        with st.expander("Activate النسخة التراكمية بعد Commit", expanded=False):
            expected_hash = st.text_input("expected_history_sha256 من نتيجة Commit/Status", key="history_hash")
            activate_confirm = st.checkbox("أوافق على تفعيل النسخة بعد مراجعة البصمة", key="history_activate_confirm")
            if st.button("تفعيل Activate", disabled=not (expected_hash and activate_confirm and config.admin_key)):
                code, data, _ = client.advisor("POST", "/api/v1/admin/history/activate",
                                               data={"history_as_of_part": delta["part_id"],
                                                     "expected_history_sha256": expected_hash, "confirmation": True}, admin=True)
                show_api_status(code, data, label="activate")
    if st.button("عرض حالة Frozen History الحالية"):
        try:
            code, data, _ = client.advisor("GET", "/api/v1/admin/history/status", admin=True)
            show_api_status(code, data, label="history status")
        except ClientError as exc:
            st.error(str(exc))


# The collection tab deliberately does NOT interact with FastAPI recommendation
# endpoints, or with history commit/activate. It saves exact upstream HTTP bodies.
with tab_collection:
    st.subheader("📥 جمع وحفظ استجابات API — Pilot 20251")
    st.caption("هذه وظيفة أرشفة فقط: لا تدريب، لا توصية، لا تحديث Frozen History الرسمي.")
    snapshot_id = st.selectbox('نسخة البيانات', options=['after_backend_fix', 'before_backend_fix'], key='pilot_snapshot')
    readonly_snapshot = snapshot_id == 'before_backend_fix'
    store = PilotCollectionStore(Path(__file__).resolve().parents[2], snapshot_id=snapshot_id)
    st.info('النسخة النشطة: ' + snapshot_id + (' — أرشيف للقراءة فقط' if readonly_snapshot else ' — حفظ استجابات Backend المصححة'))
    st.code(str(store.root), language=None)
    try:
        cohort = store.load_students()
    except CollectionError as exc:
        st.error(str(exc))
        cohort = []

    def save_pilot_student(record):
        return store.collect_student(record, client)

    def save_pilot_history(part):
        dest = store.history_file(part)
        if store.state(dest) == 'saved':
            return True
        raise CollectionError('Frozen History is reused from the verified original snapshot; fetching is disabled.')

    if cohort:
        total_primary = sum(row['role'] == 'primary' for row in cohort)
        total_reserve = sum(row['role'] == 'reserve' for row in cohort)
        summary = store.overview(cohort)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric('طلاب أساسيون', total_primary)
        m2.metric('Student API', f"{summary['student_response_saved']}/{summary['primary_total']}")
        m3.metric('Courses API', f"{summary['courses_response_saved']}/{summary['primary_total']}")
        m4.metric('فصول التاريخ المحفوظة', f"{summary['history_saved']}/{summary['history_total']}")
        if summary['warnings']:
            st.warning(f"يوجد {summary['warnings']} ملف غير موثق أو تالف؛ لن يُستبدل تلقائيًا.")
        st.caption(f'عدد الاحتياط: {total_reserve}. الحفظ يتجاوز الملفات المحفوظة والمتحقق منها.')

        st.divider()
        st.markdown('**1 · حفظ استجابات الطلاب والمواد**')
        row_labels = {f"{r['sample_id']} | {r['role']}": r for r in cohort}
        selected = st.selectbox('اختيار طالب من students.csv', options=list(row_labels))
        c1, c2 = st.columns(2)
        single = c1.button('حفظ الطالب المختار', key='pilot_one_student', disabled=readonly_snapshot)
        all_primary = c2.button('جمع الأساسيين الـ30 وحفظهم', key='pilot_all_students', type='primary', disabled=readonly_snapshot)
        student_jobs = ([row_labels[selected]] if single else
                        [r for r in cohort if r['role'] == 'primary'] if all_primary else [])
        if student_jobs:
            bar = st.progress(0.0)
            report = []
            for i, row in enumerate(student_jobs, 1):
                try:
                    success = save_pilot_student(row)
                    report.append({'sample_id': row['sample_id'], 'status': 'saved' if success else 'incomplete'})
                except (ClientError, CollectionError, OSError, ValueError) as exc:
                    report.append({'sample_id': row['sample_id'], 'status': 'failed', 'reason': str(exc)})
                bar.progress(i / len(student_jobs))
            st.dataframe(report, use_container_width=True, hide_index=True)
            st.info('يمكنك إعادة التنفيذ؛ الاستجابات المحفوظة بصورة صحيحة لا تُستبدل.')

        st.divider()
        st.markdown('**2 · حفظ Frozen History التاريخي**')
        st.caption('التاريخ الأصلي المعاد استخدامه من 20201 إلى 20243. الجلب معطل للحفاظ على مقارنة ثابتة. لا commit ولا activate.')
        selected_part = st.selectbox('الفصل التاريخي', options=history_parts(), key='pilot_history_part')
        h1, h2 = st.columns(2)
        one_part = h1.button('جلب وحفظ الفصل المختار', key='pilot_one_history', disabled=True)
        all_parts = h2.button('جلب وحفظ الفصول الـ15', key='pilot_all_history', disabled=True)
        history_jobs = [selected_part] if one_part else history_parts() if all_parts else []
        if history_jobs:
            bar = st.progress(0.0)
            report = []
            for i, part in enumerate(history_jobs, 1):
                try:
                    ok = save_pilot_history(part)
                    report.append({'part_id': part, 'status': 'saved' if ok else 'incomplete'})
                except (ClientError, CollectionError, OSError, ValueError) as exc:
                    report.append({'part_id': part, 'status': 'failed', 'reason': str(exc)})
                bar.progress(i / len(history_jobs))
            st.dataframe(report, use_container_width=True, hide_index=True)

        st.divider()
        st.markdown('**3 · حالة ملفات التجربة**')
        with st.expander('تفاصيل الحالات', expanded=False):
            student_status = []
            for row in cohort:
                student_status.append({
                    'sample_id': row['sample_id'], 'role': row['role'],
                    'student': store.state(store.student_file(row['sample_id'], 'student')),
                    'courses': store.state(store.student_file(row['sample_id'], 'courses')),
                })
            st.dataframe(student_status, use_container_width=True, hide_index=True)
            st.dataframe([{'part_id': part, 'status': store.state(store.history_file(part))}
                          for part in history_parts()], use_container_width=True, hide_index=True)
