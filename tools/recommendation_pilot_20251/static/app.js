"use strict";

// Local API data is always rendered as text, including course names and errors.
const $ = (id) => document.getElementById(id);
const EXPERIMENTS = ["A", "B", "C"];
const TITLES = {A: "النظام الأصلي", B: "تاريخ الجامعة", C: "النظام المحسّن"};
const SUBTITLES = {A: "Original Baseline", B: "University History · ضابطة", C: "Enhanced Recommendation"};
const state = {students: [], selectedSample: null, run: null, activeStudent: 0, chosenPlan: null, courseContext: null, busy: false, pollToken: 0, runningCount: 0, runFamily: "actual"};
const ACTUAL_RUNS_API = "/api/actual-candidate-runs";
const CANDIDATE_LABELS = {original: "Original API", augmented: "Actual-Course Augmented"};
const CREDIT_LABELS = {fixed_18: "Experiment A · Fixed 18 Credits", actual_load: "Experiment B · Actual Credit Load Diagnostic"};

function isCandidateRun() { return asArray(state.run?.student_results).some((row) => row.candidate_mode); }
function viewMatches(row) {
  return !row.candidate_mode || (row.candidate_mode === ($("experiment-mode").value || "original") &&
    row.credit_experiment === ($("credit-experiment").value || "fixed_18"));
}
function activeResult() { return asArray(state.run?.student_results)[state.activeStudent]; }

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined && text !== null) node.textContent = String(text);
  return node;
}

function replace(node, ...children) { node.replaceChildren(...children); }
function asArray(value) { return Array.isArray(value) ? value : []; }
function numeric(value) {
  if (value === null || value === undefined || value === "" || typeof value === "boolean") return null;
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}
function num(value, digits = 2) {
  const number = numeric(value);
  return number === null ? "—" : number.toLocaleString("en-US", {maximumFractionDigits: digits, minimumFractionDigits: digits});
}
function pct(value) { const number = numeric(value); return number === null ? "—" : `${num(number * 100, 1)}%`; }
function signed(value, digits = 3) { const number = numeric(value); return number === null ? "—" : `${number > 0 ? "+" : ""}${num(number, digits)}`; }
function simple(value) {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}
function badge(status) {
  const label = String(status || "NOT_AVAILABLE");
  const labels = {PREDICTION_AVAILABLE: "التوقعات متاحة", PROVISIONAL_PLAN: "خطة تحليلية مؤقتة", VALIDATED_PLAN: "تم التحقق من التسجيل", BLOCKED: "التنبؤ متعذّر", NO_MATCHING_PLAN: "لا توجد خطة بالساعات المطلوبة", NOT_AVAILABLE: "لا توجد نتيجة", AVAILABLE: "متاح", UNAVAILABLE: "غير متاح"};
  const node = el("span", `badge ${label.toLowerCase().replace(/[^a-z_]/g, "")}`, labels[label] || "نتيجة محفوظة");
  return node;
}
function errorText(error) { return error instanceof Error ? error.message : simple(error); }
function showError(message) {
  $("global-error").textContent = message ? "تعذّر إكمال الطلب المحلي. راجع التفاصيل التقنية أو افتح نتيجة محفوظة." : "";
  $("global-error").hidden = !message;
  $("technical-error").textContent = message;
  $("technical-error").hidden = !message;
}

async function api(path, options = {}) {
  const response = await fetch(path, {cache: "no-store", ...options});
  const text = await response.text();
  let result;
  try { result = text ? JSON.parse(text) : {}; }
  catch (_) { throw new Error(`استجابة غير صالحة من الخادم المحلي (${response.status}).`); }
  if (!response.ok) {
    const detail = result.detail || result.error || result.message || `HTTP ${response.status}`;
    throw new Error(simple(detail));
  }
  return result;
}

function renderStudents() {
  replace($("student-options"), ...state.students.map((student) => new Option(studentChoiceLabel(student), studentChoiceLabel(student))));
  $("student-count").textContent = `(${state.students.length})`;
  updateSelection();
}

function studentChoiceLabel(student) { return `${student.sample_id} · الطالب ${student.student_id}`; }
function selectedStudent() { return state.students.find((student) => String(student.sample_id) === state.selectedSample); }
function updateSelection() {
  $("run-button").disabled = state.busy || !state.selectedSample;
  $("run-all").disabled = state.busy || !state.students.length;
  const student = selectedStudent();
  const result = asArray(state.run?.student_results).find((entry) => String(entry.sample_id) === state.selectedSample && viewMatches(entry));
  const summary = {...(student?.student_summary || {}), ...(result?.student_summary || {})};
  if (!student) { replace($("selected-student-summary"), el("p", "empty-small", "لم يُختر طالب بعد.")); return; }
  const heading = el("strong", "", `الطالب ${student.student_id}`);
  const facts = el("div", "selection-facts");
  const startingGpa = summary.start_agpa_points ?? summary.previous_gpa;
  facts.append(el("span", "", `معدل بداية الفصل: ${numeric(startingGpa) === null ? "غير متوفر" : num(startingGpa, 3)}`));
  if (numeric(summary.degree_credits_count) !== null) facts.append(el("span", "", `ساعات الدرجة: ${num(summary.degree_credits_count, 0)}`));
  if (summary.gpa_category ?? student.gpa_category) facts.append(el("span", "", `الفئة: ${summary.gpa_category ?? student.gpa_category}`));
  replace($("selected-student-summary"), heading, facts);
}

function chooseStudent() {
  const query = $("student-search").value.trim();
  const match = state.students.find((student) => [studentChoiceLabel(student), String(student.sample_id), String(student.student_id)].includes(query));
  state.selectedSample = match ? String(match.sample_id) : null;
  state.chosenPlan = null;
  state.courseContext = null;
  updateSelection();
  if (state.run) renderRun();
}

function setBusy(busy) {
  state.busy = busy;
  ["student-search", "target-credits", "max-plans", "load-run", "experiment-mode", "credit-experiment", "compare-candidates"].forEach((id) => { $(id).disabled = busy; });
  if (!busy) $("load-run").disabled = !$("saved-runs").value;
  renderStudents();
}

function renderProgress(progress) {
  $("run-progress").hidden = false;
  const total = Math.max(1, Number(progress.total) || state.runningCount || 1);
  const completed = Math.max(0, Number(progress.completed) || 0);
  $("progress-bar").max = total;
  $("progress-bar").value = Math.min(total, completed);
  $("progress-count").textContent = `${completed} / ${total}`;
  $("progress-label").textContent = progress.status === "completed" ? "اكتمل التشغيل وحُفظت النتائج" : progress.status === "failed" ? "تعذّر إكمال التشغيل" : "جارٍ تنفيذ المقارنة…";
}

