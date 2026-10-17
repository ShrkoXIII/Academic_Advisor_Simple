"""Split ingestion reuses synthetic API fixtures and the existing engine path."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import replace
from decimal import Decimal
from threading import Barrier, Event

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.api.service import ApiService
from src.api.settings import ApiSettings
from tests.test_api_http import client, post
from tests.test_api_integration import api_engine


PREFIX = "/api/v1/recommendation-inputs/"
LOOKUP = "/api/v1/recommendation-requests/"


def split(request, request_id="synthetic-rec-001"):
    identity = {key: request[key] for key in ("student_id", "degree_id", "part_id")}
    student = {**identity, "request_id": request_id, "student_api_response": deepcopy(request["student_api_response"]),
               "source_contexts": {"student": deepcopy(request["source_contexts"]["student"])},
               "integration_context": {key: deepcopy(value) for key, value in request["integration_context"].items()
                                       if key in {"student_values", "total_reg_credits_source"}},
               "recommendation": {key: request[key] for key in
                                  ("history_as_of_part", "target_credits", "min_credits", "max_credits", "top_k", "mode")
                                  if key in request}}
    courses = {**identity, "request_id": request_id, "courses_api_response": deepcopy(request["courses_api_response"]),
               "source_contexts": {"courses": deepcopy(request["source_contexts"]["courses"])},
               "integration_context": {key: deepcopy(value) for key, value in request["integration_context"].items()
                                       if key in {"previous_course_statuses", "registration_policy"}}}
    return {"student": student, "courses": courses}


def setup(tmp_path, **settings):
    return client(tmp_path / "history", request_store_path=tmp_path / "requests" / "requests.sqlite3", **settings)


@pytest.mark.parametrize("first", ["student", "courses"])
def test_either_order_pending_completion_and_cached_retries(tmp_path, first):
    c, api, engine, request = setup(tmp_path)
    parts = split(request)
    other = "courses" if first == "student" else "student"
    response = post(c, PREFIX + first, parts[first])
    assert response.status_code == 202
    assert response.json() == {"request_id": "synthetic-rec-001", "status": "pending", "received": [first], "missing": [other]}
    assert post(c, PREFIX + first, parts[first]).json() == response.json()
    assert engine.calls == []
    completed = post(c, PREFIX + other, parts[other])
    assert completed.status_code == 200 and completed.json()["status"] == "no_feasible_plan"
    assert completed.headers["X-Request-ID"] == "synthetic-rec-001"
    assert len(engine.calls) == 1
    # A cached retry still works if a serving dependency disappears afterwards.
    api.catalog = None
    assert post(c, PREFIX + first, parts[first]).json() == completed.json()
    assert post(c, PREFIX + other, parts[other]).json() == completed.json()
    lookup = c.get(LOOKUP + "synthetic-rec-001", headers={"X-API-Key": "service"})
    assert lookup.status_code == 200
    assert lookup.json()["status"] == "completed" and lookup.json()["result"] == completed.json()
    assert len(engine.calls) == 1


@pytest.mark.parametrize("component", ["student", "courses"])
def test_invalid_components_not_stored_and_diagnostics_read_only(tmp_path, component):
    c, api, engine, request = setup(tmp_path)
    parts = split(request)
    parts[component][component + "_api_response"]["success"] = False
    assert post(c, PREFIX + component, parts[component]).status_code == 422
    assert c.get(LOOKUP + "synthetic-rec-001", headers={"X-API-Key": "service"}).status_code == 404
    assert engine.calls == []
    diagnostic = deepcopy(split(request)[component])
    diagnostic.pop("request_id")
    diagnostic.pop("recommendation", None)
    assert post(c, "/api/v1/inputs/" + component + "/validate", diagnostic).status_code == 200
    assert c.get(LOOKUP + "synthetic-rec-001", headers={"X-API-Key": "service"}).status_code == 404


@pytest.mark.parametrize("field,value", [("student_id", "other-student"), ("degree_id", "other-degree"), ("part_id", 20252)])
def test_envelope_mismatch_rejected_before_pair_claim(tmp_path, field, value):
    c, _, engine, request = setup(tmp_path)
    parts = split(request)
    assert post(c, PREFIX + "student", parts["student"]).status_code == 202
    parts["courses"][field] = value
    response = post(c, PREFIX + "courses", parts["courses"])
    assert response.status_code == 409 and response.json()["error"]["code"] == "REQUEST_IDENTITY_MISMATCH"
    assert engine.calls == []


def test_different_request_ids_never_join(tmp_path):
    c, _, engine, request = setup(tmp_path)
    parts = split(request)
    parts["courses"]["request_id"] = "synthetic-rec-002"
    assert post(c, PREFIX + "student", parts["student"]).json()["missing"] == ["courses"]
    assert post(c, PREFIX + "courses", parts["courses"]).json()["missing"] == ["student"]
    assert engine.calls == []


def test_conflicting_retry_does_not_overwrite_pending(tmp_path):
    c, _, engine, request = setup(tmp_path)
    parts = split(request)
    assert post(c, PREFIX + "student", parts["student"]).status_code == 202
    parts["student"]["recommendation"]["target_credits"] = 17
    response = post(c, PREFIX + "student", parts["student"])
    assert response.status_code == 409 and response.json()["error"]["code"] == "REQUEST_COMPONENT_CONFLICT"
    assert engine.calls == []


@pytest.mark.parametrize("section", ["integration_context", "source_contexts"])
def test_overlapping_evidence_must_agree_and_failure_is_cached(tmp_path, section):
    c, _, engine, request = setup(tmp_path)
    parts = split(request)
    if section == "integration_context":
        values = deepcopy(parts["student"][section]["student_values"])
        values["current_gpa_credits"]["value"] = 109
        parts["courses"][section]["student_values"] = values
    else:
        parts["student"][section]["courses"] = {**parts["courses"][section]["courses"], "student_id": "unrelated"}
    assert post(c, PREFIX + "student", parts["student"]).status_code == 202
    response = post(c, PREFIX + "courses", parts["courses"])
    assert response.status_code == 409 and response.json()["error"]["code"] == "REQUEST_CONTEXT_CONFLICT"
    assert response.json()["status"] == "failed"
    assert post(c, PREFIX + "courses", parts["courses"]).json() == response.json()
    assert engine.calls == []


def test_consistent_overlapping_context_and_combined_path_have_identical_engine_inputs(tmp_path):
    c, _, engine, request = setup(tmp_path)
    combined = post(c, "/recommend", request)
    parts = split(request)
    parts["student"]["integration_context"] = deepcopy(request["integration_context"])
    parts["courses"]["integration_context"] = deepcopy(request["integration_context"])
    assert post(c, PREFIX + "student", parts["student"]).status_code == 202
    response = post(c, PREFIX + "courses", parts["courses"])
    assert response.json() == combined.json()
    assert engine.calls[0] == engine.calls[1]


def test_simultaneous_arrivals_across_service_instances_claim_once(tmp_path):
    c, api, engine, request = setup(tmp_path)
    api2 = ApiService(settings=api.settings, catalog=api.catalog, grade_scale=api.grade_scale,
                      history_manager=api.history_manager, engine=engine, history_store=api.history_store)
    c2 = TestClient(create_app(service=api2))
    parts = split(request)
    barrier = Barrier(2)
    def submit(component, target):
        barrier.wait(timeout=10)
        return post(target, PREFIX + component, parts[component])
    with ThreadPoolExecutor(2) as pool:
        futures = [pool.submit(submit, "student", c), pool.submit(submit, "courses", c2)]
        responses = [future.result(timeout=30) for future in futures]
    assert sorted(response.status_code for response in responses) == [200, 202]
    assert len(engine.calls) == 1


def test_duplicates_and_lookup_during_inference_do_not_start_another_call(tmp_path):
    c, _, engine, request = setup(tmp_path)
    parts = split(request)
    entered, release = Event(), Event()
    original = engine.recommend_from_payloads
    def blocked(**kwargs):
        entered.set()
        assert release.wait(timeout=20)
        return original(**kwargs)
    engine.recommend_from_payloads = blocked
    assert post(c, PREFIX + "student", parts["student"]).status_code == 202
    with ThreadPoolExecutor(1) as pool:
        future = pool.submit(post, c, PREFIX + "courses", parts["courses"])
        assert entered.wait(timeout=10)
        try:
            duplicate = post(c, PREFIX + "courses", parts["courses"])
            assert duplicate.status_code == 202 and duplicate.json()["status"] == "processing"
            assert c.get(LOOKUP + "synthetic-rec-001", headers={"X-API-Key": "service"}).json()["status"] == "processing"
        finally:
            release.set()
        assert future.result(timeout=30).status_code == 200
    assert len(engine.calls) == 1


@pytest.mark.parametrize("key,status", [(None, 401), ("unknown", 403), ("admin", 403)])
def test_ingestion_and_retrieval_authentication(tmp_path, key, status):
    c, _, _, request = setup(tmp_path)
    headers = {"X-API-Key": key} if key else {}
    assert c.post(PREFIX + "student", json=split(request)["student"], headers=headers).status_code == status
    assert c.get(LOOKUP + "synthetic-rec-001", headers=headers).status_code == status


def test_authenticated_caller_cannot_access_or_complete_another_callers_request(tmp_path):
    c, _, engine, request = setup(tmp_path, service_keys={"php-a": "key-a", "php-b": "key-b"})
    parts = split(request)
    assert post(c, PREFIX + "student", parts["student"], key="key-a").status_code == 202
    assert c.get(LOOKUP + "synthetic-rec-001", headers={"X-API-Key": "key-b"}).status_code == 404
    assert post(c, PREFIX + "courses", parts["courses"], key="key-b").status_code == 404
    assert post(c, PREFIX + "courses", parts["courses"], key="key-a").status_code == 200
    assert len(engine.calls) == 1


def test_raw_http_decimal_credit_limit_is_not_rounded(tmp_path):
    import json
    c, _, engine, request = setup(tmp_path)
    parts = split(request)
    parts["student"]["recommendation"].pop("target_credits")
    parts["student"]["recommendation"].update(min_credits="12.0000000000000000000000000001", max_credits="12")
    raw = json.dumps(parts["student"]).replace('"12.0000000000000000000000000001"', "12.0000000000000000000000000001")
    assert c.post(PREFIX + "student", content=raw, headers={"X-API-Key": "service", "Content-Type": "application/json"}).status_code == 202
    assert post(c, PREFIX + "courses", parts["courses"]).status_code == 422
    assert engine.calls == []


def test_expired_pending_request_returns_terminal_error_without_inference(tmp_path):
    from src.api.request_store import RequestStore
    c, api, engine, request = setup(tmp_path)
    now = [100.0]
    api._request_store = RequestStore(api.settings.request_store_path, pending_ttl_seconds=1,
                                     processing_ttl_seconds=10, result_ttl_seconds=20,
                                     max_requests=10, max_payload_bytes=2097152, clock=lambda: now[0])
    parts = split(request)
    assert post(c, PREFIX + "student", parts["student"]).status_code == 202
    now[0] += 2
    response = post(c, PREFIX + "courses", parts["courses"])
    assert response.status_code == 410 and response.json()["status"] == "failed"
    assert response.json()["error"]["code"] == "REQUEST_EXPIRED"
    assert engine.calls == []


def test_result_is_durable_when_response_delivery_disconnects(tmp_path):
    import asyncio
    import json
    c, api, engine, request = setup(tmp_path)
    parts = split(request)
    assert post(c, PREFIX + "student", parts["student"]).status_code == 202
    path = PREFIX + "courses"
    raw = json.dumps(parts["courses"]).encode()
    scope = {"type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1", "method": "POST",
             "scheme": "http", "path": path, "raw_path": path.encode(), "query_string": b"",
             "headers": [(b"content-type", b"application/json"), (b"x-api-key", b"service")],
             "server": ("testserver", 80), "client": ("testclient", 1), "root_path": ""}
    delivered = False
    async def receive():
        nonlocal delivered
        if not delivered:
            delivered = True
            return {"type": "http.request", "body": raw, "more_body": False}
        return {"type": "http.disconnect"}
    async def send(message):
        raise ConnectionError("synthetic response disconnect")
    with pytest.raises(ConnectionError):
        asyncio.run(c.app(scope, receive, send))
    # Another worker can retrieve the saved result, without retaining the old service object.
    other = ApiService(settings=api.settings, catalog=api.catalog, grade_scale=api.grade_scale,
                       history_manager=api.history_manager, engine=engine, history_store=api.history_store)
    lookup = TestClient(create_app(service=other)).get(LOOKUP + "synthetic-rec-001", headers={"X-API-Key": "service"})
    assert lookup.status_code == 200 and lookup.json()["status"] == "completed"
    assert len(engine.calls) == 1


def test_unexpected_inference_error_is_safe_and_never_retried(tmp_path):
    c, api, engine, request = setup(tmp_path)
    parts = split(request)
    calls = []
    def fail(request):
        calls.append(request)
        raise RuntimeError("PII_CANARY D:/private/secret")
    api.recommend = fail
    assert post(c, PREFIX + "student", parts["student"]).status_code == 202
    result = post(c, PREFIX + "courses", parts["courses"])
    assert result.status_code == 500 and result.json()["status"] == "failed"
    assert "PII_CANARY" not in result.text and "private" not in result.text
    assert post(c, PREFIX + "student", parts["student"]).json() == result.json()
    assert len(calls) == 1 and engine.calls == []


def test_payload_stream_limit_and_safe_schema_error(tmp_path):
    c, _, engine, request = setup(tmp_path, request_max_payload_bytes=128)
    response = post(c, PREFIX + "student", split(request)["student"])
    assert response.status_code == 413 and "studentDegreeInfo" not in response.text
    assert not c.app.state.api_service.settings.request_store_path.exists()
    c, _, _, request = setup(tmp_path / "other")
    body = split(request)["student"]
    body["request_id"] = "../PII_CANARY"
    response = post(c, PREFIX + "student", body)
    assert response.status_code == 422 and "PII_CANARY" not in response.text
    assert engine.calls == []


def test_actual_two_stage_recommendation_output_and_features_match_combined(tmp_path):
    api, artifacts, request = api_engine(tmp_path / "history")
    combined = api.recommend(deepcopy(request))
    first_features = artifacts.stage1.grade_model.matrices[-1].copy()
    second_features = artifacts.stage2.grade_model.matrices[-1].copy()
    api.settings = replace(api.settings, request_store_path=tmp_path / "requests" / "requests.sqlite3")
    parts = split(request)
    assert api.submit_recommendation_input("courses", parts["courses"], owner="php")["status"] == "pending"
    state = api.submit_recommendation_input("student", parts["student"], owner="php")
    assert state["result"] == combined
    import pandas as pd
    pd.testing.assert_frame_equal(first_features, artifacts.stage1.grade_model.matrices[-1])
    pd.testing.assert_frame_equal(second_features, artifacts.stage2.grade_model.matrices[-1])


def test_settings_keep_storage_separate_keys_distinct_and_limits_explicit(tmp_path, monkeypatch):
    with pytest.raises(ValueError):
        ApiSettings(service_key="shared", service_keys={"php": "shared"})
    with pytest.raises(ValueError):
        ApiSettings(service_keys={"legacy": "key"})
    with pytest.raises(ValueError):
        ApiSettings(request_pending_ttl_seconds=True)
    with pytest.raises(ValueError):
        ApiSettings(request_store_path=tmp_path / "history" / "requests.sqlite3", incremental_history_root=tmp_path / "history")
    monkeypatch.setenv("ADVISOR_SERVICE_KEYS", '{"php-a":"synthetic-key"}')
    monkeypatch.setenv("ADVISOR_REQUEST_STORE_PATH", str(tmp_path / "private.sqlite3"))
    monkeypatch.setenv("ADVISOR_REQUEST_PENDING_TTL_SECONDS", "60")
    settings = ApiSettings.from_env()
    assert settings.service_keys == {"php-a": "synthetic-key"}
    assert settings.request_pending_ttl_seconds == 60
    assert "synthetic-key" not in repr(settings) and str(tmp_path) not in repr(settings)
