"""HTTP-to-immutable-store integration with synthetic approved artifacts only."""
from copy import deepcopy
import json

from fastapi.testclient import TestClient

from src.api.app import create_app
from src.api.service import ApiService
from src.api.settings import ApiSettings
from src.api.validation import json_safe
from src.features.frozen_history import file_sha256
from src.recommendation.two_stage_engine import TwoStagePlanRecommender
from tests.test_api_integration import api_engine
from tests.test_cumulative_history import payload, source


ADMIN = {"X-API-Key": "admin"}
EVENT = {"X-API-Key": "event"}
SERVICE = {"X-API-Key": "service"}


def delta(part):
    data = payload(part)
    return {"part_id": part, "rows": data["aggregates"],
            "finalization": {"finalized_part_id": part, "approval_reference": "synthetic-approved-term"}}


def configured(tmp_path):
    legacy = tmp_path / "legacy"
    previous, artifacts, request = api_engine(legacy)
    _, digest = source(legacy)
    settings = ApiSettings(service_key="service", admin_key="admin", finalization_key="event",
        incremental_history_root=tmp_path / "incremental", history_baseline_source_root=legacy)
    service = ApiService(settings=settings, engine=previous.engine, catalog=previous.catalog,
                         grade_scale=previous.grade_scale)
    return service, artifacts, request, digest


def initialize(http, digest):
    response = http.post("/api/v1/admin/history/initialize", headers=ADMIN, json={
        "expected_source_hash": digest, "approval_reference": "synthetic-approved-prefix",
        "confirmation": True, "cumulative_history_confirmed": True})
    assert response.status_code == 200, response.text
    return response.json()


def test_http_migration_manual_auto_rollback_and_existing_pareto_contract(tmp_path):
    service, artifacts, request, digest = configured(tmp_path)
    before = deepcopy(service.recommend(request)["recommendations"])
    legacy_hashes = {p.relative_to(service.settings.history_baseline_source_root).as_posix(): file_sha256(p)
                     for p in service.settings.history_baseline_source_root.rglob("*") if p.is_file()}
    with TestClient(create_app(service=service)) as http:
        baseline = initialize(http, digest)
        status = http.get("/api/v1/admin/history/status", headers=ADMIN).json()
        assert status["active_as_of_part"] == 20251
        assert status["serving_artifacts_compatible"] is True

        preview = http.post("/api/v1/admin/history/preview", headers=ADMIN, json=delta(20252)).json()
        committed = http.post("/api/v1/admin/history/commit", headers=ADMIN,
            json={**delta(20252), "preview_token": preview["preview_token"], "confirmation": True})
        assert committed.status_code == 200, committed.text
        assert committed.json()["activated"] is False
        assert http.get("/api/v1/admin/history/status", headers=ADMIN).json()["active_as_of_part"] == 20251
        activated = http.post("/api/v1/admin/history/activate", headers=ADMIN, json={
            "history_as_of_part": 20252, "expected_history_sha256": committed.json()["new_history_sha256"], "confirmation": True})
        assert activated.status_code == 200, activated.text
        assert service.history_manager.capture(target_part=20253, history_as_of_part=20252,
                                               allow_older_history=False).as_of_part == 20252

        # Original request keeps its exact earlier snapshot through the read-only
        # legacy path; the recommendation payload and both feature widths agree.
        output = http.post("/api/v1/recommendations", headers=SERVICE, json=json_safe(request))
        assert output.status_code == 200, output.text
        assert output.json()["recommendations"] == json_safe(before)
        assert output.json()["metadata"]["production_ranking_strategy"] == "pareto v1 -> pareto v1"
        assert output.json()["metadata"]["top_k"] == 3
        assert artifacts.stage1.grade_model.matrices[-1].shape[1] == 33
        assert artifacts.stage2.grade_model.matrices[-1].shape[1] == 47

        assert http.put("/api/v1/admin/history/mode", headers=ADMIN, json={"mode": "auto_on_finalization"}).status_code == 200
        automatic = http.post("/api/v1/admin/history/finalization-events", headers=EVENT, json=delta(20253))
        assert automatic.status_code == 200, automatic.text
        assert automatic.json()["active_as_of_part"] == 20253
        replay = http.post("/api/v1/admin/history/finalization-events", headers=EVENT, json=delta(20253))
        assert replay.status_code == 200 and replay.json()["status"] == "already_applied"
        assert http.put("/api/v1/admin/history/mode", headers=ADMIN, json={"mode": "manual"}).status_code == 200
        rollback = http.post("/api/v1/admin/history/activate", headers=ADMIN, json={
            "history_as_of_part": 20251, "expected_history_sha256": baseline["new_history_sha256"],
            "confirmation": True, "rollback": True})
        assert rollback.status_code == 200, rollback.text
        assert http.get("/api/v1/admin/history/status", headers=ADMIN).json()["available_versions"] == [20251, 20252, 20253]
    assert legacy_hashes == {p.relative_to(service.settings.history_baseline_source_root).as_posix(): file_sha256(p)
                            for p in service.settings.history_baseline_source_root.rglob("*") if p.is_file()}


