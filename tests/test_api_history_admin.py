"""Administrative transport uses independent roles and explicit confirmations."""
import pytest

from src.api.service import ApiService
from src.api.settings import ApiSettings


class Store:
    def __init__(self):
        self.calls = []
    def status(self):
        return {"mode": "manual", "active_as_of_part": None, "available_versions": [], "pending_delta": None,
                "last_successful_update": None, "failures": [], "serving_compatibility": "unavailable"}
    def set_mode(self, mode):
        self.calls.append(("mode", mode))
        return {"mode": mode}
    def initialize(self, **kwargs):
        self.calls.append(("initialize", kwargs))
        return {"status": "initialized"}
    def preview(self, **kwargs):
        self.calls.append(("preview", kwargs))
        return {"status": "previewed", "preview_token": "a" * 64}
    def commit(self, **kwargs):
        self.calls.append(("commit", kwargs))
        return {"status": "committed", "activated": False}
    def activate(self, **kwargs):
        self.calls.append(("activate", kwargs))
        return {"status": "activated"}
    def finalize(self, **kwargs):
        self.calls.append(("finalize", kwargs))
        return {"status": "applied"}
    def serving_manager(self):
        return None


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from src.api.app import create_app
    store = Store()
    service = ApiService(settings=ApiSettings(service_key="service", admin_key="admin", finalization_key="event"), history_store=store)
    with TestClient(create_app(service=service)) as http:
        yield http, store


def delta():
    return {"part_id": 20252, "rows": [], "finalization": {"finalized_part_id": 20252, "approval_reference": "synthetic-approved-term"}}


def test_admin_status_and_durable_mode_workflow(client):
    http, store = client
    response = http.get("/api/v1/admin/history/status", headers={"X-API-Key": "admin"})
    assert response.status_code == 200
    assert response.json()["mode"] == "manual"
    assert http.put("/api/v1/admin/history/mode", headers={"X-API-Key": "admin"}, json={"mode": "disabled"}).status_code == 200
    assert store.calls == [("mode", "disabled")]


@pytest.mark.parametrize("path,method,body", [
    ("/api/v1/admin/history/status", "get", None),
    ("/api/v1/admin/history/mode", "put", {"mode": "manual"}),
    ("/api/v1/admin/history/initialize", "post", {"expected_source_hash": "a"*64, "approval_reference": "synthetic", "confirmation": True, "cumulative_history_confirmed": True}),
    ("/api/v1/admin/history/preview", "post", delta()),
    ("/api/v1/admin/history/commit", "post", {**delta(), "preview_token": "a"*64, "confirmation": True}),
    ("/api/v1/admin/history/activate", "post", {"history_as_of_part": 20252, "expected_history_sha256": "b"*64, "confirmation": True}),
])
def test_service_credentials_cannot_access_administration(client, path, method, body):
    http, store = client
    kwargs = {"headers": {"X-API-Key": "service"}}
    if body is not None:
        kwargs["json"] = body
    assert getattr(http, method)(path, **kwargs).status_code == 403
    assert store.calls == []


def test_manual_preview_commit_and_activation_are_separate(client):
    http, store = client
    headers = {"X-API-Key": "admin"}
    assert http.post("/api/v1/admin/history/preview", headers=headers, json=delta()).status_code == 200
    response = http.post("/api/v1/admin/history/commit", headers=headers, json={**delta(), "preview_token": "a"*64, "confirmation": True})
    assert response.status_code == 200 and response.json()["activated"] is False
    assert http.post("/api/v1/admin/history/activate", headers=headers, json={"history_as_of_part": 20252, "expected_history_sha256": "b"*64,
                "confirmation": True, "rollback": False}).status_code == 200
    assert [call[0] for call in store.calls] == ["preview", "commit", "activate"]


def test_finalization_event_has_its_own_authorized_credential(client):
    http, store = client
    for credential in ("service", "admin"):
        assert http.post("/api/v1/admin/history/finalization-events", headers={"X-API-Key": credential}, json=delta()).status_code == 403
    assert http.post("/api/v1/admin/history/finalization-events", headers={"X-API-Key": "event"}, json=delta()).status_code == 200
    assert store.calls[0][0] == "finalize"
    assert store.calls[0][1]["trusted_event"] is True


def test_confirmation_and_finalization_proof_are_required_before_writing(client):
    http, store = client
    headers = {"X-API-Key": "admin"}
    assert http.post("/api/v1/admin/history/commit", headers=headers, json={**delta(), "preview_token": "a"*64, "confirmation": False}).status_code == 422
    bad = delta()
    bad["finalization"]["finalized_part_id"] = 20253
    assert http.post("/api/v1/admin/history/preview", headers=headers, json=bad).status_code == 422
    no_proof = {"part_id": 20252, "rows": []}
    assert http.post("/api/v1/admin/history/finalization-events", headers={"X-API-Key": "event"}, json=no_proof).status_code == 422
    assert store.calls == []


def test_request_cannot_supply_a_history_source_path_or_backend_url(client):
    http, store = client
    request = {"expected_source_hash": "a"*64, "approval_reference": "synthetic", "confirmation": True, "source_root": "private-path"}
    response = http.post("/api/v1/admin/history/initialize", headers={"X-API-Key": "admin"}, json=request)
    assert response.status_code == 422 and "private-path" not in response.text
    assert store.calls == []


def test_baseline_requires_explicit_cumulative_history_attestation(client):
    http, store = client
    request = {"expected_source_hash": "a"*64, "approval_reference": "synthetic", "confirmation": True,
               "cumulative_history_confirmed": False}
    response = http.post("/api/v1/admin/history/initialize", headers={"X-API-Key": "admin"}, json=request)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "BASELINE_NOT_CUMULATIVE"
    assert store.calls == []
