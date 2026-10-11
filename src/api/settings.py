"""Environment-only transport configuration; no academic policy defaults."""
from dataclasses import dataclass, field
import ipaddress
import json
import math
import os
from pathlib import Path
import re
from urllib.parse import urlsplit

from src import paths


def validate_backend_url(value, *, allow_local_http=False):
    """Validate trusted deployment configuration, never a request-supplied URL."""
    if value is None:
        return
    if not isinstance(value, str) or not value or any(char.isspace() or ord(char) < 32 for char in value):
        raise ValueError("Invalid backend endpoint configuration.")
    try:
        parsed = urlsplit(value)
        hostname, port = parsed.hostname, parsed.port
        if not hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError
        local = hostname == "localhost"
        try:
            address = ipaddress.ip_address(hostname)
        except ValueError:
            address = None
        if address is not None:
            local = address.is_loopback
            if (not address.is_global or address.is_multicast) and not (allow_local_http and local):
                raise ValueError
        if hostname == "localhost" and not allow_local_http:
            raise ValueError
        if parsed.scheme != "https" and not (allow_local_http and local and parsed.scheme == "http"):
            raise ValueError
        if port is not None and not 1 <= port <= 65535:
            raise ValueError
    except (ValueError, TypeError):
        raise ValueError("Backend endpoints require HTTPS and a public address, or explicit loopback testing.") from None


@dataclass(frozen=True)
class ApiSettings:
    service_key: str | None = field(default=None, repr=False)
    admin_key: str | None = field(default=None, repr=False)
    finalization_key: str | None = field(default=None, repr=False)
    enable_backtesting: bool = False
    performance_test_mode: bool = False
    performance_test_max_candidates: int | None = None
    diploma_gpa_aliases: tuple = ("diploma_gpa", "DIPLOMA_GPA")
    diploma_type_aliases: tuple = ("diploma_type_id", "DIPLOMA_TYPE_ID")
    direct_fetch_enabled: bool = False
    student_api_url: str | None = field(default=None, repr=False)
    courses_api_url: str | None = field(default=None, repr=False)
    courses_query_parameters: dict | None = field(default=None, repr=False)
    api_timeout_seconds: float = 10.0
    backend_token: str | None = field(default=None, repr=False)
    allow_local_backend_http: bool = False
    incremental_history_root: Path = field(default_factory=lambda: paths.FROZEN_HISTORY_INCREMENTAL_DIR, repr=False)
    history_baseline_source_root: Path = field(default_factory=lambda: paths.FROZEN_HISTORY_DIR_V2, repr=False)
    history_update_mode: str = "manual"

    def __post_init__(self):
        keys = [key for key in (self.service_key, self.admin_key, self.finalization_key) if key]
        if len(keys) != len(set(keys)):
            raise ValueError("Service, administrative and finalization keys must be distinct.")
        if self.history_update_mode not in {"disabled", "manual", "auto_on_finalization"}:
            raise ValueError("Invalid history update mode.")
        if isinstance(self.api_timeout_seconds, bool) or not math.isfinite(self.api_timeout_seconds) or self.api_timeout_seconds <= 0:
            raise ValueError("Backend timeout must be finite and positive.")
        for url in (self.student_api_url, self.courses_api_url):
            validate_backend_url(url, allow_local_http=self.allow_local_backend_http)
        if self.courses_query_parameters is not None:
            mapping = self.courses_query_parameters
            if (not isinstance(mapping, dict) or set(mapping) - {"student_id", "degree_id", "part_id"}
                    or any(not isinstance(value, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]*", value) for value in mapping.values())
                    or len(set(mapping.values())) != len(mapping)):
                raise ValueError("Courses query parameter mapping must explicitly map identity fields to unique parameter names.")
        if self.direct_fetch_enabled and (not self.student_api_url or not self.courses_api_url or self.courses_query_parameters is None):
            raise ValueError("Direct fetching needs both endpoints and an explicit Courses parameter mapping.")
        if self.backend_token and any(ord(char) < 32 or ord(char) == 127 for char in self.backend_token):
            raise ValueError("Invalid backend credential configuration.")
        value = self.performance_test_max_candidates
        if value is not None and (isinstance(value, bool) or not isinstance(value, int) or value < 1):
            raise ValueError("Performance test candidate limit must be a positive integer.")
        if self.performance_test_mode and value is None:
            raise ValueError("Performance test mode requires an explicit candidate limit.")

    @classmethod
    def from_env(cls):
        def flag(name):
            value = os.environ.get(name, "false").lower()
            if value not in {"true", "false"}:
                raise ValueError("Boolean configuration must be true or false.")
            return value == "true"
        limit = os.environ.get("ADVISOR_PERFORMANCE_TEST_MAX_CANDIDATES")
        return cls(service_key=os.environ.get("ADVISOR_API_KEY"), admin_key=os.environ.get("ADVISOR_ADMIN_API_KEY"),
                   finalization_key=os.environ.get("ADVISOR_FINALIZATION_API_KEY"),
                   direct_fetch_enabled=flag("ADVISOR_ENABLE_DIRECT_FETCH"),
                   student_api_url=os.environ.get("ADVISOR_STUDENT_API_URL"),
                   courses_api_url=os.environ.get("ADVISOR_COURSES_API_URL"),
                   courses_query_parameters=json.loads(os.environ["ADVISOR_COURSES_QUERY_PARAMETERS"]) if "ADVISOR_COURSES_QUERY_PARAMETERS" in os.environ else None,
                   api_timeout_seconds=float(os.environ.get("ADVISOR_API_TIMEOUT_SECONDS", "10")),
                   backend_token=os.environ.get("ADVISOR_BACKEND_TOKEN"),
                   allow_local_backend_http=flag("ADVISOR_ALLOW_LOCAL_BACKEND_HTTP"),
                   incremental_history_root=Path(os.environ.get("ADVISOR_HISTORY_INCREMENTAL_ROOT", paths.FROZEN_HISTORY_INCREMENTAL_DIR)),
                   history_baseline_source_root=Path(os.environ.get("ADVISOR_HISTORY_BASELINE_SOURCE_ROOT", paths.FROZEN_HISTORY_DIR_V2)),
                   history_update_mode=os.environ.get("ADVISOR_HISTORY_UPDATE_MODE", "manual"),
                   enable_backtesting=flag("ADVISOR_ENABLE_BACKTESTING"),
                   performance_test_mode=flag("ADVISOR_PERFORMANCE_TEST_MODE"),
                   performance_test_max_candidates=int(limit) if limit else None,
                   diploma_gpa_aliases=tuple(os.environ.get("ADVISOR_DIPLOMA_GPA_ALIASES", "diploma_gpa,DIPLOMA_GPA").split(",")),
                   diploma_type_aliases=tuple(os.environ.get("ADVISOR_DIPLOMA_TYPE_ALIASES", "diploma_type_id,DIPLOMA_TYPE_ID").split(",")))
