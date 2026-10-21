"""Static dashboard integration boundaries; API behavior is tested separately."""
from html.parser import HTMLParser
from pathlib import Path
import re
import shutil
import subprocess

import pytest


STATIC = Path(__file__).resolve().parents[1] / "tools" / "recommendation_pilot_20251" / "static"


class DashboardHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.resources = []
        self.inline_handlers = []
        self.html_attributes = {}
        self.script_sources = []
        self.elements = {}
        self.ancestors = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "html":
            self.html_attributes = attrs
        if "id" in attrs:
            self.ids.append(attrs["id"])
            self.elements[attrs["id"]] = (tag, attrs, list(self.ancestors))
        if tag in {"script", "link", "img", "iframe"}:
            self.resources.extend(attrs[key] for key in ("src", "href") if key in attrs)
        if tag == "script":
            self.script_sources.append(attrs.get("src"))
        self.inline_handlers.extend(key for key in attrs if key.startswith("on"))
        if tag not in {"input", "meta", "link", "img", "br", "hr"}:
            self.ancestors.append((tag, attrs))

    def handle_endtag(self, tag):
        for index in range(len(self.ancestors) - 1, -1, -1):
            if self.ancestors[index][0] == tag:
                self.ancestors = self.ancestors[:index]
                return


def read_dashboard():
    parser = DashboardHTML()
    parser.feed((STATIC / "index.html").read_text(encoding="utf-8"))
    return parser


def test_arabic_rtl_dashboard_has_unique_resolvable_controls():
    """Every fixed JS control resolves to one actual HTML element."""
    parsed = read_dashboard()
    assert parsed.html_attributes["lang"] == "ar"
    assert parsed.html_attributes["dir"] == "rtl"
    assert len(parsed.ids) == len(set(parsed.ids))
    script = (STATIC / "app.js").read_text(encoding="utf-8")
    selectors = re.findall(r'\$\("([\w-]+)"\)', script)
    assert selectors
    assert set(selectors) <= set(parsed.ids)


def test_dashboard_resources_are_local_and_api_data_is_not_html():
    """Saved API text cannot become executable markup or remote resources."""
    parsed = read_dashboard()
    assert parsed.resources
    for resource in parsed.resources:
        assert resource.startswith("/static/")
        assert (STATIC / resource.removeprefix("/static/")).is_file()
    assert all(parsed.script_sources)
    assert not parsed.inline_handlers
    script = (STATIC / "app.js").read_text(encoding="utf-8")
    assert not re.search(r"\b(?:innerHTML|outerHTML|insertAdjacentHTML|eval)\b", script)
    assert "textContent" in script


def test_dashboard_javascript_parses():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js unavailable for JavaScript syntax verification")
    checked = subprocess.run([node, "--check", str(STATIC / "app.js")], capture_output=True, text=True)
    assert checked.returncode == 0, checked.stderr


def test_primary_student_picker_is_single_searchable_control_and_batch_is_separate():
    parsed = read_dashboard()
    tag, attributes, _ = parsed.elements["student-search"]
    assert tag == "input" and attributes["type"] == "search"
    assert attributes["list"] == "student-options"
    assert parsed.elements["student-options"][0] == "datalist"
    assert not {"student-tabs", "student-list", "select-all", "clear-selection"} & set(parsed.ids)
    _, _, ancestors = parsed.elements["run-all"]
    assert any(tag == "details" and "open" not in attrs for tag, attrs in ancestors)
    assert not any(attrs.get("id") == "run-form" for _, attrs in ancestors)


def test_technical_validation_and_source_codes_are_initially_collapsed():
    parsed = read_dashboard()
    for identifier in ("student-issues", "experiment-technical", "technical-error", "system-status", "run-metadata", "analysis-support", "plan-technical"):
        _, _, ancestors = parsed.elements[identifier]
        assert any(tag == "details" and attrs.get("class") == "panel technical-panel" and "open" not in attrs for tag, attrs in ancestors)


