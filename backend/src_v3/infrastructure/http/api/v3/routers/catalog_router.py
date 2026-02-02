"""Catalog HTTP Router - API v3

Read-only endpoints for academic structure (subjects, courses, commissions).
"""
from __future__ import annotations

from typing import List, Optional
from datetime import date

from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel

from backend.src_v3.application.catalog.use_cases import (
    ListSubjectsUseCase,
    ListCoursesForSubjectUseCase,
    ListCommissionsForCourseUseCase,
    ListSubjectsCommand,
    ListCoursesForSubjectCommand,
    ListCommissionsForCourseCommand,
)
from backend.src_v3.infrastructure.persistence.database import get_db_session
from backend.src_v3.infrastructure.persistence.repositories.catalog_repository import CatalogRepository


router = APIRouter(prefix="/catalog", tags=["Catalog"])


# ---------- Schemas ----------


class SubjectResponse(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str] = None
    credits: Optional[int] = None
    semester: Optional[int] = None
    is_active: bool


class CourseResponse(BaseModel):
    id: int
    subject_id: int
    year: int
    semester: int
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: bool


class CommissionResponse(BaseModel):
    id: int
    course_id: int
    code: str
    schedule: Optional[str] = None
    capacity: Optional[int] = None
    teacher_id: Optional[str] = None


# ---------- Dependencies ----------


async def get_catalog_repository():
    async for session in get_db_session():
        yield CatalogRepository(session)


async def get_list_subjects_use_case(
    repo: CatalogRepository = Depends(get_catalog_repository),
) -> ListSubjectsUseCase:
    return ListSubjectsUseCase(repo)


async def get_list_courses_for_subject_use_case(
    repo: CatalogRepository = Depends(get_catalog_repository),
) -> ListCoursesForSubjectUseCase:
    return ListCoursesForSubjectUseCase(repo)


async def get_list_commissions_for_course_use_case(
    repo: CatalogRepository = Depends(get_catalog_repository),
) -> ListCommissionsForCourseUseCase:
    return ListCommissionsForCourseUseCase(repo)


# ---------- Endpoints ----------


@router.get("/subjects", response_model=List[SubjectResponse])
async def list_subjects(
    active_only: bool = Query(True, description="Only active subjects"),
    use_case: ListSubjectsUseCase = Depends(get_list_subjects_use_case),
):
    command = ListSubjectsCommand(active_only=active_only)
    data = await use_case.execute(command)
    return [SubjectResponse(**item) for item in data]


@router.get("/subjects/{subject_id}/courses", response_model=List[CourseResponse])
async def list_courses_for_subject(
    subject_id: str,
    active_only: bool = Query(True, description="Only active courses"),
    use_case: ListCoursesForSubjectUseCase = Depends(get_list_courses_for_subject_use_case),
):
    command = ListCoursesForSubjectCommand(subject_id=subject_id, active_only=active_only)
    data = await use_case.execute(command)
    return [CourseResponse(**item) for item in data]


@router.get("/courses/{course_id}/commissions", response_model=List[CommissionResponse])
async def list_commissions_for_course(
    course_id: str,
    use_case: ListCommissionsForCourseUseCase = Depends(get_list_commissions_for_course_use_case),
):
    command = ListCommissionsForCourseCommand(course_id=course_id)
    data = await use_case.execute(command)
    return [CommissionResponse(**item) for item in data]
