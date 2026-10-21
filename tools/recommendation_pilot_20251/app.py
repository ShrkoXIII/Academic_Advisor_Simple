"""Loopback-only API, independent of production FastAPI contracts."""
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr

from .adapter import PILOT_ROOT, PilotInputError, read_students, load_student_inputs
from .runner import ComparisonRunner, json_value
from .observed import ObservedPlanStore, unavailable
from .observed_prediction import ObservedPlanPredictor, blocked_forecast


class RunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sample_ids: list[StrictStr] = Field(min_length=1, max_length=30)
    target_credits: float = Field(default=18, gt=0, le=36, allow_inf_nan=False)
    max_plans: StrictInt = Field(default=200, ge=1, le=2000)


def create_app(root=PILOT_ROOT, *, engine_factory=None, observed_store=None, observed_predictor=None):
    runner = ComparisonRunner(root, engine_factory=engine_factory)
    observed = observed_store if observed_store is not None else ObservedPlanStore()
    actual_predictor = observed_predictor if observed_predictor is not None else ObservedPlanPredictor(root)

    @asynccontextmanager
    async def lifespan(app):
        yield
        runner.executor.shutdown(wait=True)

    app = FastAPI(title="Academic Advisor — Pilot 20251", lifespan=lifespan, docs_url=None, redoc_url=None)
    app.state.runner = runner

    @app.middleware("http")
    async def local_only(request: Request, call_next):
        host = request.headers.get("host", "").split(":")[0]
        origin = request.headers.get("origin")
        if host != "127.0.0.1" or (origin and (urlsplit(origin).scheme != "http" or urlsplit(origin).netloc != request.headers.get("host"))):
            return JSONResponse({"detail": "Loopback same-origin access only."}, status_code=403)
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; frame-ancestors 'none'"
        return response

    @app.get("/api/students")
    def students():
        from .engine import build_snapshot, student_summary
        rows = read_students(root)
        for student in rows:
            try:
                snapshot, _ = build_snapshot(load_student_inputs(student, root))
                student["student_summary"] = student_summary(snapshot, student)
            except PilotInputError as error:
                student["student_summary"] = {"status": "UNAVAILABLE", "reason": error.code}
        return {"students": rows, "count": len(rows)}

    @app.get("/api/status")
    def status():
        return JSONResponse(json_value(runner.status()))

    @app.post("/api/runs", status_code=202)
    def run(payload: RunRequest):
        try:
            run_id = runner.start(payload.sample_ids, target_credits=payload.target_credits, max_plans=payload.max_plans)
        except ValueError as error:
            raise HTTPException(422, str(error)) from None
        return {"run_id": run_id}

    @app.get("/api/runs")
    def list_runs():
        return {"runs": runner.store.list_runs()}

    @app.get("/api/runs/{run_id}/progress")
    def progress(run_id: str):
        try:
            return runner.progress(run_id)
        except (ValueError, OSError):
            raise HTTPException(404, "Run not found.") from None

    @app.get("/api/runs/{run_id}")
    def saved_run(run_id: str):
        try:
            saved = runner.store.load(run_id)
        except (ValueError, OSError):
            raise HTTPException(404, "Run not found.") from None
        try:
            cohort = {student["sample_id"]: student for student in read_students(root)}
        except (ValueError, OSError):
            cohort = {}
        actual_cases = []
        for result in saved["student_results"]:
            student = None
            try:
                student = cohort.get(result.get("sample_id"))
                if (student is not None and str(result.get("student_id")) == str(student["student_id"]) and
                        saved["run_manifest"].get("part_id") == int(student["part_id"])):
                    result["observed_plan"] = observed.get(student)
                else:
                    result["observed_plan"] = unavailable("OBSERVED_IDENTITY_UNVERIFIED", "هوية الطالب أو فصل التشغيل لا يطابقان العينة المحفوظة.")
            except (ValueError, OSError, KeyError, TypeError):
                result["observed_plan"] = unavailable("OBSERVED_SOURCE_UNAVAILABLE", "تعذر قراءة بيانات الخطة الفعلية؛ تبقى توقعات النماذج متاحة.")
            try:
                actual = result["observed_plan"]
                if student is not None and actual["status"] in {"AVAILABLE", "PARTIAL"}:
                    registrations = [{"course_id": course["course_id"], "course_credits": course["course_credits"]}
                                     for course in actual["courses"]]
                    actual_cases.append((result, student, registrations))
                else:
                    result["observed_plan_prediction"] = blocked_forecast()
            except (ValueError, OSError, KeyError, TypeError):
                result["observed_plan_prediction"] = blocked_forecast()
        if actual_cases:
            try:
                cases = [(student, registrations) for _, student, registrations in actual_cases]
                predictions = (actual_predictor.predict_many(cases) if hasattr(actual_predictor, "predict_many")
                               else [actual_predictor.predict(student, registrations) for student, registrations in cases])
                if len(predictions) != len(actual_cases):
                    raise ValueError("Incomplete actual-plan forecasts.")
                for (result, _, _), prediction in zip(actual_cases, predictions):
                    result["observed_plan_prediction"] = prediction
                    prediction["registration_source_sha256"] = result["observed_plan"].get("source", {}).get("roster_sha256")
            except (ValueError, OSError, KeyError, TypeError):
                for result, _, _ in actual_cases:
                    result["observed_plan_prediction"] = blocked_forecast()
        return JSONResponse(json_value(saved))

    static = Path(__file__).parent / "static"
    static.mkdir(exist_ok=True)
    app.mount("/static", StaticFiles(directory=static), name="static")

    @app.get("/")
    def index():
        return FileResponse(static / "index.html")

    return app
