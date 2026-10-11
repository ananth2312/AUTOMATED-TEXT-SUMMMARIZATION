"""
app/database/connection.py
──────────────────────────
MongoDB connection management using PyMongo.
Provides a single MongoClient reused across the application lifetime,
with a startup health check and a graceful shutdown.
"""

import logging
from typing import Optional

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from app.config import get_settings

logger = logging.getLogger(__name__)

# Module-level singleton – set once on startup
_client: Optional[MongoClient] = None
_db: Optional[Database] = None


def connect_db() -> None:
    """
    Create the MongoClient and verify the connection.
    Called from the FastAPI lifespan handler so it runs once at startup.
    Raises ConnectionFailure if MongoDB is unreachable.
    """
    global _client, _db
    settings = get_settings()

    logger.info("Connecting to MongoDB at %s …", settings.MONGODB_URL)
    _client = MongoClient(
        settings.MONGODB_URL,
        serverSelectionTimeoutMS=5000,   # fail fast in dev
    )

    # Ping to verify connectivity before accepting traffic
    try:
        _client.admin.command("ping")
        logger.info("MongoDB connection established. Database: %s", settings.MONGODB_DB_NAME)
    except (ConnectionFailure, ServerSelectionTimeoutError) as exc:
        logger.error("Could not connect to MongoDB: %s", exc)
        raise

    _db = _client[settings.MONGODB_DB_NAME]
    _ensure_indexes()


def disconnect_db() -> None:
    """Close the MongoClient cleanly on application shutdown."""
    global _client, _db
    if _client:
        _client.close()
        logger.info("MongoDB connection closed.")
        _client = None
        _db = None


def get_db() -> Database:
    """
    Return the active database instance.
    Use as a FastAPI dependency:

        db: Database = Depends(get_db)
    """
    if _db is None:
        raise RuntimeError(
            "Database not initialised. Ensure connect_db() is called at startup."
        )
    return _db


# ── Index definitions ────────────────────────────────────────────────────────

def _ensure_indexes() -> None:
    """Create indexes that do not yet exist (idempotent)."""
    db = _db
    assert db is not None

    # users – unique email lookup
    db.users.create_index("email", unique=True, background=True)
    db.users.create_index("created_at", background=True)

    # documents – per-user listing, title search
    db.documents.create_index("user_id", background=True)
    db.documents.create_index("created_at", background=True)
    db.documents.create_index([("user_id", 1), ("created_at", -1)], background=True)

    # analyses – per-user and per-document lookup
    db.analyses.create_index("user_id", background=True)
    db.analyses.create_index("document_id", background=True)
    db.analyses.create_index([("user_id", 1), ("created_at", -1)], background=True)

    # audit_logs
    db.audit_logs.create_index("user_id", background=True)
    db.audit_logs.create_index("created_at", background=True)

    logger.info("MongoDB indexes verified.")
