"""InternSync API: application factory (Design 2)."""
import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.ai import embeddings
from app.attendance.router import router as attendance_router
from app.audit.router import router as audit_router
from app.auth.router import router as auth_router
from app.catalog.router import router as catalog_router
from app.core import errors
from app.core.config import get_settings
from app.core.db import get_db
from app.core.i18n import language_from_header, set_language
from app.cycles.router import router as cycles_router
from app.dashboard.router import router as dashboard_router
from app.dev.router import router as dev_router
from app.evaluations.router import router as evaluations_router
from app.files.router import router as files_router
from app.grades.router import router as grades_router
from app.matching.router import router as matching_router
from app.orgs.router import router as orgs_router
from app.profiles.router import router as profiles_router
from app.reports.router import router as reports_router
from app.vacancies.router import router as vacancies_router

API = "/api/v1"
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

system = APIRouter(tags=["system"])


@system.get("/health")
def health(deep: bool = False, db: Session = Depends(get_db)) -> dict:
    out = {"status": "ok"}
    if deep:
        db.execute(text("SELECT 1"))
        last = db.execute(text("SELECT max(finished_at) FROM job_runs")).scalar()
        embedder = embeddings.loaded()
        out.update(database="ok", scheduler_last_run=last.isoformat() if last else None,
                   model=embedder.version if embedder else None)
    return out


@system.get("/version")
def version() -> dict:
    embedder = embeddings.loaded()
    return {"version": get_settings().app_version, "embedding_model": embedder.version if embedder else None}


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = None
    if get_settings().env != "test":
        embeddings.warm_up()
    if get_settings().scheduler_enabled:
        from app.jobs.scheduler import start
        scheduler = start()
    yield
    if scheduler:
        scheduler.shutdown(wait=False)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="InternSync API", version=settings.app_version, lifespan=lifespan,
                  openapi_url=f"{API}/openapi.json", docs_url=f"{API}/docs", redoc_url=None)
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=False,
                       allow_methods=["*"], allow_headers=["*"])

    @app.middleware("http")
    async def language(request: Request, call_next):
        set_language(language_from_header(request.headers.get("accept-language")))
        return await call_next(request)

    errors.install(app)
    for r in (system, auth_router, orgs_router, cycles_router, catalog_router, profiles_router, vacancies_router,
              reports_router, audit_router, files_router, matching_router, attendance_router, evaluations_router,
              grades_router, dashboard_router):
        app.include_router(r, prefix=API)
    if settings.env in ("development", "test"):
        app.include_router(dev_router, prefix=API)
    return app


app = create_app()
