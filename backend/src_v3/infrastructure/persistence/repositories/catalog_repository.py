"""Catalog Repository - Subjects, Courses, Commissions.

Async access layer for the academic structure used by teacher/student modules.

NOTE: This repository uses raw SQL aligned with the V2 schema defined in
`create_tables_v2_clean.sql`, instead of ORM models that target an
alternative normalized schema.
"""
from __future__ import annotations

from typing import List, Optional, Dict, Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class CatalogRepository:
    """Read-only catalog repository for academic structure (V2 schema)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ---------- Subjects ----------

    async def get_subjects(self, active_only: bool = True) -> List[Dict[str, Any]]:
        # subjects table has no is_active flag in V2 schema
        result = await self._session.execute(
            text("SELECT id, code, name, description, credits FROM subjects ORDER BY name")
        )
        return [dict(row._mapping) for row in result]

    async def get_subject_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        result = await self._session.execute(
            text("SELECT id, code, name, description, credits FROM subjects WHERE code = :code")
            .bindparams(code=code)
        )
        row = result.first()
        return dict(row._mapping) if row else None

    # ---------- Courses ----------

    async def get_courses_for_subject(
        self,
        subject_id: int,
        active_only: bool = True,
    ) -> List[Dict[str, Any]]:
        # courses table has (id, subject_id, year, semester, start_date, end_date, ...)
        result = await self._session.execute(
            text(
                """
                SELECT id, subject_id, year, semester, start_date, end_date
                FROM courses
                WHERE subject_id = :subject_id
                ORDER BY year DESC, semester DESC
                """
            ).bindparams(subject_id=subject_id)
        )
        return [dict(row._mapping) for row in result]

    async def get_course_by_id(self, course_id: int) -> Optional[Dict[str, Any]]:
        result = await self._session.execute(
            text(
                "SELECT id, subject_id, year, semester, start_date, end_date FROM courses WHERE id = :course_id"
            ).bindparams(course_id=course_id)
        )
        row = result.first()
        return dict(row._mapping) if row else None

    # ---------- Commissions ----------

    async def get_commissions_for_course(
        self,
        course_id: int,
        active_only: bool = True,
    ) -> List[Dict[str, Any]]:
        # commissions has no explicit active flag; we ignore active_only for now
        result = await self._session.execute(
            text(
                """
                SELECT id, course_id, code, schedule, NULL::INTEGER AS capacity
                FROM commissions
                WHERE course_id = :course_id
                ORDER BY code
                """
            ).bindparams(course_id=course_id)
        )
        return [dict(row._mapping) for row in result]

    async def get_commission_by_id(self, commission_id: int) -> Optional[Dict[str, Any]]:
        result = await self._session.execute(
            text(
                "SELECT id, course_id, code, schedule, NULL::INTEGER AS capacity FROM commissions WHERE id = :commission_id"
            ).bindparams(commission_id=commission_id)
        )
        row = result.first()
        return dict(row._mapping) if row else None