async function refreshRuns() {
  const previous = $("saved-runs").value;
  const [diagnostic, archived] = await Promise.all([api(ACTUAL_RUNS_API), api("/api/runs")]);
  const options = [new Option("اختر تشغيلاً محفوظاً", "")];
  for (const [family, payload] of [["actual", diagnostic], ["legacy", archived]]) for (const run of asArray(payload.runs)) {
    const when = run.created_at ? new Date(run.created_at) : null;
    const timestamp = when && !Number.isNaN(when.valueOf()) ? when.toLocaleString("ar-SY") : simple(run.created_at);
    const label = `${run.snapshot_id || "before_backend_fix"} · ${family === "actual" ? "تشخيص المرشحات" : "مقارنة A/B/C"} · ${timestamp} · ${run.student_count ?? "؟"} طالب · ${run.status || "محفوظ"}`;
    options.push(new Option(label, `${family}:${run.run_id}`));
  }
  replace($("saved-runs"), ...options);
  if (options.some((option) => option.value === previous)) $("saved-runs").value = previous;
  $("load-run").disabled = state.busy || !$("saved-runs").value;
}

async function pollRun(runId, token, family = "actual") {
  const base = family === "actual" ? ACTUAL_RUNS_API : "/api/runs";
  while (token === state.pollToken) {
    const progress = await api(`${base}/${encodeURIComponent(runId)}/progress`);
    if (token !== state.pollToken) return;
    renderProgress(progress);
    if (progress.status === "failed") throw new Error(`تعذّر التشغيل: ${simple(progress.error || progress.reason)}`);
    if (progress.status === "completed") {
      await loadRun(`${family}:${runId}`);
      await refreshRuns();
      $("saved-runs").value = `${family}:${runId}`;
      return;
    }
    await new Promise((resolve) => setTimeout(resolve, 800));
  }
}

async function startRun(event) {
  event.preventDefault();
  if (!$("run-form").reportValidity()) return;
  if (state.busy || !state.selectedSample) return;
  await executeRun([state.selectedSample]);
}

async function executeRun(sampleIds) {
  if (state.busy || !sampleIds.length || !$("run-form").reportValidity()) return;
  showError("");
  const candidateModes = $("compare-candidates").checked ? ["original", "augmented"] : [$("experiment-mode").value || "original"];
  const diagnostic = $("compare-candidates").checked;
  const family = diagnostic ? "actual" : "legacy";
  state.runningCount = diagnostic ? sampleIds.length * candidateModes.length * 2 : sampleIds.length;
  setBusy(true);
  renderProgress({completed: 0, total: state.runningCount, status: "running"});
  const token = ++state.pollToken;
  try {
    const payload = diagnostic
      ? {sample_ids: sampleIds, candidate_modes: candidateModes, credit_experiments: ["fixed_18", "actual_load"], max_plans: Number($("max-plans").value)}
      : {sample_ids: sampleIds, target_credits: Number($("target-credits").value), max_plans: Number($("max-plans").value)};
    const created = await api(diagnostic ? ACTUAL_RUNS_API : "/api/runs", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(payload)});
    if (!created.run_id) throw new Error("لم يُرجع الخادم معرف تشغيل.");
    await pollRun(String(created.run_id), token, family);
  } catch (error) {
    $("progress-label").textContent = "توقف التتبع بسبب خطأ؛ راجع التشغيلات المحفوظة";
    showError(errorText(error));
  } finally { if (token === state.pollToken) setBusy(false); }
}

async function loadRun(runId) {
  $("load-run").disabled = true;
  $("load-run").textContent = "جارٍ تحميل النتائج…";
  try {
  const [family, identifier] = String(runId).includes(":") ? String(runId).split(":", 2) : ["legacy", runId];
  const base = family === "actual" ? ACTUAL_RUNS_API : "/api/runs";
  const result = await api(`${base}/${encodeURIComponent(identifier)}`);
  state.runFamily = family;
  state.run = result;
  const students = asArray(result.student_results);
  const matched = students.find((student) => String(student.sample_id) === state.selectedSample && viewMatches(student));
  const active = matched || students[0];
  if (active) {
    if (active.candidate_mode && !students.some((row) => String(row.sample_id) === String(active.sample_id) && viewMatches(row))) {
      $("experiment-mode").value = active.candidate_mode;
      $("credit-experiment").value = active.credit_experiment;
    }
    state.selectedSample = String(active.sample_id);
    const student = selectedStudent() || active;
    $("student-search").value = studentChoiceLabel(student);
  }
  state.chosenPlan = null;
  state.courseContext = null;
  updateSelection();
  renderRun();
  } finally {
    $("load-run").textContent = "عرض النتيجة";
    $("load-run").disabled = state.busy || !$("saved-runs").value;
  }
}

function summaryItem(label, value) { const item = el("div", "summary-item", label); item.append(el("strong", "", value)); return item; }

function renderRun() {
  const run = state.run;
  const manifest = run.run_manifest || {};
  const students = asArray(run.student_results);
  state.activeStudent = students.findIndex((student) => String(student.sample_id) === state.selectedSample && viewMatches(student));
  if (state.activeStudent < 0 && students.length) {
    $("welcome").hidden = false;
    $("results").hidden = true;
    renderMetadata($("experiment-technical"), {});
    replace($("student-issues"));
    replace($("analysis-support"));
    renderPlanDetail();
    renderObservedComparison(null);
    renderActualPlanForecasts(null);
    $("candidate-diagnostic-panel").hidden = true;
    return;
  }
  $("welcome").hidden = true;
  $("results").hidden = false;
  $("run-id").textContent = `${run.snapshot_id || manifest.snapshot_id || "before_backend_fix"} · ${manifest.run_id || run.run_id || ""}`;
  const studentCount = new Set(students.map((student) => student.sample_id)).size;
  const current = students[state.activeStudent];
  replace($("run-summary"), summaryItem("طلاب التشغيل المحفوظ", studentCount), summaryItem("الساعات المطلوبة", current?.target_credits ?? manifest.target_credits ?? "—"),
    ...(current?.candidate_mode ? [summaryItem("مصدر المرشحات", CANDIDATE_LABELS[current.candidate_mode]), summaryItem("اختبار الساعات", CREDIT_LABELS[current.credit_experiment])] : []));
  renderMetadata($("run-metadata"), {run_manifest: manifest, diagnostics: run.diagnostics || {}});
  if (!students.length) {
    replace($("student-overview"), el("p", "empty-small", "لا يحتوي هذا التشغيل على نتائج طلاب. راجع التشخيص."));
    replace($("experiment-grid")); replace($("student-issues"));
    renderPlanDetail();
    renderObservedComparison(null);
    renderActualPlanForecasts(null);
    ["courses", "plans", "support"].forEach((tab) => replace($(`analysis-${tab}`), el("p", "empty-small", "لا توجد بيانات.")));
    return;
  }
  renderStudent(students[state.activeStudent]);
}

function issueNode(issue) {
  if (typeof issue === "string") return el("li", "", issue);
  const node = el("li");
  node.append(el("strong", "", issue.code || issue.status || issue.field || "ملاحظة"));
  node.append(el("span", "", issue.message || issue.reason || simple(issue)));
  return node;
}

