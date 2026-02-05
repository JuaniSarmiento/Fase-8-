"""User repository for authentication in Fase 8.

Uses async SQL (no ORM) over the `users` table created in create_tables_v2_clean.sql.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


@dataclass
class AuthUser:
    id: str  # Changed from int to str to match VARCHAR(36)
    username: str
    email: str
    full_name: Optional[str]
    role: str
    roles: List[str]
    hashed_password: str
    is_active: bool


class UserRepository:
    """Persistence operations for users (auth-focused)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> Optional[AuthUser]:
        query = text(
            """
            SELECT id, username, email, full_name, roles, hashed_password, is_active
            FROM users
            WHERE email = :email
            """
        )
        result = await self.db.execute(query, {"email": email})
        row = result.fetchone()
        if not row:
            return None

        roles = row[4] or []
        if isinstance(roles, dict):  # just in case of bad data
            roles = list(roles.values())
        
        # Derive primary role from roles list
        primary_role = "student"  # default
        if roles:
            if "admin" in roles:
                primary_role = "admin"
            elif "teacher" in roles:
                primary_role = "teacher"
            elif "student" in roles:
                primary_role = "student"
        
        return AuthUser(
            id=row[0],
            username=row[1],
            email=row[2],
            full_name=row[3],
            role=primary_role,
            roles=list(roles),
            hashed_password=row[5] or "",
            is_active=bool(row[6]),
        )

    async def get_by_id(self, user_id: str) -> Optional[AuthUser]:  # Changed from int to str
        query = text(
            """
            SELECT id, username, email, full_name, roles, hashed_password, is_active
            FROM users
            WHERE id = :user_id
            """
        )
        result = await self.db.execute(query, {"user_id": user_id})
        row = result.fetchone()
        if not row:
            return None

        roles = row[4] or []
        if isinstance(roles, dict):
            roles = list(roles.values())
        
        # Derive primary role from roles list
        primary_role = "student"  # default
        if roles:
            if "admin" in roles:
                primary_role = "admin"
            elif "teacher" in roles:
                primary_role = "teacher"
            elif "student" in roles:
                primary_role = "student"
        
        return AuthUser(
            id=row[0],
            username=row[1],
            email=row[2],
            full_name=row[3],
            role=primary_role,
            roles=list(roles),
            hashed_password=row[5] or "",
            is_active=bool(row[6]),
        )

    async def create_user(self, data: Dict[str, Any]) -> AuthUser:
        """Create a new user. Expects hashed_password already computed."""
        import json
        import uuid
        import logging
        from sqlalchemy.exc import IntegrityError
        
        logger = logging.getLogger(__name__)
        
        # Verificar si el email ya existe
        existing_email = await self.get_by_email(data["email"])
        if existing_email:
            logger.warning(f"Attempt to create user with existing email: {data['email']}")
            raise ValueError("Email already registered")
        
        # Verificar si el username ya existe
        check_username_query = text(
            "SELECT id FROM users WHERE username = :username"
        )
        result = await self.db.execute(check_username_query, {"username": data["username"]})
        if result.fetchone():
            logger.warning(f"Attempt to create user with existing username: {data['username']}")
            raise ValueError("Username already exists")
        
        user_id = str(uuid.uuid4())
        query = text(
            """
            INSERT INTO users (id, username, email, full_name, hashed_password, roles, is_active, created_at, updated_at)
            VALUES (:id, :username, :email, :full_name, :hashed_password, CAST(:roles AS jsonb), :is_active, NOW(), NOW())
            RETURNING id, username, email, full_name, roles, hashed_password, is_active
            """
        )
        roles_list = data.get("roles") or [data.get("role", "STUDENT").upper()]
        params = {
            "id": user_id,
            "username": data["username"],
            "email": data["email"],
            "full_name": data.get("full_name"),
            "hashed_password": data["hashed_password"],
            "roles": json.dumps(roles_list),
            "is_active": data.get("is_active", True),
        }
        
        try:
            result = await self.db.execute(query, params)
            row = result.fetchone()
            await self.db.commit()
            logger.info(f"User created successfully: {data['username']} (ID: {user_id})")
        except IntegrityError as e:
            await self.db.rollback()
            logger.error(f"Integrity error creating user: {e}")
            raise ValueError("Failed to create user: username or email already exists")
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Unexpected error creating user: {e}", exc_info=True)
            raise

        # RETURNING: id, username, email, full_name, roles, hashed_password, is_active
        roles = row[4] or []
        return AuthUser(
            id=row[0],
            username=row[1],
            email=row[2],
            full_name=row[3],
            role=roles[0] if roles else "STUDENT",
            roles=list(roles),
            hashed_password=row[5] or "",
            is_active=bool(row[6]),
        )
