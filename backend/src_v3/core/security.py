"""Security utilities for Fase 8 (JWT + password hashing).

Based on Fase 7 core.security but simplified and adapted to src_v3.
"""
from __future__ import annotations

import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from jose import JWTError, jwt
import bcrypt

logger = logging.getLogger(__name__)


# ==================== CONFIG ====================

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))

_is_production = os.getenv("ENVIRONMENT", "development").lower() == "production"

if not SECRET_KEY:
    if _is_production:
        raise RuntimeError(
            "SECURITY ERROR: JWT_SECRET_KEY environment variable is REQUIRED in production."
        )
    else:
        # Generar clave aleatoria para desarrollo
        import secrets
        SECRET_KEY = secrets.token_hex(32)
        logger.warning(
            "WARNING: Generated random JWT_SECRET_KEY for development. "
            "For production, set JWT_SECRET_KEY in environment with: python -c 'import secrets; print(secrets.token_hex(32))'"
        )

if _is_production and len(SECRET_KEY) < 32:
    raise RuntimeError(
        f"SECURITY ERROR: JWT_SECRET_KEY must be at least 32 characters long. "
        f"Current length: {len(SECRET_KEY)}."
    )


def utc_now() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


# ==================== PASSWORD HASHING ====================


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a bcrypt hash."""
    try:
        password_bytes = plain_password.encode("utf-8")[:72]
        return bcrypt.checkpw(password_bytes, hashed_password.encode("utf-8"))
    except Exception as e:  # pragma: no cover - defensive
        logger.error("Password verification error: %s", e, exc_info=True)
        return False


def get_password_hash(password: str) -> str:
    """Hash password with bcrypt (12 rounds)."""
    password_bytes = password.encode("utf-8")[:72]
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=12)).decode("utf-8")


hash_password = get_password_hash


# ==================== JWT TOKENS ====================


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = utc_now() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = utc_now() + (expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


class TokenError(Exception):
    """Base exception for token-related errors."""


class TokenExpiredError(TokenError):
    """Raised when token has expired."""


class TokenInvalidError(TokenError):
    """Raised when token is malformed or invalid."""


def decode_access_token(token: str, raise_on_error: bool = False) -> Optional[Dict[str, Any]]:
    """Decode and validate a JWT token. Returns payload or None."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError as e:  # type: ignore[attr-defined]
        logger.debug("JWT expired: %s", e)
        if raise_on_error:
            raise TokenExpiredError("Token has expired") from e
        return None
    except JWTError as e:
        logger.debug("JWT decode error: %s", e)
        if raise_on_error:
            raise TokenInvalidError("Invalid token format or signature") from e
        return None
    except Exception as e:  # pragma: no cover - defensive
        logger.error("Token decode error: %s", e, exc_info=True)
        if raise_on_error:
            raise TokenInvalidError("Token validation failed") from e
        return None


def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    payload = decode_access_token(token)
    if not payload:
        return None
    if payload.get("type") and payload.get("type") != token_type:
        logger.warning("Token type mismatch: expected %s, got %s", token_type, payload.get("type"))
        return None
    return payload


def get_user_id_from_token(token: str) -> Optional[str]:
    payload = verify_token(token, token_type="access")
    if not payload:
        return None
    sub = payload.get("sub")
    return str(sub) if sub is not None else None


def create_token_pair(user_id: str) -> Dict[str, str]:
    access = create_access_token({"sub": user_id})
    refresh = create_refresh_token({"sub": user_id})
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}


def refresh_access_token(refresh_token: str) -> Optional[str]:
    payload = verify_token(refresh_token, token_type="refresh")
    if not payload:
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    return create_access_token({"sub": user_id})