function renderStudent(student) {
  const label = el("div");
  label.append(el("h3", "", student.sample_id || "نتيجة الطالب"), el("p", "", `معرّف الطالب: ${simple(student.student_id)}`));
  const facts = el("div", "overview-facts");
  facts.append(el("span", "", `المواد المرشحة: ${simple(student.candidate_count)}`));
  replace($("student-overview"), label, facts);
  const issues = [...asArray(student.issues), ...asArray(student.warnings)];
  const issueElements = [];
  if (issues.length) {
    const alert = el("div", "alert");
    alert.append(el("strong", "", "قيود المدخلات وصلاحية التسجيل"));
    const list = el("ul"); list.append(...issues.map(issueNode)); alert.append(list); issueElements.push(alert);
  }
  if (student.search?.truncated || student.search_truncated) issueElements.push(el("div", "alert", "البحث محدود بعدد الخطط المعلن. النتائج لا تثبت أفضلية عالمية عبر جميع الخطط الممكنة."));
  replace($("student-issues"), ...issueElements);
  renderCandidateDiagnostic(student);
  renderMetadata($("experiment-technical"), {student_status: student.status, student_summary: student.student_summary, search: student.search, experiments: Object.fromEntries(EXPERIMENTS.map((id) => { const experiment = student.experiments?.[id] || {}; const {plans, diagnostic_plans, analytical_plans, course_predictions, ...technical} = experiment; return [id, technical]; }))});
  replace($("experiment-grid"), ...EXPERIMENTS.map((id) => renderExperiment(id, student.experiments?.[id] || {status: "NOT_AVAILABLE", reason: "لا توجد نتيجة لهذه التجربة في التشغيل المحفوظ."}, student.observed_plan_prediction?.experiments?.[id], student.observed_plan)));
  renderActualPlanForecasts(student);
  const actualForecast = student.observed_plan_prediction || {};
  renderMetadata($("actual-prediction-source"), {context: actualForecast.context, provenance: actualForecast.provenance,
    registration_source_sha256: actualForecast.registration_source_sha256, shared_inputs_sha256: actualForecast.shared_inputs_sha256,
    plan_set_sha256: actualForecast.plan_set_sha256, experiments: Object.fromEntries(EXPERIMENTS.map((id) => {
      const {course_predictions, ...metadata} = actualForecast.experiments?.[id] || {}; return [id, metadata];
    }))});
  renderPlanDetail();
  renderObservedComparison(student);
  renderMetadata($("observed-source"), student.observed_plan?.source || {});
  renderCourseComparison(student);
  renderPlanComparison(student);
  renderSupport(student);
}

function renderCandidateDiagnostic(student) {
  const panel = $("candidate-diagnostic-panel");
  panel.hidden = !student?.candidate_mode;
  if (panel.hidden) return;
  const coverage = student.candidate_coverage || {};
  const peers = asArray(state.run?.student_results).filter((row) => String(row.sample_id) === String(student.sample_id) &&
    row.credit_experiment === student.credit_experiment);
  $("diagnostic-warning").hidden = !peers.some((row) => row.candidate_mode === "augmented");
  const counts = el("div", "summary-strip");
  counts.append(summaryItem("المواد الفعلية", simple(coverage.actual_course_count)),
    summaryItem("مرشحات API الخام الأصلية", simple(coverage.original_candidate_count)),
    summaryItem("المرشحات الخام بعد الإضافة", simple(coverage.augmented_candidate_count)),
    summaryItem("المواد المحقونة", simple(coverage.injected_course_count)),
    summaryItem("الفعليات داخل API قبل / بعد", `${simple(coverage.actual_in_candidates_before)} / ${simple(coverage.actual_in_candidates_after)}`),
    summaryItem("التغطية الخام قبل / بعد", `${pct(coverage.coverage_before)} / ${pct(coverage.coverage_after)}`));
  const content = [counts];
  content.push(el("p", "comparison-note", "تغطية API الخام منفصلة عن المواد المقبولة للبحث. تبقى مرشحات API الأصلية خاضعة لقواعدها؛ قد تُرفض مادة فعلية رغم وجودها في الرد الخام."));
  const modelBefore = coverage.model_actual_in_candidates_before ?? coverage.actual_courses_in_original_model_candidates ??
    (numeric(coverage.model_candidate_coverage_before) !== null && numeric(coverage.actual_course_count) !== null ? Math.round(coverage.model_candidate_coverage_before * coverage.actual_course_count) : undefined);
  const modelAfter = coverage.model_actual_in_candidates_after ?? coverage.actual_courses_in_augmented_model_candidates ??
    (numeric(coverage.model_candidate_coverage_after) !== null && numeric(coverage.actual_course_count) !== null ? Math.round(coverage.model_candidate_coverage_after * coverage.actual_course_count) : undefined);
  if (modelBefore !== undefined || modelAfter !== undefined) content.push(el("p", "comparison-note",
    `المواد الفعلية داخل مساحة البحث قبل / بعد: ${simple(modelBefore)} / ${simple(modelAfter)} · مرشحات البحث الحالية: ${simple(student.model_candidate_count ?? coverage.model_candidate_count ?? student.candidate_count)}`));
  if (student.credit_experiment === "actual_load") content.push(el("div", "alert", `Actual Credit Load Diagnostic — الهدف ${simple(student.target_credits ?? student.observed_plan?.total_credits)} ساعة مأخوذ من تسجيل الطالب الفعلي، وليس قرار توصية مستقل. حدود التسجيل لا تُتجاوز تلقائياً.`));
  else if (numeric(student.observed_plan?.total_credits) !== null && numeric(student.observed_plan.total_credits) !== 18) content.push(el("p", "comparison-note", `الحمل الفعلي ${simple(student.observed_plan.total_credits)} ساعة؛ لا يُنتظر تطابق كامل مع هدف 18 ساعة.`));
  const injected = asArray(coverage.injected_courses);
  content.push(el("h3", "candidate-section-title", "تفاصيل المواد المحقونة"));
  content.push(injected.length ? makeTable(["معرّف المادة", "اسم المادة", "المصدر", "الأهلية التاريخية"], injected.map((course) =>
    [course.course_id, course.course_name || "الاسم غير متوفر", "ACTUAL_INJECTED", "UNVERIFIED · غير مثبتة"])) : el("p", "empty-small", "لم تُحقن مواد في هذا الوضع."));
  const rejected = asArray(coverage.rejected_injections);
  if (rejected.length) { content.push(el("h3", "candidate-section-title", "إضافات مرفوضة"), makeTable(["المادة", "سبب الرفض"], rejected.map((course) => [course.course_id, course.reason || course.code || simple(course)]))); }
  const warnings = asArray(student.warnings);
  if (warnings.length) { const list = el("ul", "candidate-warnings"); list.append(...warnings.map(issueNode)); content.push(list); }
  replace($("candidate-coverage"), ...content);
  const rows = [];
  for (const row of peers) for (const id of EXPERIMENTS) {
    const model = row.experiments?.[id] || {};
    const metrics = model.recommendation_metrics || row.recommendation_metrics?.[id] || {};
    const search = row.search || {};
    rows.push([CANDIDATE_LABELS[row.candidate_mode], id, num(row.target_credits ?? row.observed_plan?.total_credits, 2),
      simple(metrics.top1_actual_overlap), simple(metrics.top3_union_actual_overlap), num(availablePlans(model)[0]?.expected_plan_gpa, 3),
      simple(search.evaluated_plan_count ?? search.evaluated_plans ?? search.plan_count ?? search.generated_plans ?? row.evaluated_plan_count),
      simple(search.visited_search_states ?? search.visited_states ?? search.states_visited ?? row.search_states),
      search.truncated === undefined && row.search_truncated === undefined ? "غير معلوم" : (search.truncated ?? row.search_truncated) ? "توقف عند الميزانية" :
        search.complete_plan_space_examined === false && (search.visited_search_states ?? 0) === 0 ? "لم يبدأ بسبب المدخلات أو القيود" : "اكتمل البحث",
      metrics.actual_plan_examined === null || metrics.actual_plan_examined === undefined ? "غير متاح / غير ممكن" : metrics.actual_plan_examined ? "نعم" : "لا"]);
  }
  const comparison = [el("h3", "candidate-section-title", `${CREDIT_LABELS[student.credit_experiment]} · الطالب نفسه`),
    el("p", "comparison-note", "تُقارن الوضعيات عند هدف الساعات والميزانية نفسيهما. زيادة التقاطع وصف لتغطية المرشحات؛ لا تثبت جودة توصية بديلة."),
    makeTable(["وضع المرشحات", "النظام", "الهدف", "Top-1 تقاطع", "Top-3 اتحاد", "GPA أعلى خطة", "خطط مفحوصة", "حالات البحث", "حالة البحث", "الخطة الفعلية مفحوصة"], rows)];
  if (peers.length < 2) comparison.push(el("p", "empty-small", "لا توجد نتيجة محفوظة للوضع الآخر في اختبار الساعات هذا. فعّل مقارنة Original وAugmented ثم شغّل الطالب."));
  const timing = student.latency || student.timing;
  if (timing) { const details = el("details", "latency-details"); details.append(el("summary", "", "الأزمنة وإحصاءات التنبؤ المحفوظة")); const metadata = el("div", "metadata"); renderMetadata(metadata, {latency: timing, prediction_metrics: student.prediction_metrics || student.observed_plan_prediction?.metrics || {}}); details.append(metadata); comparison.push(details); }
  replace($("candidate-mode-comparison"), ...comparison);
}

