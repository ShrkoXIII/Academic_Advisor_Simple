"""HTTP integration uses synthetic records and an inference recording double."""
from copy import deepcopy
import importlib
from types import SimpleNamespace

import pytest
pytest.importorskip("fastapi", reason="Optional API dependencies are not installed.")
pytest.importorskip("httpx", reason="Optional API test dependencies are not installed.")
from fastapi.testclient import TestClient

from tests.api_fixtures import payloads, catalog, grade_scale
from tests.two_stage_fixtures import history_manager, new_history_delta


class Engine:
    def __init__(self, manager):
        self.history_manager = manager
        self.calls = []
        self.artifacts = SimpleNamespace(manifest={"stages": {"stage1": {"training_as_of_part": 20243},
                                                             "stage2": {"training_as_of_part": 20243}}})

    def recommend_from_payloads(self, **kwargs):
        self.calls.append(kwargs)
        return {"status": "no_feasible_plan", "recommendations": [],
                "metadata": {"student_id": "private", "skipped_history_bundles": [{"reason": "D:/private"}],
                             "candidate_count": len(kwargs["student_payload"]["candidates"]), "top_k": kwargs["top_k"]}}


def client(tmp_path, *, ready=True, **settings_values):
    settings = importlib.import_module("src.api.settings").ApiSettings(service_key="service", admin_key="admin", **settings_values)
    manager = history_manager(tmp_path)
    engine = Engine(manager) if ready else None
    request = payloads(complete=True)
    api = importlib.import_module("src.api.service").ApiService(settings=settings, catalog=catalog(request),
                 grade_scale=grade_scale(), history_manager=manager if ready else None, engine=engine)
    app = importlib.import_module("src.api.app").create_app(service=api)
    return TestClient(app), api, engine, request


def student_request(request):
    return {key: value for key, value in request.items() if key not in {"courses_api_response", "target_credits", "history_as_of_part"}}


def course_request(request):
    return {key: value for key, value in request.items() if key not in {"student_api_response", "target_credits", "history_as_of_part"}}


def post(c, path, payload, key="service"):
    return c.post(path, json=payload, headers={"X-API-Key": key})


def test_http_health_and_validators_survive_unready_models_and_history(tmp_path):
    c, api, _, request = client(tmp_path, ready=False)
    health = c.get("/health").json()
    assert health["api_health"] == "healthy"
    assert health["model_readiness"]["ready"] is False
    assert health["history_readiness"]["ready"] is False
    assert post(c, "/api/v1/inputs/student/validate", student_request(request)).status_code == 200
    assert post(c, "/api/v1/inputs/courses/validate", course_request(request)).json()["summary"]["candidate_count"] == 17
    assert post(c, "/api/v1/recommendations", request).status_code == 503


@pytest.mark.parametrize("component", ["student", "courses"])
@pytest.mark.parametrize("field,value", [("student_id", "other"), ("degree_id", "other"), ("part_id", 20252)])
def test_http_context_conflicts_make_zero_engine_calls(tmp_path, component, field, value):
    c, _, engine, request = client(tmp_path)
    request["source_contexts"][component][field] = value
    assert post(c, "/api/v1/recommendations", request).status_code == 422
    assert engine.calls == []


def test_missing_courses_context_and_payload_identity_conflict_stop_inference(tmp_path):
    c, _, engine, request = client(tmp_path)
    request["source_contexts"].pop("courses")
    assert post(c, "/api/v1/recommendations", request).status_code == 422
    request = payloads(complete=True)
    request["courses_api_response"]["data"]["availableCourses"][0].update(DEGREE_ID="other", ALLOW_REGISTER="N")
    assert post(c, "/api/v1/recommendations", request).status_code == 422
    assert engine.calls == []


def test_performance_limit_is_configurable_and_never_truncates_validation(tmp_path):
    c, _, engine, request = client(tmp_path, performance_test_mode=True, performance_test_max_candidates=16)
    assert post(c, "/api/v1/recommendations", request).status_code == 422
    assert engine.calls == []
    assert post(c, "/api/v1/inputs/courses/validate", course_request(request)).json()["summary"]["candidate_count"] == 17


@pytest.mark.parametrize("test_mode,limit", [(False, 1), (True, 20), (True, 17)])
def test_config_limit_applies_only_in_test_mode(tmp_path, test_mode, limit):
    c, _, engine, request = client(tmp_path, performance_test_mode=test_mode, performance_test_max_candidates=limit)
    response = post(c, "/api/v1/recommendations", request)
    assert response.status_code == 200, response.text
    assert len(engine.calls[0]["student_payload"]["candidates"]) == 17
    assert engine.calls[0]["top_k"] == 3
    assert "private" not in response.text


@pytest.mark.parametrize("enabled,mode,expected", [(False, "normal", 422), (True, "normal", 422),
                                                  (False, "backtesting", 422), (True, "backtesting", 200)])
