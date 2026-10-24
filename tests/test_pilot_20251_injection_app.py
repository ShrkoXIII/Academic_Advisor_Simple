"""Diagnostic-only endpoint isolation and reuse of the existing Pilot dashboard."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from tools.recommendation_pilot_20251.app import create_app
from tools.recommendation_pilot_20251.runner import RunStore
from tests.test_pilot_20251_dashboard import run_dashboard_scenario


class NoPredictionOnRead:
    def predict(self, *args, **kwargs):
        raise AssertionError("Reading a saved diagnostic must not predict")

    def predict_many(self, *args, **kwargs):
        raise AssertionError("Reading a saved diagnostic must not predict")


class DiagnosticRunner:
    def __init__(self, root):
        self.store = RunStore(root / "experiments" / "actual_candidate_injection")
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.calls = []

    def start(self, sample_ids, **options):
        if "unknown" in sample_ids:
            raise ValueError("Unknown primary sample.")
        self.calls.append((sample_ids, options))
        return "run_diagnostic"

    def progress(self, run_id):
        if run_id != "run_diagnostic":
            raise ValueError("Run not found.")
        return {"run_id": run_id, "status": "completed", "completed": 4, "total": 4}


@pytest.fixture
def diagnostic_app(tmp_path):
    runner = DiagnosticRunner(tmp_path)
    row = {"sample_id": "sample-1", "student_id": "123", "candidate_mode": "augmented",
           "credit_experiment": "fixed_18", "experiments": {},
           "observed_plan_prediction": {"context": "actual_registered_plan", "saved_value": 71}}
    runner.store.save("run_diagnostic", {"run_id": "run_diagnostic", "status": "completed"}, [row], {})
    app = create_app(tmp_path, actual_candidate_runner=runner, observed_predictor=NoPredictionOnRead())
    with TestClient(app, base_url="http://127.0.0.1") as client:
        yield app, client, runner


def test_diagnostic_routes_save_and_read_separately_without_reprediction(diagnostic_app):
    app, client, runner = diagnostic_app
    original = {file.name: file.read_bytes() for file in runner.store.directory("run_diagnostic").iterdir()}
    assert app.state.runner.store.root != runner.store.root
    response = client.post("/api/actual-candidate-runs", json={"sample_ids": ["sample-1"], "max_plans": 2000})
    assert response.status_code == 202
    assert runner.calls == [(["sample-1"], {"candidate_modes": ["original", "augmented"],
                                         "credit_experiments": ["fixed_18", "actual_load"], "max_plans": 2000})]
    assert client.get("/api/actual-candidate-runs").json()["runs"][0]["run_id"] == "run_diagnostic"
    assert client.get("/api/actual-candidate-runs/run_diagnostic/progress").json()["completed"] == 4
    for _ in range(2):
        saved = client.get("/api/actual-candidate-runs/run_diagnostic")
        assert saved.status_code == 200
        assert saved.json()["student_results"][0]["observed_plan_prediction"]["saved_value"] == 71
    assert client.get("/api/runs").json()["runs"] == []
    assert original == {file.name: file.read_bytes() for file in runner.store.directory("run_diagnostic").iterdir()}


@pytest.mark.parametrize("change", [
    {"candidate_modes": ["production"]}, {"candidate_modes": ["original", "original"]},
    {"credit_experiments": ["actual_load", "actual_load"]}, {"credit_experiments": ["unbounded"]},
    {"max_plans": True}, {"max_plans": 2001}, {"target_credits": 21},
    {"sample_ids": ["sample-1", "sample-1"]}, {"sample_ids": ["unknown"]},
])
def test_diagnostic_endpoint_rejects_invalid_modes_and_budgets(diagnostic_app, change):
    _, client, runner = diagnostic_app
    assert client.post("/api/actual-candidate-runs", json={"sample_ids": ["sample-1"], **change}).status_code == 422
    assert not runner.calls


def test_diagnostic_routes_keep_loopback_same_origin_policy(diagnostic_app):
    _, client, _ = diagnostic_app
    assert client.get("/api/actual-candidate-runs", headers={"host": "foreign.example"}).status_code == 403
    assert client.post("/api/actual-candidate-runs", json={"sample_ids": ["sample-1"]},
                       headers={"origin": "https://foreign.example"}).status_code == 403
    assert client.get("/api/actual-candidate-runs/run_unknown").status_code == 404
    assert client.get("/api/actual-candidate-runs/run_unknown/progress").status_code == 404


def test_dashboard_diagnostic_controls_and_exact_warning_are_present():
    static = Path(__file__).resolve().parents[1] / "tools/recommendation_pilot_20251/static"
    html = (static / "index.html").read_text(encoding="utf-8")
    for expected in ["experiment-mode", "compare-candidates", "credit-experiment", "candidate-mode-comparison",
                     "DIAGNOSTIC ONLY — ACTUAL COURSES WERE INJECTED", "DIAGNOSTIC_ACTUAL_COURSE_INJECTION"]:
        assert expected in html
    script = (static / "app.js").read_text(encoding="utf-8")
    assert "/api/actual-candidate-runs" in script
    assert 'credit_experiments: ["fixed_18", "actual_load"]' in script


def test_dashboard_switches_existing_abc_cards_by_mode_and_credit_test():
    run_dashboard_scenario('''
const actual = {status:"AVAILABLE",total_credits:21,courses:[{course_id:"10"},{course_id:"20"}]};
function row(mode, credit) {return {sample_id:"s1",student_id:123,candidate_mode:mode,credit_experiment:credit,target_credits:credit==="fixed_18"?18:21,
 candidate_coverage:{actual_course_count:2,original_candidate_count:3,augmented_candidate_count:4,injected_course_count:mode==="augmented"?1:0,
 actual_in_candidates_before:1,actual_in_candidates_after:mode==="augmented"?2:1,coverage_before:0.5,coverage_after:mode==="augmented"?1:0.5,
 injected_courses:mode==="augmented"?[{course_id:"20",course_name:"المادة المحقونة"}]:[]},
 observed_plan:actual,experiments:{A:{prediction_status:"PREDICTION_AVAILABLE",analytical_plans:[{expected_plan_gpa:mode==="augmented"?3.5:2.5,total_credits:18,courses:[{course_id:"10"}]}]}},
 recommendation_metrics:{A:{top1_actual_overlap:1,top3_union_actual_overlap:1,actual_plan_examined:false}},
 search:{evaluated_plan_count:200,visited_search_states:2020,truncated:true}};}
state.students=[{sample_id:"s1",student_id:123}];state.selectedSample="s1";
state.run={student_results:[row("original","fixed_18"),row("augmented","fixed_18"),row("original","actual_load"),row("augmented","actual_load")]};
$("experiment-mode").value="original";$("credit-experiment").value="fixed_18";renderRun();
assert.strictEqual(state.activeStudent,0);assert($("experiment-grid").textContent.includes("2.500"));
assert($("candidate-mode-comparison").textContent.includes("3.500"));
assert($("candidate-mode-comparison").textContent.includes("2020"));
assert.strictEqual($("diagnostic-warning").hidden,false);
$("experiment-mode").value="augmented";switchCandidateView();
assert.strictEqual(state.activeStudent,1);assert($("experiment-grid").textContent.includes("3.500"));
assert($("candidate-coverage").textContent.includes("المادة المحقونة"));
assert($("candidate-coverage").textContent.includes("UNVERIFIED"));
$("credit-experiment").value="actual_load";switchCandidateView();
assert.strictEqual(state.activeStudent,3);assert($("candidate-coverage").textContent.includes("ليس قرار توصية مستقل"));
assert.strictEqual(compareObservedPlan({total_credits:18,courses:actual.courses},actual).exactMatch,false);
''')


def test_dashboard_separates_observed_prediction_errors_from_recommendations():
    run_dashboard_scenario('''
renderActualPlanForecasts({candidate_mode:"augmented",observed_plan:{status:"AVAILABLE",courses:[{course_id:"10",actual_mark:81}]},
 observed_plan_prediction:{context:"actual_registered_plan",experiments:{A:{prediction_status:"PREDICTION_AVAILABLE",course_predictions:[{course_id:"10",predicted_mark:72}]}}},
 prediction_metrics:{A:{course_count:1,mae:9,rmse:9,bias:-9,fail_brier:0.1234,fail_log_loss:0.2,fail_roc_auc:null}}});
const content=$("actual-plan-forecasts").textContent;
assert(content.includes("تقييم توقع العلامات على الخطة الفعلية"));
assert(content.includes("MAE"));assert(content.includes("0.1234"));assert(content.includes("-9.000"));
assert(content.includes("لا تقيس جودة الخطط الجديدة"));assert(!content.includes("null"));
''')


def test_plan_source_uses_injection_provenance_when_scored_courses_omit_annotations():
    run_dashboard_scenario('''
state.run={student_results:[{candidate_mode:"augmented",candidate_coverage:{candidate_provenance:{"1423.111":{candidate_source:"ACTUAL_INJECTED"},"10":{candidate_source:"API"}}}}]};
state.activeStudent=0;state.chosenPlan={experimentId:"A",plan:{courses:[{course_id:"01423.1110",course_name:"المحقونة",predicted_mark:75},{course_id:10,course_name:"الأصلية"}]}};
renderPlanDetail();const rendered=$("plan-detail").textContent;
assert(rendered.includes("ACTUAL_INJECTED"));assert(rendered.includes("API"));
assert.strictEqual(candidateSource({course_id:"missing"}),"غير موثّق");
''')