function renderExperiment(id, experiment, actualForecast = null, observed = null) {
  const card = el("article", "experiment-card"); card.dataset.experiment = id;
  const header = el("header", "experiment-header");
  const status = predictionStatus(experiment);
  const label = el("div", "experiment-label"); label.append(el("span", "experiment-letter", id), badge(status));
  header.append(label, el("h3", "", TITLES[id]), el("p", "", SUBTITLES[id]));
  const body = el("div", "experiment-body");
  if (actualForecast && ["AVAILABLE", "PARTIAL"].includes(observed?.status)) {
    const actualDetails = el("details", "actual-model-details");
    actualDetails.append(el("summary", "", "توقعات مواد الطالب الفعلية"));
    if (actualForecast.prediction_status === "PREDICTION_AVAILABLE") {
      actualDetails.append(metric("معدل خطة الطالب الفعلية المتوقع", num(actualForecast.expected_plan_gpa, 3)));
      const predictions = courseMap(actualForecast.course_predictions);
      actualDetails.append(makeTable(["المادة", "التوقع /100", "الفعلية /100"], asArray(observed.courses).map((course) =>
        [courseLabel(course), num(predictions.get(String(course.course_id))?.predicted_mark, 2), num(course.actual_mark, 2)])));
    } else actualDetails.append(el("p", "empty-small", actualForecast.reason_ar || "تعذر التنبؤ بمواد الخطة الفعلية في هذا النظام."));
    body.append(actualDetails, el("h4", "candidate-section-title", "الخطط المرشحة"));
  }
  const plans = availablePlans(experiment).slice(0, 3);
  const provisional = experiment.plan_status !== "VALIDATED_PLAN";
  if (plans.length) {
    body.append(badge(provisional ? "PROVISIONAL_PLAN" : "VALIDATED_PLAN"));
    if (provisional) body.append(el("p", "experiment-reason", "نتائج تحليلية تشخيصية. صلاحية التسجيل غير مؤكدة، ولا تُعد توصيات معتمدة."));
    body.append(el("p", "experiment-reason", arabicReason(experiment, status)));
    body.append(...plans.map((plan, index) => renderPlanCard(id, plan, index, provisional, experiment)));
  } else {
    body.append(el("p", "experiment-reason", arabicReason(experiment, status)));
    body.append(el("p", "empty-small", status === "NO_MATCHING_PLAN" ? "لم تنتج خطة تطابق الساعات المطلوبة ضمن البحث المتاح." : "لا توجد توقعات خطط متاحة لهذه التجربة في هذا التشغيل."));
  }
  const stats = el("div", "experiment-stats");
  const elapsed = experiment.elapsed_seconds ?? experiment.timing?.elapsed_seconds;
  stats.append(el("span", "", `خطط معروضة: ${plans.length}`), el("span", "", `الزمن: ${elapsed === undefined ? "—" : `${num(elapsed, 2)} ث`}`));
  body.append(stats); card.append(header, body); return card;
}

function predictionStatus(experiment) {
  if (experiment.prediction_status) return experiment.prediction_status;
  // Older saved results may contain scored diagnostic plans with a plan-level BLOCKED status.
  if (asArray(experiment.analytical_plans).length || asArray(experiment.diagnostic_plans).length || asArray(experiment.plans).length) return "PREDICTION_AVAILABLE";
  return experiment.status === "NO_MATCHING_PLAN" ? "NO_MATCHING_PLAN" : "BLOCKED";
}
function availablePlans(experiment) {
  if (predictionStatus(experiment) === "BLOCKED") return [];
  const plans = Array.isArray(experiment.analytical_plans) ? experiment.analytical_plans : asArray(experiment.diagnostic_plans).length ? experiment.diagnostic_plans : asArray(experiment.plans);
  return plans.filter((plan) => numeric(plan.expected_plan_gpa) !== null);
}
function arabicReason(experiment, status) {
  if (typeof experiment.reason_ar === "string" && experiment.reason_ar.trim()) return experiment.reason_ar;
  if (status === "BLOCKED") return "مدخلات التنبؤ أو النموذج غير متوافقة. سبب التعذّر والإصلاح المطلوب في التفاصيل التقنية.";
  if (status === "NO_MATCHING_PLAN") return "لا توجد خطة بالساعات المختارة ضمن البحث المتاح.";
  return "التوقعات متاحة. يُعرض المعدل التراكمي عند توفر طريقة حساب مدعومة فقط.";
}
function cumulativeSupported(experiment, plan) {
  return experiment?.cumulative_gpa_status === "AVAILABLE" && numeric(plan.projected_cumulative_gpa) !== null;
}