def run_dashboard_scenario(scenario):
    """Exercise actual render functions in a small text-only DOM; no browser or API writes."""
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js unavailable for dashboard behavior verification")
    harness = r'''
const fs = require("fs");
const vm = require("vm");
const assert = require("assert");
class TextNode {
  constructor(tag = "div") { this.tagName = tag; this.children = []; this.attributes = {}; this.dataset = {}; this.style = {}; this.events = {}; this.value = ""; this._text = ""; }
  append(...nodes) { this.children.push(...nodes); }
  replaceChildren(...nodes) { this.children = nodes; this._text = ""; }
  setAttribute(name, value) { this.attributes[name] = value; }
  addEventListener(name, handler) { this.events[name] = handler; }
  reportValidity() { return true; }
  set textContent(value) { this._text = String(value); this.children = []; }
  get textContent() { return this._text + this.children.map(node => node.textContent ?? String(node)).join(" "); }
}
class Option extends TextNode { constructor(label, value) { super("option"); this.textContent = label; this.value = value; } }
const controls = new Map();
const document = {getElementById: id => { if (!controls.has(id)) controls.set(id, new TextNode()); return controls.get(id); }, createElement: tag => new TextNode(tag), querySelectorAll: () => []};
const source = fs.readFileSync(process.argv[1], "utf8").replace(/\ninitialize\(\);\s*$/, "");
vm.runInNewContext(source + "\n" + process.argv[2], {document, Node: TextNode, Option, assert, console, setTimeout});
'''
    checked = subprocess.run([node, "-e", harness, str(STATIC / "app.js"), scenario], capture_output=True, text=True, encoding="utf-8")
    assert checked.returncode == 0, checked.stderr


def test_real_prediction_cards_are_visible_without_cumulative_or_registration_approval():
    run_dashboard_scenario('''
const plan = {expected_plan_gpa: 3.2, total_credits: 18, projected_cumulative_gpa: 3.4, expected_cumulative_gpa_gain: 0.2, courses: [{course_id: "7", course_name: "الرياضيات", course_credits: 3, expected_points: 3.2}]};
const experiment = {prediction_status: "PREDICTION_AVAILABLE", plan_status: "PROVISIONAL_PLAN", cumulative_gpa_status: "UNAVAILABLE", analytical_plans: [plan], reason: "DEGREE_CREDITS_COUNT_UNAVAILABLE", reason_ar: "صلاحية التسجيل غير مؤكدة"};
const rendered = renderExperiment("A", experiment).textContent;
assert(rendered.includes("التوقعات متاحة"));
assert(rendered.includes("خطة تحليلية مؤقتة"));
assert(rendered.includes("3.200"));
assert(rendered.includes("الرياضيات"));
assert(!rendered.includes("3.400"));
assert(!rendered.includes("DEGREE_CREDITS_COUNT_UNAVAILABLE"));
assert(!rendered.includes("تم التحقق من التسجيل"));
assert(renderExperiment("A", {...experiment, cumulative_gpa_status: "AVAILABLE"}).textContent.includes("3.400"));
assert(!renderExperiment("A", {...experiment, prediction_status: "BLOCKED"}).textContent.includes("3.200"));
assert(renderExperiment("A", {status: "BLOCKED", diagnostic_plans: [plan]}).textContent.includes("التوقعات متاحة"));
''')


def test_single_picker_browses_saved_batch_students_without_rerunning():
    run_dashboard_scenario('''
state.students = [{sample_id: "s1", student_id: 101, previous_gpa: 4.9, student_summary: {start_agpa_points: 2.75}}, {sample_id: "s2", student_id: 102, student_summary: {start_agpa_points: null}}];
state.run = {student_results: [{sample_id: "s1", student_id: 101, experiments: {}}, {sample_id: "s2", student_id: 102, experiments: {}}]};
$("student-search").value = "s1";
chooseStudent();
assert.strictEqual(state.selectedSample, "s1");
assert.strictEqual(state.activeStudent, 0);
assert($("selected-student-summary").textContent.includes("2.750"));
assert(!$("selected-student-summary").textContent.includes("4.900"));
$("student-search").value = "102";
chooseStudent();
assert.strictEqual(state.selectedSample, "s2");
assert.strictEqual(state.activeStudent, 1);
assert($("selected-student-summary").textContent.includes("غير متوفر"));
assert($("student-overview").textContent.includes("102"));
$("student-search").value = "unknown";
chooseStudent();
assert.strictEqual(state.selectedSample, null);
assert.strictEqual($("results").hidden, true);
assert.strictEqual($("run-button").disabled, true);
''')