def test_stale_cutoff_requires_both_explicit_and_enabled_backtesting(tmp_path, enabled, mode, expected):
    history_manager(tmp_path, part=20242)
    c, _, engine, request = client(tmp_path, enable_backtesting=enabled)
    request.update(history_as_of_part=20242, mode=mode)
    response = post(c, "/api/v1/recommendations", request)
    assert response.status_code == expected, response.text
    assert bool(engine.calls) == (expected == 200)
    if expected == 200:
        assert response.json()["metadata"]["mode"] == "backtesting"
        assert response.json()["metadata"]["history_as_of_part"] == 20242


def test_target_history_and_training_cutoff_forbidden(tmp_path):
    c, _, engine, request = client(tmp_path, enable_backtesting=True)
    request.update(history_as_of_part=20251, mode="backtesting")
    assert post(c, "/api/v1/recommendations", request).status_code == 422
    request.update(part_id=20243, history_as_of_part=20242)
    for context in request["source_contexts"].values():
        context["part_id"] = 20243
    assert post(c, "/api/v1/recommendations", request).status_code == 422
    request = payloads(complete=True)
    engine.artifacts.manifest["stages"]["stage1"]["training_as_of_part"] = 20251
    response = post(c, "/api/v1/recommendations", request)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "TRAINING_CUTOFF_OVERLAP"
    assert engine.calls == []


def test_admin_delta_validation_is_partial_without_history_and_never_publishes(tmp_path):
    c, _, _, _ = client(tmp_path, ready=False)
    core = new_history_delta()
    body = {"part_id": core["delta_part"], "rows": core["aggregates"]}
    assert post(c, "/api/v1/history/deltas/validate", body).status_code == 403
    response = post(c, "/api/v1/history/deltas/validate", body, key="admin")
    assert response.status_code == 200
    assert response.json()["validation_status"] == "partial"
    assert response.json()["checks"]["aggregates"] == "verified"
    assert not (tmp_path / "as_of_20251").exists()


def test_auth_keys_errors_and_sensitive_inputs_never_echoed(tmp_path):
    c, _, engine, request = client(tmp_path)
    path = "/api/v1/recommendations"
    assert c.post(path, json=request).status_code == 401
    request["student_id"] = {"secret": "PII_CANARY"}
    request["unexpected"] = "D:/private/PII_CANARY"
    response = post(c, path, request)
    assert response.status_code == 422
    assert "PII_CANARY" not in response.text and "D:/private" not in response.text
    assert engine.calls == []


def test_credit_bounds_use_actual_upper_intersection(tmp_path):
    c, _, engine, request = client(tmp_path)
    request.pop("target_credits")
    request.update(min_credits=12, max_credits=30)
    assert post(c, "/api/v1/recommendations", request).status_code == 200
    assert engine.calls[0]["request_payload"]["target_credits"] == 25


def test_http_numeric_literals_keep_decimal_precision(tmp_path):
    c, _, engine, request = client(tmp_path)
    request.pop("target_credits")
    request.update(min_credits="12.0000000000000000000000000001", max_credits="12")
    import json
    raw = json.dumps(request).replace('"12.0000000000000000000000000001"', '12.0000000000000000000000000001')
    response = c.post("/api/v1/recommendations", content=raw, headers={"X-API-Key": "service", "Content-Type": "application/json"})
    assert response.status_code == 422
    assert not engine.calls


@pytest.mark.parametrize("key", ["IS_REQUESTABLE", "ALLOW_REGISTER"])
def test_invalid_structured_eligibility_is_422_not_server_error(tmp_path, key):
    c, _, engine, request = client(tmp_path)
    request["courses_api_response"]["data"]["availableCourses"][0][key] = {"private": "PII_CANARY"}
    response = post(c, "/api/v1/recommendations", request)
    assert response.status_code == 422 and "PII_CANARY" not in response.text
    assert not engine.calls


def test_runtime_exception_does_not_escape_to_server_logs(tmp_path, caplog):
    c, api, _, request = client(tmp_path)
    def broken(value):
        raise RuntimeError("PII_CANARY D:/private")
    api.validate_student = broken
    response = post(c, "/api/v1/inputs/student/validate", student_request(request))
    assert response.status_code == 500
    assert "PII_CANARY" not in response.text and "PII_CANARY" not in caplog.text


def test_invalid_target_status_key_is_422(tmp_path):
    c, _, engine, request = client(tmp_path)
    request["student_api_response"]["data"]["studentDegreeInfo"]["STUDENT_STATUS_ID"] = {"private": "PII_CANARY"}
    response = post(c, "/api/v1/recommendations", request)
    assert response.status_code == 422
    assert not engine.calls


def test_missing_exact_bundle_is_503_with_no_fallback(tmp_path):
    c, _, engine, request = client(tmp_path, enable_backtesting=True)
    request.update(mode="backtesting", history_as_of_part=20242)
    response = post(c, "/api/v1/recommendations", request)
    assert response.status_code == 503
    assert not engine.calls


def test_empty_candidates_return_no_feasible_plan_with_actual_core(tmp_path):
    from tests.test_api_integration import api_engine
    api, artifacts, request = api_engine(tmp_path)
    for row in request["courses_api_response"]["data"]["availableCourses"]:
        row["ALLOW_REGISTER"] = "N"
    response = api.recommend(request)
    assert response["status"] == "no_feasible_plan"
    assert not artifacts.stage1.grade_model.matrices