function metric(label, value) { const node = el("div"); node.append(el("span", "", label), el("strong", "", value)); return node; }
function courseLabel(course) { return course.course_name || `مادة ${simple(course.course_id)}`; }
function canonicalCourseId(value) {
  const text = String(value ?? "").trim(), match = text.match(/^([+-]?)(\d+)(?:\.(\d+))?$/);
  if (!match) return text;
  const integer = match[2].replace(/^0+(?=\d)/, ""), fraction = (match[3] || "").replace(/0+$/, "");
  return `${match[1] === "-" && (integer !== "0" || fraction) ? "-" : ""}${integer}${fraction ? `.${fraction}` : ""}`;
}
function candidateSource(course) {
  if (course.candidate_source) return course.candidate_source;
  const provenance = activeResult()?.candidate_coverage?.candidate_provenance || {};
  const key = canonicalCourseId(course.course_id);
  const record = provenance[key] || Object.entries(provenance).find(([id]) => canonicalCourseId(id) === key)?.[1];
  return (typeof record === "string" ? record : record?.candidate_source) || "غير موثّق";
}
function planKey(plan) { return asArray(plan.courses).map((course) => String(course.course_id)).sort().join("|"); }
function validityLabel(plan) {
  return plan.plan_status === "VALIDATED_PLAN" ? "تم التحقق من التسجيل" : "تحليلية · صلاحية التسجيل غير مؤكدة";
}

function renderPlanCard(experimentId, plan, index, diagnostic, experiment) {
  const button = el("button", "plan-card"); button.type = "button";
  const selected = state.chosenPlan && state.chosenPlan.experimentId === experimentId && state.chosenPlan.plan === plan;
  button.setAttribute("aria-pressed", String(Boolean(selected)));
  const head = el("div", "plan-card-head"); head.append(el("span", "plan-rank", `الخطة ${index + 1}`), el("span", "plan-credit", `${simple(plan.total_credits)} ساعة · ${plan.course_count ?? asArray(plan.courses).length} مواد`));
  const names = asArray(plan.courses).map(courseLabel).join(" · ");
  const gpa = el("div", "plan-gpa"); gpa.append(el("span", "", "معدل الفصل المتوقع"), el("strong", "", num(plan.expected_plan_gpa, 3)));
  const metrics = el("div", "plan-metrics");
  if (cumulativeSupported(experiment, plan)) {
    metrics.append(metric("المعدل التراكمي", num(plan.projected_cumulative_gpa, 3)));
    if (numeric(plan.expected_cumulative_gpa_gain) !== null) metrics.append(metric("التحسن المتوقع", signed(plan.expected_cumulative_gpa_gain)));
  }
  metrics.append(metric("ساعات الرسوب المتوقعة", num(plan.expected_failed_credits, 2)));
  const observed = asArray(state.run?.student_results)[state.activeStudent]?.observed_plan;
  const overlap = compareObservedPlan(plan, observed);
  if (overlap) metrics.append(metric("المشترك مع خطة الطالب", `${overlap.sharedCount} من ${overlap.actualCount} مادة فعلية`));
  const risk = plan.plan_difficulty_balance || plan.risk || {};
  if (numeric(risk.max_fail_probability) !== null) metrics.append(metric("أعلى خطر رسوب", pct(risk.max_fail_probability)));
  button.append(head, el("p", "plan-course-list", names || "لا توجد تفاصيل مواد"), gpa, metrics, el("span", "plan-validity", diagnostic ? "تحليلية · صلاحية التسجيل غير مؤكدة" : "تم التحقق من التسجيل"));
  button.addEventListener("click", () => { state.chosenPlan = {experimentId, plan, diagnostic}; state.courseContext = planKey(plan); renderStudent(asArray(state.run?.student_results)[state.activeStudent]); });
  return button;
}

function makeTable(headings, rows) {
  const wrapper = el("div", "table-wrap");
  const table = el("table"); const head = el("thead"); const headRow = el("tr");
  for (const heading of headings) { const th = el("th", "", heading); th.scope = "col"; headRow.append(th); }
  head.append(headRow); const body = el("tbody");
  for (const values of rows) {
    const row = el("tr");
    for (const value of values) {
      const cell = el("td");
      if (value instanceof Node) cell.append(value); else cell.textContent = simple(value);
      row.append(cell);
    }
    body.append(row);
  }
  table.append(head, body); wrapper.append(table); return wrapper;
}

function renderPlanDetail() {
  const chosen = state.chosenPlan;
  $("selected-plan-label").textContent = chosen ? `التجربة ${chosen.experimentId}` : "";
  if (!chosen) { replace($("plan-detail"), el("p", "empty-small", "اختر خطة متاحة لعرض المواد والتوقعات التفصيلية.")); replace($("plan-technical")); return; }
  const courses = asArray(chosen.plan.courses);
  const showPeers = chosen.experimentId === "C" && courses.some((course) => Object.hasOwn(course, "peer_expected_points") || Object.hasOwn(course, "similar_peer_support"));
  const showSource = Boolean(activeResult()?.candidate_mode);
  const rows = courses.map((course) => [courseLabel(course), ...(showSource ? [candidateSource(course)] : []), course.course_credits, num(course.predicted_mark, 2), num(course.expected_points, 3), pct(course.fail_probability), ...(showPeers ? [num(course.peer_expected_points, 3), peerSupportCell(course)] : [])]);
  const content = [];
  if (chosen.diagnostic) content.push(el("div", "alert", "خطة تشخيصية: راجع القيود وحالة الصلاحية قبل تفسير التوقعات. اختيارها هنا لا يحوّلها إلى توصية صالحة."));
  content.push(makeTable(["المادة", ...(showSource ? ["مصدر المرشح"] : []), "الساعات", "العلامة المتوقعة /100", "النقاط المتوقعة", "احتمال الرسوب", ...(showPeers ? ["نقاط الأقران التاريخية", "دعم الأقران المتشابهين"] : [])], rows));
  if (showPeers) content.push(el("p", "help-text", "نقاط الأقران مؤشر من التاريخ المتاح وليست توقع النموذج. تُميّز المواد ذات الدعم الضعيف، وتبقى القيم غير المتوفرة فارغة."));
  renderMetadata($("plan-technical"), chosen.plan);
  replace($("plan-detail"), ...content);
}

function courseMap(courses) {
  return new Map(asArray(courses).filter((course) => course.course_id !== null && course.course_id !== undefined).map((course) => [String(course.course_id), course]));
}