def test_c_course_details_distinguish_weak_peer_support_from_sufficient_support():
    run_dashboard_scenario('''
state.chosenPlan = {experimentId: "C", diagnostic: true, plan: {courses: [
  {course_id: 1, course_name: "دعم قليل", expected_points: 2.9, peer_expected_points: 2.55, similar_peer_support: 4, peer_minimum_support: 5, peer_support_status: "LOW_SUPPORT"},
  {course_id: 2, course_name: "دعم كاف", expected_points: 3.1, peer_expected_points: 3.35, similar_peer_support: 5, peer_minimum_support: 5, peer_support_status: "SUFFICIENT"},
  {course_id: 3, course_name: "تاريخ غير متوفر", expected_points: 3.0, peer_expected_points: null, similar_peer_support: null}
]}};
renderPlanDetail();
const text = $("plan-detail").textContent;
assert(text.includes("نقاط الأقران التاريخية"));
assert(text.includes("2.550"));
assert(text.includes("3.350"));
assert(text.includes("4 · دعم ضعيف"));
assert(text.includes("5 · دعم كافٍ"));
assert(!text.includes("LOW_SUPPORT"));
assert(!text.includes("SUFFICIENT"));
assert(!text.includes("null"));
assert.strictEqual(peerSupportCell({similar_peer_support: null}), "—");
assert(peerSupportCell({similar_peer_support: 0}).textContent.includes("0 · دعم ضعيف"));
''')


def test_peer_statistics_are_not_invented_for_a_b_or_old_c_results():
    run_dashboard_scenario('''
for (const id of ["A", "B", "C"]) {
  state.chosenPlan = {experimentId: id, plan: {courses: [{course_id: 1, course_name: "الرياضيات", expected_points: 2.9}]}};
  renderPlanDetail();
  assert(!$("plan-detail").textContent.includes("نقاط الأقران التاريخية"));
  assert(!$("plan-detail").textContent.includes("دعم ضعيف"));
}
for (const id of ["A", "B"]) {
  state.chosenPlan = {experimentId: id, plan: {courses: [{course_id: 1, expected_points: 2.9, similar_peer_support: 20, peer_expected_points: 3.5}]}};
  renderPlanDetail();
  assert(!$("plan-detail").textContent.includes("نقاط الأقران التاريخية"));
  assert(!$("plan-detail").textContent.includes("3.500"));
}
''')


def test_actual_overlap_counts_use_unique_course_ids_and_do_not_count_unavailable_as_zero():
    run_dashboard_scenario('''
const actual = {status: "PARTIAL", course_count: 3, courses: [{course_id:"1"}, {course_id:"2"}, {course_id:"3"}]};
const plan = {courses: [{course_id:1}, {course_id:"1"}, {course_id:"2"}, {course_id:"4"}]};
const comparison = compareObservedPlan(plan, actual);
assert.strictEqual(comparison.sharedCount, 2);
assert.strictEqual(comparison.candidateCount, 3);
assert.strictEqual(comparison.actualCount, 3);
assert.strictEqual(comparison.candidateOnly.length, 1);
assert.strictEqual(comparison.actualOnly.length, 1);
assert.strictEqual(comparison.exactMatch, false);
assert.strictEqual(compareObservedPlan(plan, {status:"UNAVAILABLE",courses:[]}), null);
const exact = compareObservedPlan({courses:[{course_id:3},{course_id:2},{course_id:1}]}, actual);
assert.strictEqual(exact.exactMatch, true);
state.run = {student_results:[{observed_plan:actual}]}; state.activeStudent=0;
const card = renderPlanCard("A", {...plan,expected_plan_gpa:3},0,true,{}).textContent;
assert(card.includes("المشترك مع خطة الطالب"));
assert(card.includes("2 من 3"));
''')


