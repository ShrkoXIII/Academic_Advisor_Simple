"""Optional pull integration uses configured endpoints and pinned public addresses."""
import json

import pytest

from src.api.settings import ApiSettings
from src.api.validation import ApiError


def configured(**changes):
    return ApiSettings(direct_fetch_enabled=True, student_api_url="https://student.example.test/student",
                       courses_api_url="https://courses.example.test/candidates",
                       courses_query_parameters={"student_id": "sid", "part_id": "term", "degree_id": "degree"},
                       **changes)


def test_php_push_remains_default_and_pull_requires_explicit_configuration():
    assert ApiSettings().direct_fetch_enabled is False
    from src.api.backend_client import BackendClient
    with pytest.raises(ApiError, match="disabled"):
        BackendClient(ApiSettings()).fetch_inputs(student_id="synthetic", degree_id="degree", part_id=20252)
    with pytest.raises(ValueError):
        ApiSettings(direct_fetch_enabled=True)


def test_environment_urls_timeout_and_courses_parameters(monkeypatch):
    for name, value in {"ADVISOR_ENABLE_DIRECT_FETCH": "true", "ADVISOR_STUDENT_API_URL": "https://student.example.test/s",
                       "ADVISOR_COURSES_API_URL": "https://courses.example.test/c",
                       "ADVISOR_COURSES_QUERY_PARAMETERS": '{"student_id":"student","part_id":"semester"}',
                       "ADVISOR_API_TIMEOUT_SECONDS": "3.5", "ADVISOR_BACKEND_TOKEN": "private-token"}.items():
        monkeypatch.setenv(name, value)
    settings = ApiSettings.from_env()
    assert settings.api_timeout_seconds == 3.5
    assert settings.courses_query_parameters == {"student_id": "student", "part_id": "semester"}
    assert "private-token" not in repr(settings)


@pytest.mark.parametrize("url", ["http://university.example/s", "https://user:secret@example.test/s",
                                   "https://example.test/s#fragment", "file:///etc/passwd", "https://127.0.0.1/s",
                                   "https://169.254.169.254/latest", "https://example.test/s?token=secret",
                                   "https://224.0.0.1/student"])
def test_unsafe_endpoint_configuration_is_rejected(url):
    with pytest.raises(ValueError):
        ApiSettings(student_api_url=url)


def test_client_uses_actual_student_parameters_and_configured_courses_parameters(monkeypatch):
    from src.api import backend_client
    monkeypatch.setattr(backend_client.socket, "getaddrinfo", lambda *args, **kwargs: [(2, 1, 6, "", ("8.8.8.8", 443))])
    calls = []
    def exchange(self, endpoint, address, query, headers):
        calls.append((endpoint, address, query, headers))
        return 200, json.dumps({"success": True, "data": {}}).encode()
    monkeypatch.setattr(backend_client.BackendClient, "_exchange", exchange)
    request = backend_client.BackendClient(configured(backend_token="secret")).fetch_inputs(
        student_id="synthetic", degree_id="degree", part_id=20252)
    assert calls[0][2] == {"studentId": "synthetic", "semesterId": "20252"}
    assert calls[1][2] == {"sid": "synthetic", "term": "20252", "degree": "degree"}
    assert all(call[1] == "8.8.8.8" for call in calls)
    assert calls[0][3]["Authorization"] == "Bearer secret"
    assert request["source_contexts"]["student"] == request["source_contexts"]["courses"]
    assert request["student_api_response"]["success"] is True


def test_rebinding_to_private_address_is_blocked_before_transport(monkeypatch):
    from src.api import backend_client
    monkeypatch.setattr(backend_client.socket, "getaddrinfo", lambda *args, **kwargs: [(2, 1, 6, "", ("127.0.0.1", 443))])
    monkeypatch.setattr(backend_client.BackendClient, "_exchange", lambda *args: pytest.fail("SSRF reached transport"))
    with pytest.raises(ApiError) as raised:
        backend_client.BackendClient(configured()).fetch_inputs(student_id="synthetic", degree_id="degree", part_id=20252)
    assert raised.value.issue["code"] == "BACKEND_ADDRESS_FORBIDDEN"


@pytest.mark.parametrize("status,body", [(302, b'{"location":"http://private/token"}'), (500, b'private-secret'), (200, b'not-json')])
def test_redirects_and_upstream_errors_never_leak_body(monkeypatch, status, body):
    from src.api import backend_client
    monkeypatch.setattr(backend_client.socket, "getaddrinfo", lambda *args, **kwargs: [(2, 1, 6, "", ("8.8.8.8", 443))])
    monkeypatch.setattr(backend_client.BackendClient, "_exchange", lambda *args: (status, body))
    with pytest.raises(ApiError) as raised:
        backend_client.BackendClient(configured()).fetch_inputs(student_id="synthetic", degree_id="degree", part_id=20252)
    assert "private" not in str(raised.value.issue)


def test_local_http_requires_explicit_loopback_testing_mode():
    assert ApiSettings(allow_local_backend_http=True, student_api_url="http://127.0.0.1/student").allow_local_backend_http
    with pytest.raises(ValueError):
        ApiSettings(allow_local_backend_http=True, student_api_url="http://10.0.0.1/student")


def test_tls_connection_pins_validated_ip_and_preserves_original_server_name(monkeypatch):
    from types import SimpleNamespace
    from src.api import backend_client
    calls = []
    raw_socket = SimpleNamespace(close=lambda: calls.append("closed"))
    monkeypatch.setattr(backend_client.socket, "create_connection", lambda address, timeout: calls.append((address, timeout)) or raw_socket)
    connection = backend_client._PinnedHTTPSConnection("university.example.test", "8.8.8.8", 443, 2.5)
    connection._context = SimpleNamespace(wrap_socket=lambda sock, server_hostname: calls.append((sock, server_hostname)) or sock)
    connection.connect()
    assert calls == [(("8.8.8.8", 443), 2.5), (raw_socket, "university.example.test")]


def test_mixed_public_and_private_dns_answers_are_rejected(monkeypatch):
    from src.api import backend_client
    monkeypatch.setattr(backend_client.socket, "getaddrinfo", lambda *args, **kwargs: [
        (2, 1, 6, "", ("8.8.8.8", 443)), (2, 1, 6, "", ("10.1.2.3", 443))])
    with pytest.raises(ApiError) as raised:
        backend_client.BackendClient(configured()).fetch_inputs(student_id="synthetic", degree_id="degree", part_id=20252)
    assert raised.value.issue["code"] == "BACKEND_ADDRESS_FORBIDDEN"


def test_multicast_dns_address_is_rejected_before_transport(monkeypatch):
    from src.api import backend_client
    monkeypatch.setattr(backend_client.socket, "getaddrinfo", lambda *args, **kwargs: [(2, 1, 6, "", ("224.0.0.1", 443))])
    monkeypatch.setattr(backend_client.BackendClient, "_exchange", lambda *args: pytest.fail("Unsafe DNS reached transport"))
    with pytest.raises(ApiError) as raised:
        backend_client.BackendClient(configured()).fetch_inputs(student_id="synthetic", degree_id="degree", part_id=20252)
    assert raised.value.issue["code"] == "BACKEND_ADDRESS_FORBIDDEN"
