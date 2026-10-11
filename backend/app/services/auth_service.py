"""
app/services/auth_service.py
─────────────────────────────
Authentication and user management service.

Handles registration, login, profile updates, and password changes.
Passwords are hashed with bcrypt before storage; plaintext is never retained.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from fastapi import HTTPException, status
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from app.config import get_settings
from app.core.security import create_access_token, hash_password, verify_password

logger = logging.getLogger(__name__)


# ── Registration ──────────────────────────────────────────────────────────────

def register_user(db: Database, name: str, email: str, password: str) -> dict:
    """
    Create a new user account.

    :raises HTTPException 409: If email is already registered.
    :returns: The new user document (without password_hash).
    """
    now = datetime.now(timezone.utc)
    normalized_email = email.lower().strip()
    if db.users.find_one({"email": normalized_email}):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists.",
        )

    user_doc = {
        "name": name.strip(),
        "email": normalized_email,
        "password_hash": hash_password(password),
        "role": "user",
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
    try:
        result = db.users.insert_one(user_doc)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists.",
        )

    user_doc["_id"] = str(result.inserted_id)
    user_doc.pop("password_hash", None)
    logger.info("Registered new user: %s", email)
    return user_doc


# ── Login ─────────────────────────────────────────────────────────────────────

def authenticate_user(db: Database, email: str, password: str) -> dict:
    """
    Verify credentials and return a JWT token response.

    Uses a generic error message to avoid leaking whether the email exists.
    :raises HTTPException 401: On invalid credentials or inactive account.
    """
    settings = get_settings()
    _GENERIC_ERROR = "Invalid email or password."

    user = db.users.find_one({"email": email.lower().strip()})
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_GENERIC_ERROR,
        )

    if not verify_password(password, user.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_GENERIC_ERROR,
        )

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated.",
        )

    token = create_access_token(subject=str(user["_id"]))
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


# ── Profile ───────────────────────────────────────────────────────────────────

def get_user_profile(user: dict) -> dict:
    """Return safe public profile fields (no password_hash)."""
    return {
        "_id": str(user["_id"]),
        "name": user.get("name", ""),
        "email": user.get("email", ""),
        "role": user.get("role", "user"),
        "created_at": user.get("created_at"),
        "updated_at": user.get("updated_at"),
    }


def update_user_profile(db: Database, user_id: str, name: Optional[str] = None) -> dict:
    """Update mutable profile fields."""
    updates: dict = {"updated_at": datetime.now(timezone.utc)}
    if name:
        updates["name"] = name.strip()

    db.users.update_one({"_id": ObjectId(user_id)}, {"$set": updates})
    updated = db.users.find_one({"_id": ObjectId(user_id)})
    return get_user_profile(updated)


def change_password(
    db: Database,
    user_id: str,
    current_password: str,
    new_password: str,
) -> None:
    """
    Change a user's password after verifying the current one.

    :raises HTTPException 401: If the current password is wrong.
    """
    user = db.users.find_one({"_id": ObjectId(user_id)})
    if not verify_password(current_password, user.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect.",
        )
    db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {
            "password_hash": hash_password(new_password),
            "updated_at": datetime.now(timezone.utc),
        }},
    )
    logger.info("Password changed for user %s", user_id)