def test_missing_artifacts_block_migration_but_http_validation_remains_available(tmp_path):
    service, _, request, digest = configured(tmp_path)
    service.engine = service.artifacts = None
    with TestClient(create_app(service=service)) as http:
        denied = http.post("/api/v1/admin/history/initialize", headers=ADMIN, json={
            "expected_source_hash": digest, "approval_reference": "synthetic-approved-prefix",
            "confirmation": True, "cumulative_history_confirmed": True})
        assert denied.status_code == 503
        assert denied.json()["error"]["code"] == "SERVING_ARTIFACTS_UNAVAILABLE"
        assert not (service.settings.incremental_history_root / "as_of_20251").exists()
        health = http.get("/health").json()
        assert health["api_health"] == "healthy" and health["model_readiness"]["ready"] is False
        validation = {key: request[key] for key in (
            "student_id", "degree_id", "part_id", "source_contexts", "integration_context", "student_api_response")}
        assert http.post("/api/v1/inputs/student/validate", headers=SERVICE, json=json_safe(validation)).status_code == 200
        status = http.get("/api/v1/admin/history/status", headers=ADMIN).json()
        assert status["active_as_of_part"] is None
        assert status["failures"][-1]["code"] == "SERVING_ARTIFACTS_UNAVAILABLE"


def test_specialty_feature_requirement_rejects_update_before_publication(tmp_path):
    service, artifacts, _, digest = configured(tmp_path)
    with TestClient(create_app(service=service)) as http:
        initialize(http, digest)
        artifacts.manifest["stages"]["stage1"]["feature_contract"]["model_features"].append("specialty_history_unavailable")
        response = http.post("/api/v1/admin/history/preview", headers=ADMIN, json=delta(20252))
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "SPECIALTY_HISTORY_AGGREGATES_UNAVAILABLE"
        assert not (service.settings.incremental_history_root / "as_of_20252").exists()
        assert http.get("/api/v1/admin/history/status", headers=ADMIN).json()["active_as_of_part"] == 20251


def test_worker_started_before_migration_adopts_shared_active_pointer(tmp_path):
    service, artifacts, _, digest = configured(tmp_path)
    other_engine = TwoStagePlanRecommender.from_loaded_artifacts(artifacts, service.history_manager)
    other = ApiService(settings=service.settings, engine=other_engine,
                       catalog=service.catalog, grade_scale=service.grade_scale)
    with TestClient(create_app(service=service)) as first, TestClient(create_app(service=other)) as second:
        initialize(first, digest)
        preview = first.post("/api/v1/admin/history/preview", headers=ADMIN, json=delta(20252)).json()
        committed = first.post("/api/v1/admin/history/commit", headers=ADMIN,
            json={**delta(20252), "preview_token": preview["preview_token"], "confirmation": True}).json()
        assert first.post("/api/v1/admin/history/activate", headers=ADMIN, json={
            "history_as_of_part": 20252, "expected_history_sha256": committed["new_history_sha256"], "confirmation": True}).status_code == 200
        response = second.post("/api/v1/history/deltas/validate", headers=ADMIN, json=delta(20253))
        assert response.status_code == 200, response.text
        assert response.json()["summary"]["history_as_of_part"] == 20252
        assert other.engine.history_manager.capture(target_part=20253, history_as_of_part=20252,
                                                    allow_older_history=False).as_of_part == 20252


def test_corrupt_active_pointer_preserves_independent_diagnostics(tmp_path):
    service, artifacts, request, digest = configured(tmp_path)
    with TestClient(create_app(service=service)) as http:
        initialize(http, digest)
        control_path = service.settings.incremental_history_root / "control.json"
        control = json.loads(control_path.read_text(encoding="utf8"))
        control["active"]["history_sha256"] = "0" * 64
        control_path.write_text(json.dumps(control), encoding="utf8")
        health = http.get("/health").json()
        assert health["api_health"] == "healthy" and health["history_readiness"]["ready"] is False
        validation = http.post("/api/v1/history/deltas/validate", headers=ADMIN, json=delta(20252))
        assert validation.status_code == 200 and validation.json()["validation_status"] == "partial"
        denied = http.post("/api/v1/recommendations", headers=SERVICE, json=json_safe(request))
        assert denied.status_code == 503 and denied.json()["error"]["code"] == "HISTORY_UNAVAILABLE"
        assert not artifacts.stage1.grade_model.matrices and not artifacts.stage2.grade_model.matrices


def test_read_only_delta_validation_rejects_skipped_semester_without_writing(tmp_path):
    service, _, _, digest = configured(tmp_path)
    with TestClient(create_app(service=service)) as http:
        initialize(http, digest)
        control_path = service.settings.incremental_history_root / "control.json"
        before = control_path.read_bytes()
        response = http.post("/api/v1/history/deltas/validate", headers=ADMIN, json=delta(20261))
        assert response.status_code == 409, response.text
        assert response.json()["validation_status"] == "invalid"
        assert before == control_path.read_bytes()
        assert not (service.settings.incremental_history_root / "as_of_20261").exists()


def test_oversized_integer_delta_is_rejected_safely_without_publication(tmp_path):
    service, _, _, digest = configured(tmp_path)
    with TestClient(create_app(service=service)) as http:
        initialize(http, digest)
        body = delta(20252)
        body["rows"][0].update(count=2**53 + 1, mark_sum=50 * (2**53 + 1),
                               fail_count=0, retake_count=0, attempt_sum=2**53 + 1)
        control_path = service.settings.incremental_history_root / "control.json"
        before = control_path.read_bytes()
        response = http.post("/api/v1/history/deltas/validate", headers=ADMIN, json=body)
        assert response.status_code == 422
        assert response.json()["errors"][0]["code"] == "INVALID_DELTA"
        assert str(2**53 + 1) not in response.text
        assert control_path.read_bytes() == before
        assert not (service.settings.incremental_history_root / "as_of_20252").exists()
