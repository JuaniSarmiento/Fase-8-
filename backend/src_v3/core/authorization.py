"""Authorization Dependencies for Role-Based Access Control.

Protects endpoints by verifying user roles.
"""
from __future__ import annotations

from typing import List
from fastapi import Depends, HTTPException, status

from backend.src_v3.infrastructure.http.api.v3.routers.auth_router import get_current_user
from backend.src_v3.infrastructure.persistence.repositories.user_repository import AuthUser


def require_roles(allowed_roles: List[str]):
    """Dependency to require specific roles.
    
    Usage:
        @router.get("/admin/users", dependencies=[Depends(require_roles(["admin"]))])
        async def get_users():
            ...
    """
    async def check_role(current_user: AuthUser = Depends(get_current_user)):
        user_roles = current_user.roles or []
        
        # Check if user has any of the allowed roles
        if not any(role in user_roles for role in allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
            )
        
        return current_user
    
    return check_role


def require_teacher(current_user: AuthUser = Depends(get_current_user)) -> AuthUser:
    """Require teacher role."""
    user_roles = current_user.roles or []
    if "teacher" not in user_roles and "admin" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Teacher role required."
        )
    return current_user


def require_student(current_user: AuthUser = Depends(get_current_user)) -> AuthUser:
    """Require student role."""
    user_roles = current_user.roles or []
    if "student" not in user_roles and "admin" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Student role required."
        )
    return current_user


def require_admin(current_user: AuthUser = Depends(get_current_user)) -> AuthUser:
    """Require admin role."""
    user_roles = current_user.roles or []
    if "admin" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin role required."
        )
    return current_user


def require_active_user(current_user: AuthUser = Depends(get_current_user)) -> AuthUser:
    """Require active user account."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact support."
        )
    return current_user
