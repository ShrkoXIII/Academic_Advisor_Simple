"""Optional FastAPI transport. Importing this module never loads artifacts."""
from contextlib import asynccontextmanager
from decimal import Decimal
import json
from secrets import compare_digest

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from starlette.concurrency import run_in_threadpool

from .schemas import StudentValidationRequest, CoursesValidationRequest, RecommendationRequest, HistoryDeltaRequest
from .service import ApiService
from .settings import ApiSettings
from .validation import ApiError, json_safe


class DecimalRequest(Request):
    async def json(self):
        if not hasattr(self, "_json"):
            body = await self.body()
            def reject_constant(value):
                raise json.JSONDecodeError("Nonfinite JSON numbers are unsupported.", "", 0)
            self._json = json.loads(body, parse_float=Decimal, parse_constant=reject_constant)
        return self._json


class DecimalRoute(APIRoute):
    def get_route_handler(self):
        handler = super().get_route_handler()
        async def preserve_credit_precision(request):
            try:
                return await handler(DecimalRequest(request.scope, request.receive))
            except (ApiError, RequestValidationError, HTTPException):
                raise
            except Exception:
                # A generic Exception handler still rethrows to the ASGI server.
                # Convert at the route boundary so private tracebacks never leak.
                raise ApiError("INTERNAL_ERROR", "Request could not be completed.", status_code=500) from None
        return preserve_credit_precision


def create_app(*, settings=None, service=None):
    """Create an app; injected services are already initialized for tests/tools."""
    api = service or ApiService(settings=settings or ApiSettings.from_env())
    @asynccontextmanager
    async def lifespan(app):
        if service is None:
            await run_in_threadpool(api.initialize)
        yield
    app = FastAPI(title="Academic Advisor Integration", version="1.0", lifespan=lifespan)
    app.router.route_class = DecimalRoute
    app.state.api_service = api

    def authenticate(value, *, admin=False):
        expected = api.settings.admin_key if admin else api.settings.service_key
        if not expected:
            raise ApiError("AUTH_UNCONFIGURED", "Service authentication is unavailable.", status_code=503)
        if value is None:
            raise ApiError("AUTH_REQUIRED", "A service credential is required.", status_code=401)
        if not compare_digest(value.encode("utf8"), expected.encode("utf8")):
            raise ApiError("AUTH_FORBIDDEN", "Service credential is not authorized.", status_code=403)

    def service_auth(x_api_key: str | None = Header(default=None)):
        authenticate(x_api_key)

    def admin_auth(x_api_key: str | None = Header(default=None)):
        authenticate(x_api_key, admin=True)

    @app.exception_handler(ApiError)
    async def api_error(request, error):
        return JSONResponse(status_code=error.status_code, content=json_safe({"error": error.issue}))

    @app.exception_handler(RequestValidationError)
    async def schema_error(request, error):
        # Pydantic's input/context and arbitrary dictionary keys may contain PII.
        return JSONResponse(status_code=422, content={"error": {"code": "INVALID_REQUEST_SCHEMA",
                            "message": "Request does not satisfy the documented HTTP schema."}})

    @app.exception_handler(Exception)
    async def internal_error(request, error):
        return JSONResponse(status_code=500, content={"error": {"code": "INTERNAL_ERROR",
                            "message": "Request could not be completed."}})

    def diagnostic(result):
        return JSONResponse(status_code=result.http_status, content=json_safe(result.public()))

    @app.get("/health")
    async def health():
        return api.health()

    @app.post("/api/v1/inputs/student/validate", dependencies=[Depends(service_auth)])
    async def validate_student(body: StudentValidationRequest):
        return diagnostic(await run_in_threadpool(api.validate_student, body.model_dump()))

    @app.post("/api/v1/inputs/courses/validate", dependencies=[Depends(service_auth)])
    async def validate_courses(body: CoursesValidationRequest):
        return diagnostic(await run_in_threadpool(api.validate_courses, body.model_dump()))

    @app.post("/api/v1/recommendations", dependencies=[Depends(service_auth)])
    async def recommend(body: RecommendationRequest):
        result = await run_in_threadpool(api.recommend, body.model_dump())
        return JSONResponse(content=json_safe(result))

    @app.post("/api/v1/history/deltas/validate", dependencies=[Depends(admin_auth)])
    async def validate_delta(body: HistoryDeltaRequest):
        return diagnostic(await run_in_threadpool(api.validate_delta, body.model_dump()))

    return app