def test_actual_course_table_preserves_plan_context_missing_grades_and_actual_zero():
    run_dashboard_scenario('''
const student = {observed_plan: {status:"PARTIAL",course_count:3,total_credits:9,graded_course_count:2,part_id:20251,courses:[
 {course_id:"1",course_name:"مشترك بصفر",actual_mark:0,actual_points:0,result_status:"AVAILABLE"},
 {course_id:"2",course_name:"دون علامة",actual_mark:null,result_status:"NO_FINAL_RESULT"},
 {course_id:"3",course_name:"فعلية فقط",actual_mark:88,result_status:"AVAILABLE"}
]}};
state.run={student_results:[student]};state.activeStudent=0;
state.chosenPlan={experimentId:"C",plan:{courses:[
 {course_id:"1",course_name:"مشترك بصفر",predicted_mark:75,expected_points:2.75},
 {course_id:"2",course_name:"دون علامة",predicted_mark:70,expected_points:2.5},
 {course_id:"4",course_name:"مرشحة فقط",predicted_mark:99,expected_points:4}
]}};
renderObservedComparison(student);
const text=$("observed-comparison").textContent;
assert(text.includes("75.00"));assert(text.includes("0.00"));assert(text.includes("+75.00"));
assert(text.includes("88.00"));assert(text.includes("مرشحة فقط"));assert(text.includes("فعلية فقط"));
assert(text.includes("لا توجد علامة نهائية"));assert(!text.includes("null"));
assert(text.includes("المتوقع − الفعلي"));assert(text.includes("سياق الخطة المرشحة"));
state.chosenPlan=null;renderObservedComparison(student);
assert($("observed-comparison").textContent.includes("اختر خطة"));
assert(!$("observed-comparison").textContent.includes("75.00"));
renderObservedComparison({observed_plan:{status:"UNAVAILABLE",reason_ar:"التسجيل غير متوفر"}});
assert($("observed-comparison").textContent.includes("التسجيل غير متوفر"));
assert(!$("observed-comparison").textContent.includes("0 من"));
''')


def test_actual_plan_forecasts_use_dedicated_full_plan_scores_in_every_system():
    run_dashboard_scenario('''
const observed = {status:"AVAILABLE",course_count:1,total_credits:3,graded_course_count:1,courses:[{course_id:"c",course_name:"المادة الفعلية",actual_mark:85}]};
const forecasts = {context:"actual_registered_plan",experiments:{
 A:{prediction_status:"PREDICTION_AVAILABLE",expected_plan_gpa:2.5,course_predictions:[{course_id:"c",predicted_mark:61}]},
 B:{prediction_status:"PREDICTION_AVAILABLE",expected_plan_gpa:3.0,course_predictions:[{course_id:"c",predicted_mark:72}]},
 C:{prediction_status:"BLOCKED",reason_ar:"نموذج غير متوافق",course_predictions:[]}
}};
const student = {observed_plan:observed,observed_plan_prediction:forecasts,experiments:{
 A:{prediction_status:"PREDICTION_AVAILABLE",analytical_plans:[{courses:[{course_id:"c",predicted_mark:99}]}]}}};
state.chosenPlan = {experimentId:"A",plan:{courses:[{course_id:"c",predicted_mark:98}]}};
renderActualPlanForecasts(student);
const text = $("actual-plan-forecasts").textContent;
assert(text.includes("61.00"));assert(text.includes("72.00"));assert(text.includes("85.00"));
assert(!text.includes("99.00"));assert(!text.includes("98.00"));assert(text.includes("نموذج غير متوافق"));
const card = renderExperiment("A", {status:"NO_MATCHING_PLAN"}, forecasts.experiments.A, observed).textContent;
assert(card.includes("توقعات مواد الطالب الفعلية"));assert(card.includes("61.00"));assert(card.includes("85.00"));
assert(card.includes("2.500"));
state.chosenPlan=null;renderActualPlanForecasts(student);
assert($("actual-plan-forecasts").textContent.includes("61.00"));
renderObservedComparison(student);
const noCandidate = $("observed-comparison").textContent;
assert(noCandidate.includes("توقع A /100"));assert(noCandidate.includes("توقع B /100"));assert(noCandidate.includes("توقع C /100"));
assert(noCandidate.includes("61.00"));assert(noCandidate.includes("72.00"));assert(noCandidate.includes("85.00"));
assert(!noCandidate.includes("99.00"));assert(!noCandidate.includes("98.00"));
state.chosenPlan={experimentId:"A",plan:{courses:[{course_id:"other",predicted_mark:90}]}};
renderObservedComparison(student);
assert($("observed-comparison").textContent.includes("خارج الخطة المرشحة"));
renderActualPlanForecasts({observed_plan:observed});
assert(!$("actual-plan-forecasts").textContent.includes("99.00"));
''')
