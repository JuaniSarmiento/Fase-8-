"""Auth use cases - login, register, current user.

Application layer for authentication in Fase 8.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Any

from backend.src_v3.infrastructure.persistence.repositories.user_repository import UserRepository, AuthUser
from backend.src_v3.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
)


# ==================== COMMANDS ====================


@dataclass
class LoginCommand:
    email: str
    password: str


@dataclass
class RegisterCommand:
    username: str
    email: str
    password: str
    full_name: Optional[str] = None
    role: str = "student"


# ==================== USE CASES ====================


class LoginUseCase:
    """Authenticate user and return tokens + user info."""

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def execute(self, command: LoginCommand) -> Dict[str, Any]:
        user = await self.user_repo.get_by_email(command.email)
        if not user or not user.hashed_password:
            raise ValueError("Invalid credentials")
        if not user.is_active:
            raise ValueError("Inactive user")
        if not verify_password(command.password, user.hashed_password):
            raise ValueError("Invalid credentials")

        user_id_str = str(user.id)
        access = create_access_token({"sub": user_id_str})
        refresh = create_refresh_token({"sub": user_id_str})

        return {
            "user": user,
            "tokens": {
                "access_token": access,
                "refresh_token": refresh,
                "token_type": "bearer",
            },
        }


class RegisterUserUseCase:
    """Register a new user with hashed password."""

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def execute(self, command: RegisterCommand) -> Dict[str, Any]:
        hashed = get_password_hash(command.password)
        base_role = command.role or "student"
        data = {
            "username": command.username,
            "email": command.email,
            "full_name": command.full_name,
            "role": base_role,
            "hashed_password": hashed,
            "roles": [base_role],
            "is_active": True,
        }
        user = await self.user_repo.create_user(data)
        user_id_str = str(user.id)
        access = create_access_token({"sub": user_id_str})
        refresh = create_refresh_token({"sub": user_id_str})
        return {
            "user": user,
            "tokens": {
                "access_token": access,
                "refresh_token": refresh,
                "token_type": "bearer",
            },
        }


class GetUserByIdUseCase:
    """Get user by id (used for /me)."""

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def execute(self, user_id: int) -> Optional[AuthUser]:
        return await self.user_repo.get_by_id(user_id)
