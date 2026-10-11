"""
app/api/routes/auth.py
───────────────────────
Authentication endpoints:
  POST /api/auth/register
  POST /api/auth/login
  GET  /api/auth/me
  PATCH /api/auth/profile
  POST  /api/auth/change-password
"""

from fastapi import APIRouter, Depends, status
from pymongo.database import Database

from app.core.dependencies import CurrentUser, get_db
from app.schemas import (
    ChangePasswordRequest,
    LoginRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
    UpdateProfileRequest,
    UserProfile,
)
from app.services import (
    authenticate_user,
    change_password,
    get_user_profile,
    register_user,
    update_user_profile,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
def register(body: RegisterRequest, db: Database = Depends(get_db)):
    user = register_user(db, name=body.name, email=body.email, password=body.password)
    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log in and receive a JWT access token",
)
def login(body: LoginRequest, db: Database = Depends(get_db)):
    return authenticate_user(db, email=body.email, password=body.password)


@router.get(
    "/me",
    response_model=UserProfile,
    summary="Return the authenticated user's profile",
)
def get_me(current_user: CurrentUser):
    return get_user_profile(current_user)


@router.patch(
    "/profile",
    response_model=UserProfile,
    summary="Update profile fields (name)",
)
def update_profile(
    body: UpdateProfileRequest,
    current_user: CurrentUser,
    db: Database = Depends(get_db),
):
    return update_user_profile(db, user_id=str(current_user["_id"]), name=body.name)


@router.post(
    "/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change the authenticated user's password",
)
def change_pw(
    body: ChangePasswordRequest,
    current_user: CurrentUser,
    db: Database = Depends(get_db),
):
    change_password(
        db,
        user_id=str(current_user["_id"]),
        current_password=body.current_password,
        new_password=body.new_password,
    )
