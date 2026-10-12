"""Optional local pull integration with DNS pinning, TLS and no redirects/proxies."""
from decimal import Decimal
import http.client
import ipaddress
import json
import socket
import ssl
from urllib.parse import urlencode, urlsplit

from .validators.common import ApiError, identifier, part


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, host, address, port, timeout):
        super().__init__(host, port=port, timeout=timeout, context=ssl.create_default_context())
        self._address = address

    def connect(self):
        sock = socket.create_connection((self._address, self.port), self.timeout)
        try:
            self.sock = self._context.wrap_socket(sock, server_hostname=self.host)
        except BaseException:
            sock.close()
            raise


class BackendClient:
    """Accept identity only; endpoint URLs and parameter names come from settings."""
    def __init__(self, settings):
        self.settings = settings

    def _address(self, endpoint):
        parsed = urlsplit(endpoint)
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        addresses = {item[4][0] for item in socket.getaddrinfo(parsed.hostname, port, type=socket.SOCK_STREAM)}
        local = self.settings.allow_local_backend_http and (parsed.hostname == "localhost" or
                    self._is_loopback(parsed.hostname))
        if not addresses or any(not (ipaddress.ip_address(value).is_loopback if local else
                                    ipaddress.ip_address(value).is_global and not ipaddress.ip_address(value).is_multicast)
                                for value in addresses):
            raise ApiError("BACKEND_ADDRESS_FORBIDDEN", "Configured backend resolves to an unsafe address.", status_code=503)
        return sorted(addresses)[0]

    @staticmethod
    def _is_loopback(value):
        try:
            return ipaddress.ip_address(value).is_loopback
        except ValueError:
            return False

    def _exchange(self, endpoint, address, query, headers):
        parsed = urlsplit(endpoint)
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        connection = (_PinnedHTTPSConnection(parsed.hostname, address, port, self.settings.api_timeout_seconds)
                      if parsed.scheme == "https" else http.client.HTTPConnection(address, port=port, timeout=self.settings.api_timeout_seconds))
        try:
            target = parsed.path or "/"
            if query:
                target += "?" + urlencode(query)
            connection.request("GET", target, headers={"Host": parsed.netloc, "Accept": "application/json", **headers})
            response = connection.getresponse()
            body = response.read(8 * 1024 * 1024 + 1)
            if len(body) > 8 * 1024 * 1024:
                raise ApiError("BACKEND_RESPONSE_TOO_LARGE", "Backend response exceeds the integration size limit.", status_code=502)
            return response.status, body
        finally:
            connection.close()

    def _get(self, endpoint, query):
        try:
            address = self._address(endpoint)
            headers = {"Authorization": "Bearer " + self.settings.backend_token} if self.settings.backend_token else {}
            status, body = self._exchange(endpoint, address, query, headers)
            if not 200 <= status < 300:
                raise ApiError("BACKEND_HTTP_ERROR", "Backend request failed; redirects are forbidden.", status_code=502)
            def reject_constant(value):
                raise ValueError
            payload = json.loads(body, parse_float=Decimal, parse_constant=reject_constant)
            if not isinstance(payload, dict):
                raise ValueError
            return payload
        except ApiError:
            raise
        except Exception:
            raise ApiError("BACKEND_FETCH_FAILED", "Configured backend could not provide valid JSON.", status_code=502) from None

    def fetch_inputs(self, *, student_id, degree_id, part_id):
        if not self.settings.direct_fetch_enabled:
            raise ApiError("DIRECT_FETCH_DISABLED", "Direct backend fetching is disabled.", status_code=503)
        context = {"student_id": identifier(student_id, "student_id"), "degree_id": identifier(degree_id, "degree_id"), "part_id": part(part_id)}
        student = self._get(self.settings.student_api_url, {"studentId": context["student_id"], "semesterId": str(context["part_id"])})
        courses = self._get(self.settings.courses_api_url, {name: str(context[key]) for key, name in self.settings.courses_query_parameters.items()})
        return {**context, "source_contexts": {"student": dict(context), "courses": dict(context)},
                "student_api_response": student, "courses_api_response": courses}
