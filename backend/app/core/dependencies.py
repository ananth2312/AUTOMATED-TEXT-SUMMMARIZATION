"""
app/core/dependencies.py
────────────────────────
FastAPI dependency functions for:
- Extracting and validating the current user from a JWT Bearer token.
- Injecting the database connection.
"""

import logging
from typing import Annotated

from bson import ObjectId
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

from app.core.security import decode_access_token
from app.database import get_db

logger = logging.getLogger(__name__)

# Tells FastAPI where clients send tokens; used only for OpenAPI docs UI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db=Depends(get_db),
) -> dict:
    """
    Validate the Bearer JWT and return the user document from MongoDB.

    Raises HTTP 401 for any invalid/expired token.
    Raises HTTP 403 if the account is inactive.
    """
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id: str = payload.get("sub", "")
        if not user_id:
            raise credentials_exc
    except JWTError:
        raise credentials_exc

    try:
        oid = ObjectId(user_id)
    except Exception:
        raise credentials_exc

    user = db.users.find_one({"_id": oid})
    if user is None:
        raise credentials_exc

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive.",
        )

    return user


# Convenience alias – type-annotated for cleaner route signatures
CurrentUser = Annotated[dict, Depends(get_current_user)]
DB = Annotated[object, Depends(get_db)]
