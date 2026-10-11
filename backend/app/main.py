"""
app/main.py
────────────
FastAPI application entry point.

- Configures CORS, logging, and lifespan (startup/shutdown).
- Registers all API routers.
- Exposes /api/health for monitoring.
- Generates OpenAPI docs at /docs (Swagger) and /redoc.
"""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, documents, analyses
from app.config import get_settings
from app.database import connect_db, disconnect_db

# ── Logging ───────────────────────────────────────────────────────────────────

def _configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

settings = get_settings()
_configure_logging(settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: connect to DB.  Shutdown: close DB connection."""
    logger.info("Starting Academic Research Summarizer API …")
    connect_db()
    yield
    logger.info("Shutting down …")
    disconnect_db()


# ── Application factory ───────────────────────────────────────────────────────

app = FastAPI(
    title="Academic Research Summarizer API",
    description=(
        "REST API for automated text summarisation and key-phrase extraction "
        "from academic research papers. NLP outputs are machine-generated estimates "
        "and should be reviewed by the user."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(auth.router,      prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(analyses.router,  prefix="/api")


# ── Health endpoint ───────────────────────────────────────────────────────────

@app.get("/api/health", tags=["System"], summary="API health check")
def health():
    """
    Returns application version and MongoDB connectivity status.
    Used by CI, monitoring, and the frontend startup check.
    """
    from app.database.connection import _db
    db_ok = _db is not None
    try:
        if db_ok:
            _db.command("ping")
    except Exception:
        db_ok = False

    return {
        "status": "ok" if db_ok else "degraded",
        "version": "1.0.0",
        "database": "connected" if db_ok else "unreachable",
    }


# ── Root redirect ─────────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
def root():
    return {"message": "Academic Research Summarizer API. See /docs for documentation."}
