"""
app/config.py
─────────────
Loads and validates all application configuration from environment variables.
Uses pydantic-settings so every missing required variable raises an error at startup,
not at runtime when the value is first used.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central settings object – injected via FastAPI dependency injection."""

    model_config = SettingsConfigDict(
        env_file=".env",          # reads from .env in the backend working directory
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── MongoDB ──────────────────────────────────────────────────────────────
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "academic_research_db"

    # ── JWT ──────────────────────────────────────────────────────────────────
    SECRET_KEY: str = "change-me-to-a-long-random-secret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ── File storage ─────────────────────────────────────────────────────────
    STORAGE_DIR: str = "../../storage"

    # ── Upload limits ─────────────────────────────────────────────────────────
    MAX_UPLOAD_SIZE: int = 20 * 1024 * 1024   # 20 MB
    ALLOWED_EXTENSIONS: list[str] = [".pdf"]

    # ── CORS ──────────────────────────────────────────────────────────────────
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # ── Application ───────────────────────────────────────────────────────────
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    # ── NLP defaults ──────────────────────────────────────────────────────────
    MAX_KEY_PHRASES: int = 20
    WORDS_PER_MINUTE: int = 200   # assumed reading speed

    # ── Computed helpers ──────────────────────────────────────────────────────
    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def storage_path(self) -> Path:
        p = Path(self.STORAGE_DIR)
        if not p.is_absolute():
            # resolve relative to this file's location (backend/app/)
            p = Path(__file__).parent.parent / p
        p.mkdir(parents=True, exist_ok=True)
        return p.resolve()


@lru_cache()
def get_settings() -> Settings:
    """Return a cached Settings instance (called once per process)."""
    return Settings()
