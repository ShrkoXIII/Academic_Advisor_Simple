"""Environment-only transport configuration; no academic policy defaults."""
from dataclasses import dataclass, field
import os


@dataclass(frozen=True)
class ApiSettings:
    service_key: str | None = field(default=None, repr=False)
    admin_key: str | None = field(default=None, repr=False)
    enable_backtesting: bool = False
    performance_test_mode: bool = False
    performance_test_max_candidates: int | None = None
    diploma_gpa_aliases: tuple = ("diploma_gpa", "DIPLOMA_GPA")
    diploma_type_aliases: tuple = ("diploma_type_id", "DIPLOMA_TYPE_ID")

    def __post_init__(self):
        if self.service_key and self.admin_key and self.service_key == self.admin_key:
            raise ValueError("Service and administrative keys must be distinct.")
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
                   enable_backtesting=flag("ADVISOR_ENABLE_BACKTESTING"),
                   performance_test_mode=flag("ADVISOR_PERFORMANCE_TEST_MODE"),
                   performance_test_max_candidates=int(limit) if limit else None,
                   diploma_gpa_aliases=tuple(os.environ.get("ADVISOR_DIPLOMA_GPA_ALIASES", "diploma_gpa,DIPLOMA_GPA").split(",")),
                   diploma_type_aliases=tuple(os.environ.get("ADVISOR_DIPLOMA_TYPE_ALIASES", "diploma_type_id,DIPLOMA_TYPE_ID").split(",")))
