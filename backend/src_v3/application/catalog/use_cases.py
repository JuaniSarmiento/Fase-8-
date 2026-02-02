"""Catalog Use Cases - Academic structure (subjects, courses, commissions).

These are thin read-only use cases to expose the academic catalog via HTTP.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Any, Dict

from backend.src_v3.infrastructure.persistence.repositories.catalog_repository import CatalogRepository


@dataclass
class ListSubjectsCommand:
    active_only: bool = True


@dataclass
class ListCoursesForSubjectCommand:
    subject_id: str
    active_only: bool = True


@dataclass
class ListCommissionsForCourseCommand:
    course_id: str


class ListSubjectsUseCase:
    def __init__(self, repository: CatalogRepository) -> None:
        self._repository = repository

    async def execute(self, command: ListSubjectsCommand) -> List[Dict[str, Any]]:
        subjects = await self._repository.get_subjects(active_only=command.active_only)
        return [
            {
                "id": s.get("id"),
                "code": s.get("code"),
                "name": s.get("name"),
                "description": s.get("description"),
                "credits": s.get("credits"),
                "semester": None,
                "is_active": True,
            }
            for s in subjects
        ]


class ListCoursesForSubjectUseCase:
    def __init__(self, repository: CatalogRepository) -> None:
        self._repository = repository

    async def execute(self, command: ListCoursesForSubjectCommand) -> List[Dict[str, Any]]:
        courses = await self._repository.get_courses_for_subject(
            subject_id=int(command.subject_id),
            active_only=command.active_only,
        )
        return [
            {
                "id": c.get("id"),
                "subject_id": c.get("subject_id"),
                "year": c.get("year"),
                "semester": c.get("semester"),
                "start_date": c.get("start_date"),
                "end_date": c.get("end_date"),
                "is_active": True,
            }
            for c in courses
        ]


class ListCommissionsForCourseUseCase:
    def __init__(self, repository: CatalogRepository) -> None:
        self._repository = repository

    async def execute(self, command: ListCommissionsForCourseCommand) -> List[Dict[str, Any]]:
        commissions = await self._repository.get_commissions_for_course(int(command.course_id))
        return [
            {
                "id": cm.get("id"),
                "course_id": cm.get("course_id"),
                "code": cm.get("code"),
                "schedule": cm.get("schedule"),
                "capacity": cm.get("capacity"),
                "teacher_id": None,
            }
            for cm in commissions
        ]
