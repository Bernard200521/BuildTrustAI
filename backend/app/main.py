import os
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.app.config import settings
from backend.app.dependencies import get_repository, init_bootstrap_admin
from backend.app.api.auth import router as auth_router
from backend.app.api.projects import router as projects_router
from backend.app.api.releases import router as releases_router
from backend.app.api.evidence import router as evidence_router
from backend.app.api.assessments import router as assessments_router
from backend.app.api.dashboard import router as dashboard_router
from backend.app.api.events import router as events_router
from backend.app.api.simulator import router as simulator_router
from backend.app.simulator.live_stream import live_simulator

START_TIME = time.time()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure admin account exists
    try:
        repo = get_repository()
        init_bootstrap_admin(repo)
    except Exception as e:
        print(f"Warning during repository bootstrap: {e}")

    # Live telemetry simulator remains available on-demand via /api/v1/simulator endpoints
    yield

    # Shutdown
    if live_simulator.is_running:
        live_simulator.stop()

app = FastAPI(
    title="BuildTrust AI API",
    description="AI-Assisted Continuous Trust Verification and Risk-Adaptive Release Gate for Secure Software Supply Chains",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health & Readiness checks
@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "service": "BuildTrust AI",
        "uptime_seconds": round(time.time() - START_TIME, 2),
        "storage_backend": settings.STORAGE_BACKEND,
        "environment": settings.APP_ENV
    }

@app.get("/ready", tags=["System"])
def readiness_check():
    try:
        repo = get_repository()
        repo.list_projects()
        return {
            "status": "ready",
            "storage_backend": settings.STORAGE_BACKEND,
            "ml_enabled": settings.ML_ENABLED,
            "osv_api_enabled": settings.OSV_API_ENABLED,
            "live_telemetry_active": live_simulator.is_running
        }
    except Exception as e:
        return {
            "status": "not_ready",
            "error": str(e)
        }

# API v1 Router Registration
app.include_router(auth_router, prefix="/api/v1")
app.include_router(projects_router, prefix="/api/v1")
app.include_router(releases_router, prefix="/api/v1")
app.include_router(evidence_router, prefix="/api/v1")
app.include_router(assessments_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(events_router, prefix="/api/v1")
app.include_router(simulator_router, prefix="/api/v1")

# Mount Static Frontend if built
FRONTEND_DIST = os.path.abspath("frontend/dist")
if os.path.exists(FRONTEND_DIST):
    # Mount assets subfolder
    assets_dir = os.path.join(FRONTEND_DIST, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/", tags=["Frontend"])
    @app.get("/{full_path:path}", tags=["Frontend"])
    async def serve_frontend(full_path: str = ""):
        # Don't intercept API or docs routes
        if full_path.startswith("api/") or full_path in ("docs", "redoc", "openapi.json", "health", "ready"):
            return None
        file_path = os.path.join(FRONTEND_DIST, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))