function renderActualPlanForecasts(student) {
  const container = $("actual-plan-forecasts"), observed = student?.observed_plan;
  const forecast = student?.observed_plan_prediction;
  if (!["AVAILABLE", "PARTIAL"].includes(observed?.status)) {
    replace(container, el("p", "empty-small", observed?.reason_ar || "التسجيل الفعلي غير متوفر؛ لا يمكن عرض توقعات موثوقة لمواده."));
    return;
  }
  const content = [el("p", "comparison-note", `${student?.candidate_mode ? "توقعات محفوظة وقت التشغيل" : "توقعات معاد حسابها"} لكل نظام على مواد الطالب الفعلية كاملة، بساعاتها الفعلية. لا تُنقل من خطة مرشحة أخرى، ولا تتغير عند اختيار خطة مرشحة. العلامات الفعلية للمقارنة فقط ولا تدخل في حساب التوقع.`)];
  const summaries = el("div", "actual-model-summaries");
  for (const id of EXPERIMENTS) {
    const experiment = forecast?.context === "actual_registered_plan" ? forecast.experiments?.[id] : null;
    const ready = experiment?.prediction_status === "PREDICTION_AVAILABLE";
    const summary = el("div", "actual-model-summary");
    summary.append(el("strong", "", `${id} · ${TITLES[id]}`), badge(ready ? "PREDICTION_AVAILABLE" : "BLOCKED"));
    if (ready) summary.append(metric("معدل الخطة الفعلية المتوقع", num(experiment.expected_plan_gpa, 3)));
    else summary.append(el("p", "empty-small", experiment?.reason_ar || "لم يتوفر توقع مستقل لهذا النظام على الخطة الفعلية."));
    summaries.append(summary);
  }
  content.push(summaries);
  content.push(actualPlanForecastTable(student));
  if (student.prediction_metrics) {
    content.push(el("h3", "candidate-section-title", "تقييم توقع العلامات على الخطة الفعلية"),
      el("p", "comparison-note", "أخطاء وصفية على المواد الفعلية ذات النتائج المتاحة. اختلاف Student Snapshot يحول دون اعتمادها كدقة تاريخية مثبتة؛ لا تقيس جودة الخطط الجديدة."),
      makeTable(["النظام", "عدد النتائج", "MAE", "RMSE", "Bias", "Fail Brier", "Fail Log Loss", "Fail ROC AUC"], EXPERIMENTS.map((id) => {
        const metrics = student.prediction_metrics[id] || {};
        return [id, simple(metrics.course_count ?? metrics.count ?? metrics.n), num(metrics.mae, 3), num(metrics.rmse, 3), signed(metrics.bias, 3),
          num(metrics.fail_brier, 4), num(metrics.fail_log_loss, 4), num(metrics.fail_roc_auc, 4)];
      })));
  }
  replace(container, ...content);
}

function actualPlanForecastTable(student) {
  const forecast = student.observed_plan_prediction;
  const maps = Object.fromEntries(EXPERIMENTS.map((id) => {
    const experiment = forecast?.context === "actual_registered_plan" ? forecast.experiments?.[id] : null;
    return [id, experiment?.prediction_status === "PREDICTION_AVAILABLE" ? courseMap(experiment.course_predictions) : new Map()];
  }));
  const rows = asArray(student.observed_plan?.courses).map((course) => [courseLabel(course), num(course.actual_mark, 2),
    ...EXPERIMENTS.map((id) => num(maps[id].get(String(course.course_id))?.predicted_mark, 2))]);
  return makeTable(["المادة الفعلية", "العلامة الفعلية /100", "توقع A /100", "توقع B /100", "توقع C /100"], rows);
}

function compareObservedPlan(plan, observed) {
  if (!["AVAILABLE", "PARTIAL"].includes(observed?.status) || !asArray(observed.courses).length) return null;
  const candidate = courseMap(plan?.courses), actual = courseMap(observed.courses);
  const shared = [...candidate.keys()].filter((id) => actual.has(id));
  const candidateOnly = [...candidate.keys()].filter((id) => !actual.has(id));
  const actualOnly = [...actual.keys()].filter((id) => !candidate.has(id));
  const creditCompatible = numeric(plan?.total_credits) === null || numeric(observed.total_credits) === null ||
    Math.abs(Number(plan.total_credits) - Number(observed.total_credits)) < 0.000001;
  return {candidate, actual, shared, candidateOnly, actualOnly, sharedCount: shared.length, candidateCount: candidate.size,
    actualCount: actual.size, creditCompatible, exactMatch: !candidateOnly.length && !actualOnly.length && creditCompatible};
}

function actualResultLabel(course) {
  if (!course) return "لم يسجلها الطالب";
  const labels = {NO_FINAL_RESULT: "لا توجد علامة نهائية", INVALID_FINAL_MARK: "علامة غير صالحة",
    OUTCOME_IDENTITY_MISMATCH: "هوية النتيجة غير مطابقة", AMBIGUOUS_FINAL_RESULT: "نتائج مكررة غير محسومة"};
  return labels[course.result_status] || (numeric(course.actual_mark) === null ? "لا توجد علامة نهائية" : "علامة نهائية متاحة");
}

function renderObservedComparison(student) {
  const container = $("observed-comparison"), observed = student?.observed_plan;
  if (!["AVAILABLE", "PARTIAL"].includes(observed?.status)) {
    replace(container, el("p", "empty-small", observed?.reason_ar || "بيانات التسجيل الفعلي غير متوفرة لهذا التشغيل؛ لا يمكن حساب التطابق."));
    return;
  }
  const chosen = state.chosenPlan;
  const comparison = compareObservedPlan(chosen?.plan, observed);
  if (!comparison) { replace(container, el("p", "empty-small", "سجل التسجيل الفعلي غير كافٍ للمقارنة.")); return; }
  const content = [];
  const summary = el("div", "summary-strip");
  summary.append(summaryItem("مواد الطالب الفعلية", comparison.actualCount), summaryItem("ساعات التسجيل الفعلي", num(observed.total_credits, 2)),
    summaryItem("مواد لها علامة نهائية", observed.graded_course_count ?? "—"));
  content.push(summary);
  if (chosen) {
    const coverage = el("div", "observed-overlap");
    coverage.append(metric("المواد المشتركة", `${comparison.sharedCount} من ${comparison.actualCount} مادة فعلية (${pct(comparison.sharedCount / comparison.actualCount)})`),
      metric("من مواد الخطة المرشحة", `${comparison.sharedCount} من ${comparison.candidateCount} (${comparison.candidateCount ? pct(comparison.sharedCount / comparison.candidateCount) : "—"})`),
      metric("مرشحة فقط", comparison.candidateOnly.length), metric("فعلية فقط", comparison.actualOnly.length));
    content.push(el("p", "comparison-note", `مقارنة التجربة ${chosen.experimentId} · ${comparison.exactMatch ? "تطابق كامل لمجموعة المواد" : comparison.sharedCount ? "تطابق جزئي لمجموعة المواد" : "لا توجد مواد مشتركة"}`), coverage);
  } else {
    const forecast = student.observed_plan_prediction;
    const ready = forecast?.context === "actual_registered_plan" && EXPERIMENTS.some((id) => forecast.experiments?.[id]?.prediction_status === "PREDICTION_AVAILABLE");
    if (ready) {
      content.push(el("p", "comparison-note", "لم تُختَر خطة مرشحة؛ هذه توقعات A وB وC على خطة الطالب الفعلية كاملة. اختر خطة مرشحة لمقارنة المواد المشتركة معها."), actualPlanForecastTable(student));
    } else {
      content.push(el("p", "comparison-note", "اختر خطة مرشحة لمقارنة المواد المشتركة معها. لا تتوفر هنا توقعات مستقلة للخطة الفعلية؛ المعروض أدناه هو العلامات الفعلية فقط."),
        makeTable(["المادة الفعلية", "العلامة الفعلية /100"], asArray(observed.courses).map((course) => [courseLabel(course), num(course.actual_mark, 2)])));
    }
    replace(container, ...content);
    return;
  }
  content.push(el("p", "comparison-note", "العلامات من 100. الفرق = المتوقع − الفعلي. التوقع يخص سياق الخطة المرشحة؛ هذه مقارنة وصفية للمواد المشتركة، وليست تقييماً لتفوق خطة بديلة."));
  const ids = chosen ? [...comparison.shared, ...comparison.candidateOnly, ...comparison.actualOnly] : [...comparison.actual.keys()];
  const rows = ids.map((id) => {
    const candidate = chosen ? comparison.candidate.get(id) : null, actual = comparison.actual.get(id);
    const predictedMark = numeric(candidate?.predicted_mark), actualMark = numeric(actual?.actual_mark);
    const name = el("div", "", actual?.course_name || candidate?.course_name || `مادة ${id}`);
    name.append(el("small", "muted", ` · ${id}`));
    const actualCell = el("div", "", num(actualMark, 2));
    if (actualMark === null) actualCell.append(el("small", "muted", actualResultLabel(actual)));
    const predictedCell = el("div", "", num(predictedMark, 2));
    if (predictedMark === null) predictedCell.append(el("small", "muted", candidate ? "لا يوجد توقع لهذا السياق" : "خارج الخطة المرشحة"));
    const membership = !chosen ? "فعلية" : candidate && actual ? "مشتركة" : candidate ? "مرشحة فقط" : "فعلية فقط";
    return [name, membership, predictedCell, actualCell,
      predictedMark !== null && actualMark !== null ? signed(predictedMark - actualMark, 2) : "—"];
  });
  content.push(makeTable(["المادة", "وجودها في الخطتين", "التوقع ضمن الخطة المرشحة /100", "العلامة الفعلية /100", "الفرق (المتوقع − الفعلي)"], rows));
  replace(container, ...content);
}

