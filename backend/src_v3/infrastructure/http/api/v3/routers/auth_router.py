"""Authentication HTTP Router - API v3

Provides minimal auth endpoints for Fase 8:
- POST /auth/login  (JSON email/password)
- POST /auth/token  (OAuth2 form for Swagger)
- POST /auth/register
- GET  /auth/me
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr

from sqlalchemy.ext.asyncio import AsyncSession

from backend.src_v3.infrastructure.persistence.database import get_db_session
from backend.src_v3.infrastructure.persistence.repositories.user_repository import AuthUser
from backend.src_v3.infrastructure.dependencies import (
    get_login_use_case,
    get_register_user_use_case,
    get_get_user_by_id_use_case,
)
from backend.src_v3.application.auth.use_cases import (
    LoginUseCase,
    RegisterUserUseCase,
    GetUserByIdUseCase,
)
from backend.src_v3.core.security import get_user_id_from_token


router = APIRouter(prefix="/auth", tags=["Authentication"])

# OAuth2 scheme for Bearer tokens
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v3/auth/token")


# ==================== SCHEMAS ====================


class TokensSchema(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str  # Changed from int to str to match VARCHAR(36)
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    roles: List[str] = []
    is_active: bool = True


class UserWithTokensResponse(BaseModel):
    user: UserResponse
    tokens: TokensSchema


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: str = "student"


# ==================== HELPERS ====================


def _auth_user_to_response(user: AuthUser) -> UserResponse:
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        roles=user.roles or [user.role],
        is_active=user.is_active,
    )


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db_session),
) -> AuthUser:
    """Resolve current user from Bearer token."""
    user_id_str = get_user_id_from_token(token)
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user id in token",
        )

    use_case: GetUserByIdUseCase = get_get_user_by_id_use_case(db)
    user = await use_case.execute(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return user


# ==================== ENDPOINTS ====================


@router.post("/login", response_model=UserWithTokensResponse, status_code=status.HTTP_200_OK)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """JSON login endpoint (email + password)."""
    use_case: LoginUseCase = get_login_use_case(db)
    try:
        result = await use_case.execute(
            command=
            # type: ignore[arg-type]
            # Pydantic model is compatible with dataclass fields
            payload  # LoginCommand(email=payload.email, password=payload.password)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )

    user: AuthUser = result["user"]
    tokens = result["tokens"]
    return UserWithTokensResponse(
        user=_auth_user_to_response(user),
        tokens=TokensSchema(**tokens),
    )


@router.post("/token", response_model=TokensSchema)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db_session),
):
    """OAuth2 Password flow endpoint for Swagger UI."""
    use_case: LoginUseCase = get_login_use_case(db)
    try:
        result = await use_case.execute(
            # type: ignore[arg-type]
            LoginRequest(email=form_data.username, password=form_data.password)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )

    tokens = result["tokens"]
    return TokensSchema(**tokens)


@router.post("/register", response_model=UserWithTokensResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Register new user with email/password."""
    use_case: RegisterUserUseCase = get_register_user_use_case(db)
    # Basic normalization of role
    role = (payload.role or "student").lower().strip()
    if role not in {"student", "teacher", "admin"}:
        role = "student"
    from backend.src_v3.application.auth.use_cases import RegisterCommand

    try:
        result = await use_case.execute(
            RegisterCommand(
                username=payload.username,
                email=payload.email,
                password=payload.password,
                full_name=payload.full_name,
                role=role,
            )
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    user: AuthUser = result["user"]
    tokens = result["tokens"]
    return UserWithTokensResponse(
        user=_auth_user_to_response(user),
        tokens=TokensSchema(**tokens),
    )


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: AuthUser = Depends(get_current_user)):
    """Return current authenticated user info."""
    return _auth_user_to_response(current_user)
