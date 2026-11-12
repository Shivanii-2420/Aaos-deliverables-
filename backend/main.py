import secrets

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from backend.app.config.settings import settings
from backend.app.core.logging_config import setup_logging
from backend.app.api.agent_api import router as agent_router
from backend.app.api.agent_version_api import router as version_router
from backend.app.api.test_run_api import router as test_run_router
from backend.app.api.evaluation_case_api import router as evaluation_case_router
from backend.app.api.evaluation_api import router as evaluation_router
from backend.app.api.evaluation_result_api import router as evaluation_result_router
from backend.app.api.evaluation_execution_api import router as execution_router
from backend.app.api.finding_api import router as finding_router
from backend.app.api.risk_score_api import router as risk_router
from backend.app.api.report import (    router as report_router)
from backend.app.api.certificate import (
    router as certificate_router
)
from backend.app.api.analytics_api import (
    router as analytics_router
)
from backend.app.api.attack_api import (
    router as attack_router
)
from backend.app.api.trace_api import (
    router as trace_router
)
from backend.app.api.llm_api import (
    router as llm_router
)
from backend.app.api.assurance_api import (
    router as assurance_router,
    tools_router as assurance_tools_router,
)
from backend.app.api.dataset_api import router as dataset_router
from backend.app import models  # ensure models are imported so ORM mappers are registered


setup_logging()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION
)

PUBLIC_PATHS = {
    "/", "/health", "/ui", "/docs", "/openapi.json", "/redoc",
    "/auth/status",
}


@app.middleware("http")
async def protect_api(request: Request, call_next):
    path = request.url.path
    if path in PUBLIC_PATHS or path.startswith("/static/"):
        return await call_next(request)

    configured_token = settings.API_TOKEN
    if configured_token:
        authorization = request.headers.get("authorization", "")
        scheme, _, supplied_token = authorization.partition(" ")
        if (
            scheme.lower() != "bearer"
            or not supplied_token
            or not secrets.compare_digest(supplied_token, configured_token)
        ):
            from fastapi.responses import JSONResponse

            return JSONResponse(
                status_code=401,
                content={"detail": "Valid AAOS bearer token required"},
                headers={"WWW-Authenticate": "Bearer"},
            )
    else:
        client_host = request.client.host if request.client else ""
        if client_host not in {"127.0.0.1", "::1", "localhost", "testclient"}:
            from fastapi.responses import JSONResponse

            return JSONResponse(
                status_code=403,
                content={"detail": "AAOS is restricted to loopback clients"},
            )
    return await call_next(request)

FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"

# Register the Agent API router
app.include_router(agent_router)

# Register the Agent Version API router
app.include_router(version_router)


# Register the Test Run API router
app.include_router(test_run_router)

# Register the Evaluation Case API router
app.include_router(evaluation_case_router)

# Register the Evaluation API router
app.include_router(evaluation_router)

# Register the Evaluation Result API router
app.include_router(evaluation_result_router)

# Register the Evaluation Execution API router
app.include_router(execution_router)

# Register Findings and Risk routers
app.include_router(finding_router)
app.include_router(risk_router)
app.include_router(    report_router)
app.include_router(
    certificate_router
)

# Register Analytics router
app.include_router(analytics_router)

# Register Flight Recorder and LLM router
app.include_router(trace_router)
app.include_router(attack_router)
app.include_router(llm_router)
app.include_router(assurance_router)
app.include_router(assurance_tools_router)
app.include_router(dataset_router)


@app.get("/")
def root():
    return {
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "provider_mode": settings.DEFAULT_LLM_PROVIDER
    }


@app.get("/auth/status")
def auth_status():
    return {
        "token_required": bool(settings.API_TOKEN),
        "local_only": not bool(settings.API_TOKEN),
        "auth_scheme": "Bearer",
    }


@app.get("/ui", include_in_schema=False)
def user_interface():
    return FileResponse(FRONTEND_DIR / "index.html")


app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR),
    name="static"
)