function peerSupportCell(course) {
  const support = numeric(course.similar_peer_support);
  if (support === null) return "—";
  const minimum = numeric(course.peer_minimum_support) ?? 5;
  const lowSupport = course.peer_support_status === "LOW_SUPPORT" || support < minimum;
  return el("span", `peer-support${lowSupport ? " low-support" : ""}`, `${num(support, 0)} · ${lowSupport ? "دعم ضعيف" : "دعم كافٍ"}`);
}

function allPlans(experiment) {
  if (!experiment || predictionStatus(experiment) === "BLOCKED") return [];
  const plans = [...asArray(experiment.analytical_plans), ...asArray(experiment.plans), ...asArray(experiment.diagnostic_plans)];
  return [...new Map(plans.map((plan) => [planKey(plan), plan])).values()];
}
function predictionMap(experiment) {
  const result = new Map();
  if (!experiment || predictionStatus(experiment) === "BLOCKED") return result;
  for (const plan of allPlans(experiment)) for (const course of asArray(plan.courses)) if (!result.has(String(course.course_id))) result.set(String(course.course_id), course);
  // Explicit course_predictions are preferred to an arbitrary plan's context.
  const explicit = new Map();
  for (const course of asArray(experiment?.course_predictions)) if (!explicit.has(String(course.course_id))) explicit.set(String(course.course_id), course);
  for (const [id, course] of explicit) result.set(id, course);
  return result;
}
function predictionCell(course) {
  if (!course) return "—";
  const node = el("div"); node.append(el("span", "", `${num(course.expected_points, 3)} نقطة`), el("small", "muted", ` · رسوب ${pct(course.fail_probability)}`)); return node;
}

function renderCourseComparison(student) {
  const container = $("analysis-courses");
  const contexts = new Map();
  for (const id of EXPERIMENTS) for (const plan of allPlans(student.experiments?.[id])) if (planKey(plan)) contexts.set(planKey(plan), plan);
  if (!contexts.has(state.courseContext)) state.courseContext = contexts.keys().next().value || null;
  const maps = Object.fromEntries(EXPERIMENTS.map((id) => {
    const matched = allPlans(student.experiments?.[id]).find((plan) => planKey(plan) === state.courseContext);
    return [id, state.courseContext ? new Map(asArray(matched?.courses).map((course) => [String(course.course_id), course])) : predictionMap(student.experiments?.[id])];
  }));
  const ids = [...new Set(EXPERIMENTS.flatMap((id) => [...maps[id].keys()]))].sort();
  const content = [el("p", "comparison-note", "تظهر توقعات المادة نفسها ضمن مجموعة المواد نفسها، حتى عند اختلاف معرّف الخطة بين التجارب. الشرط (—) يعني أن التجربة لم تُنتج توقعاً لهذا السياق، ولا يُستبدل بصفر.")];
  if (contexts.size) {
    const label = el("label", "field-label", "سياق الخطة المشتركة للمقارنة"); label.htmlFor = "course-context";
    const select = el("select"); select.id = "course-context";
    for (const [key, plan] of contexts) select.append(new Option(`${plan.plan_id ?? "خطة"} · ${key.replaceAll("|", " / ")}`, key));
    select.value = state.courseContext;
    select.addEventListener("change", () => { state.courseContext = select.value; renderCourseComparison(student); });
    const field = el("div", "course-context-field"); field.append(label, select); content.push(field);
  }
  if (!ids.length) { content.push(el("p", "empty-small", "لا توجد توقعات مواد قابلة للمقارنة في هذا التشغيل.")); replace(container, ...content); return; }
  const rows = ids.map((id) => {
    const course = maps.A.get(id) || maps.B.get(id) || maps.C.get(id);
    const name = el("div", "", courseLabel(course)); name.append(el("small", "muted", ` · ${id}`));
    return [name, ...EXPERIMENTS.map((experiment) => predictionCell(maps[experiment].get(id)))];
  });
  content.push(makeTable(["المادة", "A · الأصلي", "B · تاريخ الجامعة", "C · المحسّن"], rows));
  content.push(el("p", "comparison-count", `${ids.length} مادة مميزة. المقارنة الرئيسية A مقابل C.`));
  const bestA = availablePlans(student.experiments?.A || {})[0]; const bestC = availablePlans(student.experiments?.C || {})[0];
  if (bestA && bestC) {
    const idsA = new Set(asArray(bestA.courses).map((course) => String(course.course_id)));
    const idsC = new Set(asArray(bestC.courses).map((course) => String(course.course_id)));
    const difference = el("div", "pair-difference");
    const groups = [["المواد المشتركة بين أفضل A وC", [...idsA].filter((id) => idsC.has(id))], ["فقط في أفضل A", [...idsA].filter((id) => !idsC.has(id))], ["فقط في أفضل C", [...idsC].filter((id) => !idsA.has(id))]];
    groups.forEach(([label, values]) => { const item = el("div"); item.append(el("h4", "", label), el("p", "", values.join("، ") || "لا توجد")); difference.append(item); });
    content.push(difference);
  }
  replace(container, ...content);
}

function samePlanMetric(plan, field, format = num) { return plan ? format(plan[field]) : "—"; }
function renderPlanComparison(student) {
  const container = $("analysis-plans");
  const perExperiment = Object.fromEntries(EXPERIMENTS.map((id) => [id, new Map(allPlans(student.experiments?.[id]).map((plan) => [planKey(plan), plan]))]));
  const keys = [...new Set(EXPERIMENTS.flatMap((id) => [...perExperiment[id].keys()]))].filter((key) => key && EXPERIMENTS.filter((id) => perExperiment[id].has(key)).length > 1);
  const content = [el("p", "comparison-note", "المطابقة حسب مجموعة معرّفات المواد، حتى عند اختلاف معرّف الخطة. تشمل النتائج التشخيصية مع تمييزها. لا تُستنتج مقارنة خطة بين تجارب لم تنتج توقعها.")];
  if (!keys.length) content.push(el("p", "empty-small", "لا توجد خطط متطابقة بتوقعات من تجربتين أو أكثر. قد يكون السبب عائقاً في التدريب أو المدخلات؛ راجع حالة التجارب."));
  else {
    const rows = [];
    const showCumulative = EXPERIMENTS.some((id) => allPlans(student.experiments?.[id]).some((plan) => cumulativeSupported(student.experiments?.[id], plan)));
    for (const key of keys) {
      for (const id of EXPERIMENTS) {
        const plan = perExperiment[id].get(key);
        if (!plan) continue;
        const row = [key.replaceAll("|", " · "), id, num(plan.expected_plan_gpa, 3)];
        if (showCumulative) row.push(cumulativeSupported(student.experiments?.[id], plan) ? num(plan.projected_cumulative_gpa, 3) : "—", cumulativeSupported(student.experiments?.[id], plan) ? signed(plan.expected_cumulative_gpa_gain) : "—");
        row.push(num(plan.expected_failed_credits, 2), plan.is_expected_cumulative_improvement === true ? "تحسن مثبت حسابياً" : "تشخيص / تحسن غير مثبت", validityLabel(plan));
        rows.push(row);
      }
    }
    content.push(makeTable(["المواد المتطابقة", "التجربة", "معدل الفصل", ...(showCumulative ? ["المعدل التراكمي", "التحسن"] : []), "ساعات الرسوب", "التصنيف", "الصلاحية"], rows));
  }
  replace(container, ...content);
}

function renderSupport(student) {
  const grid = el("div", "support-grid");
  for (const id of EXPERIMENTS) {
    const courses = [...predictionMap(student.experiments?.[id]).values()];
    const card = el("div", "support-card"); card.append(el("h3", "", `${id} · ${TITLES[id]}`));
    if (!courses.length) { card.append(el("p", "empty-small", "لا توجد توقعات أو معلومات دعم.")); grid.append(card); continue; }
    const levels = new Map(); let low = 0; let known = 0; let missing = 0;
    for (const course of courses) {
      const level = simple(course.course_history_fallback_level);
      levels.set(level, (levels.get(level) || 0) + 1);
      const support = numeric(course.course_history_effective_support);
      if (support !== null) { known += 1; if (support < 20) low += 1; } else missing += 1;
    }
    for (const [level, count] of [...levels].sort((left, right) => left[0].localeCompare(right[0], "en", {numeric: true}))) {
      const row = el("div", "support-bar-row"); const track = el("div", "bar-track"); const fill = el("span", "bar-fill"); fill.style.width = `${100 * count / courses.length}%`; track.append(fill); row.append(el("span", "", `L${level}`), track, el("span", "", count)); card.append(row);
    }
    const stat = el("div", "support-stat", "نسبة المواد ذات الدعم الفعّال < 20");
    stat.append(el("strong", "", known ? pct(low / known) : "—"), el("small", "", `${low} من ${known} مادة ذات دعم معلوم · ${missing} دون دعم مذكور`));
    card.append(stat, el("p", "help-text", "التوزيع حسب المواد المميزة في المخرجات المتاحة، مع تفضيل جدول توقعات المواد. لا تعني قلة الدعم فشلاً مؤكداً.")); grid.append(card);
  }
  replace($("analysis-support"), grid);
}

function renderMetadata(container, data) {
  function valueNode(value, depth) {
    if (depth > 7) return el("span", "", simple(value));
    if (Array.isArray(value)) {
      if (!value.length) return el("span", "muted", "لا توجد عناصر");
      const list = el("ul", "meta-list");
      value.forEach((entry) => { const item = el("li"); item.append(valueNode(entry, depth + 1)); list.append(item); });
      return list;
    }
    if (value && typeof value === "object") {
      const list = el("dl");
      for (const [key, entry] of Object.entries(value)) {
        const term = el("dt", "", key); const definition = el("dd");
        if (entry && typeof entry === "object") { const nested = el("details"); nested.append(el("summary", "", Array.isArray(entry) ? `${entry.length} عناصر` : "عرض التفاصيل"), valueNode(entry, depth + 1)); definition.append(nested); }
        else definition.append(valueNode(entry, depth + 1));
        list.append(term, definition);
      }
      return list;
    }
    return el("span", "", simple(value));
  }
  replace(container, valueNode(data, 0));
}

$("student-search").addEventListener("input", chooseStudent);
$("student-search").addEventListener("change", chooseStudent);
function switchCandidateView() {
  state.chosenPlan = null;
  state.courseContext = null;
  updateSelection();
  if (state.run) renderRun();
}
$("experiment-mode").addEventListener("change", switchCandidateView);
$("credit-experiment").addEventListener("change", switchCandidateView);
$("run-form").addEventListener("submit", startRun);
$("run-all").addEventListener("click", () => executeRun(state.students.map((student) => String(student.sample_id))));
$("refresh-runs").addEventListener("click", () => refreshRuns().catch((error) => showError(errorText(error))));
$("saved-runs").addEventListener("change", () => { $("load-run").disabled = state.busy || !$("saved-runs").value; });
$("load-run").addEventListener("click", async () => { showError(""); try { await loadRun($("saved-runs").value); } catch (error) { showError(errorText(error)); } });
document.querySelectorAll("[data-analysis]").forEach((button) => {
  button.addEventListener("click", () => {
    const active = button.dataset.analysis;
    document.querySelectorAll("[data-analysis]").forEach((tab) => { const selected = tab.dataset.analysis === active; tab.setAttribute("aria-selected", String(selected)); $(`analysis-${tab.dataset.analysis}`).hidden = !selected; });
  });
});

async function initialize() {
  const results = await Promise.allSettled([
    api("/api/students").then((payload) => { state.students = asArray(payload.students); renderStudents(); }),
    api("/api/status").then((payload) => renderMetadata($("system-status"), payload)),
    refreshRuns(),
  ]);
  const failures = results.filter((result) => result.status === "rejected").map((result) => errorText(result.reason));
  if (failures.length) showError(failures.join(" · "));
}
initialize();
