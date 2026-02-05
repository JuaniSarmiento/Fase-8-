"""Teacher HTTP Router - API v3

Endpoints for teacher activity, document and exercise management.
"""
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File,
    BackgroundTasks,
    Request,
)
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from pathlib import Path
import os
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src_v3.infrastructure.cache.decorators import cached

from backend.src_v3.application.teacher.use_cases import (
    CreateActivityUseCase,
    GenerateExerciseUseCase,
    PublishActivityUseCase,
    GetActivityExercisesUseCase,
    CreateActivityCommand,
    GenerateExerciseCommand,
)
from backend.src_v3.infrastructure.persistence.repositories.teacher_repository import (
    TeacherRepository,
)
from backend.src_v3.application.schemas.lms_hierarchy_schemas import (
    ModuleCreate,
    ModuleUpdate,
    ModuleRead,
    EnrollmentCreate,
    EnrollmentRead,
)
from backend.src_v3.infrastructure.persistence.sqlalchemy.models import (
    ModuleModel,
    EnrollmentModel,
    EnrollmentRole,
    EnrollmentStatus,
)
from backend.src_v3.infrastructure.persistence.database import get_db_session
from sqlalchemy import select
import uuid

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/teacher", tags=["Teacher"])


# ==================== COURSE ACCESS ====================

@router.get("/courses")
@cached(ttl=120, key_prefix="teacher_courses")  # Cache for 2 minutes
async def get_teacher_courses(
    request: Request,
    teacher_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get all courses where the user is a teacher.
    Get all courses where the user is enrolled as a teacher.
    
    Returns course info for module management.
    """
    try:
        from sqlalchemy import text
        
        query_str = """
            SELECT DISTINCT
                c.course_id,
                c.subject_code,
                c.year,
                c.semester
            FROM courses c
            JOIN enrollments e ON c.course_id = e.course_id
            WHERE e.user_id = :teacher_id
              AND e.role = 'TEACHER'
              AND e.status = 'ACTIVE'
            ORDER BY c.year DESC, c.semester DESC, c.subject_code ASC
        """
        
        result = await db.execute(text(query_str), {"teacher_id": teacher_id})
        rows = result.fetchall()
        
        courses = []
        for row in rows:
            courses.append({
                "course_id": row.course_id,
                "course_name": f"{row.subject_code} - {row.year}/{row.semester}",
                "semester": f"{row.year}/{row.semester}",
            })
        
        return courses
        
    except Exception as e:
        logger.error(f"Failed to get teacher courses: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get courses: {str(e)}"
        )


@router.get("/modules")
@cached(ttl=90, key_prefix="teacher_modules")  # Cache for 90 seconds
async def get_teacher_modules(
    request: Request,
    teacher_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get all modules from courses where the user is a teacher.
    
    Returns modules with student count for dashboard display.
    """
    try:
        from sqlalchemy import text
        
        query_str = """
            SELECT 
                m.module_id,
                m.title as name,
                m.description,
                m.course_id,
                c.subject_code,
                c.year,
                c.semester,
                m.created_at,
                COUNT(DISTINCT e_students.enrollment_id) as student_count
            FROM modules m
            JOIN courses c ON m.course_id = c.course_id
            JOIN enrollments e_teacher ON c.course_id = e_teacher.course_id
            LEFT JOIN enrollments e_students ON m.module_id = e_students.module_id 
                AND e_students.role = 'STUDENT' 
                AND e_students.status = 'ACTIVE'
            WHERE e_teacher.user_id = :teacher_id
              AND e_teacher.role = 'TEACHER'
              AND e_teacher.status = 'ACTIVE'
            GROUP BY m.module_id, m.title, m.description, m.course_id, 
                     c.subject_code, c.year, c.semester, m.created_at
            ORDER BY m.created_at DESC
        """
        
        result = await db.execute(text(query_str), {"teacher_id": teacher_id})
        rows = result.fetchall()
        
        modules = []
        for row in rows:
            modules.append({
                "module_id": row.module_id,
                "name": row.name,
                "description": row.description,
                "course_id": row.course_id,
                "course_name": f"{row.subject_code} - {row.year}/{row.semester}",
                "student_count": row.student_count,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            })
        
        return modules
        
    except Exception as e:
        logger.error(f"Failed to get teacher modules: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get modules: {str(e)}"
        )


@router.post("/modules")
async def create_module(
    name: str,
    teacher_id: str,
    description: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Create a new module/commission with auto-generated course and subject.
    Each module is essentially a course/commission.
    
    Returns the created module and course.
    """
    try:
        from sqlalchemy import text
        
        # 1. Crear subject en ambas tablas (legacy y nueva)
        subject_code = f"MOD_{uuid.uuid4().hex[:8].upper()}"
        subject_id = str(uuid.uuid4())
        
        # Insertar en subjects_legacy (para FK de courses)
        query_subject_legacy = text("""
            INSERT INTO subjects_legacy (code, name)
            VALUES (:code, :name)
            ON CONFLICT (code) DO NOTHING
        """)
        await db.execute(query_subject_legacy, {
            "code": subject_code,
            "name": name,
        })
        
        # Insertar en subjects (nueva tabla)
        query_subject = text("""
            INSERT INTO subjects (subject_id, name, code, created_at)
            VALUES (:subject_id, :name, :code, NOW())
            ON CONFLICT (code) DO UPDATE SET created_at = NOW()
            RETURNING subject_id
        """)
        result = await db.execute(query_subject, {
            "subject_id": subject_id,
            "name": name,
            "code": subject_code,
        })
        subject_row = result.fetchone()
        if subject_row:
            subject_id = subject_row[0]
        
        # 2. Crear curso para este módulo
        course_id = str(uuid.uuid4())
        query_course = text("""
            INSERT INTO courses (course_id, subject_code, subject_id, year, semester, is_active)
            VALUES (:course_id, :subject_code, :subject_id, 2026, '1C', true)
        """)
        await db.execute(query_course, {
            "course_id": course_id,
            "subject_code": subject_code,
            "subject_id": subject_id,
        })
        
        # 3. Crear enrollment del profesor a este curso
        enrollment_id = str(uuid.uuid4())
        query_enrollment = text("""
            INSERT INTO enrollments (enrollment_id, user_id, course_id, role, status)
            VALUES (:enrollment_id, :user_id, :course_id, 'TEACHER', 'ACTIVE')
        """)
        await db.execute(query_enrollment, {
            "enrollment_id": enrollment_id,
            "user_id": teacher_id,
            "course_id": course_id,
        })
        
        # 4. Crear el módulo vinculado al curso
        new_module = ModuleModel(
            module_id=str(uuid.uuid4()),
            title=name,
            description=description,
            course_id=course_id,
            is_published=True,  # Publicar automáticamente para que sea visible por estudiantes
        )
        db.add(new_module)
        
        await db.commit()
        await db.refresh(new_module)
        
        return {
            "module_id": new_module.module_id,
            "name": new_module.title,
            "description": new_module.description,
            "course_id": new_module.course_id,
            "created_at": new_module.created_at.isoformat() if new_module.created_at else None,
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create module: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create module: {str(e)}"
        )


@router.get("/students")
@cached(ttl=60, key_prefix="teacher_students")  # Cache for 1 minute
async def get_available_students(
    request: Request,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get all users with STUDENT role.
    
    Returns list of students for enrollment selection.
    """
    try:
        from sqlalchemy import text
        
        query_str = """
            SELECT 
                u.id as user_id,
                u.username,
                u.email,
                u.full_name
            FROM users u
            WHERE u.roles::jsonb ? 'student'
              AND u.is_active = true
            ORDER BY u.full_name ASC, u.username ASC
        """
        
        result = await db.execute(text(query_str))
        rows = result.fetchall()
        
        students = []
        for row in rows:
            students.append({
                "user_id": row.user_id,
                "username": row.username,
                "email": row.email,
                "full_name": row.full_name,
            })
        
        return students
        
    except Exception as e:
        logger.error(f"Failed to get students: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get students: {str(e)}"
        )


# ==================== REQUEST/RESPONSE MODELS ====================

class CreateActivityRequest(BaseModel):
    """Request to create activity.

    Supports both the new v3 payload (with instructions) and legacy
    payloads that use description/topics/dates.
    """
    title: str = Field(..., min_length=3, max_length=200)
    course_id: str | int
    teacher_id: str | int
    instructions: Optional[str] = Field(None, min_length=10)
    description: Optional[str] = None
    topics: Optional[List[str]] = None
    difficulty: Optional[str] = None
    start_date: Optional[str] = None
    due_date: Optional[str] = None
    policy: str = Field("BALANCED", description="STRICT, BALANCED, or PERMISSIVE")
    max_ai_help_level: str = Field("MEDIO", description="BAJO, MEDIO, or ALTO")


class ActivityResponse(BaseModel):
    """Response with activity details"""
    activity_id: str
    title: str
    course_id: str
    teacher_id: str
    instructions: str
    policy: str
    status: str
    max_ai_help_level: str


class ActivityListItem(BaseModel):
    """Lightweight activity summary for dashboard listings."""
    activity_id: str
    title: str
    course_id: str
    teacher_id: str
    instructions: str | None = None
    status: str
    created_at: str | None = None


class GenerateExerciseRequest(BaseModel):
    """Request to generate exercise"""
    topic: str = Field(..., min_length=3, description="Exercise topic")
    difficulty: str = Field(..., description="FACIL, INTERMEDIO, or DIFICIL")
    unit_number: int = Field(1, ge=1, description="Unit number")
    language: str = Field("python", description="Programming language")
    concepts: Optional[List[str]] = Field(None, description="Key concepts to cover")
    estimated_time_minutes: int = Field(30, ge=5, le=240)


class TestCaseResponse(BaseModel):
    """Test case details"""
    test_number: int
    description: str
    input_data: str
    expected_output: str
    is_hidden: bool
    timeout_seconds: int


class ExerciseResponse(BaseModel):
    """Response with generated exercise"""
    exercise_id: str
    title: str
    description: str
    difficulty: str
    language: str
    mission_markdown: str
    starter_code: str
    solution_code: str  # Reference solution for teachers
    has_solution: bool
    test_cases: List[TestCaseResponse]
    concepts: List[str]
    learning_objectives: List[str]
    estimated_time_minutes: int
    visible_test_count: int
    hidden_test_count: int


class ApprovedExerciseTestCase(BaseModel):
    """Minimal test case payload from the teacher UI when approving exercises."""
    input: str
    expected_output: str
    is_public: bool = True


class ApprovedExercisePayload(BaseModel):
    """Exercise payload approved by the teacher in the content dashboard."""
    exercise_id: str
    title: str
    description: str
    instructions: str
    initial_code: str
    language: str
    difficulty: str
    estimated_time_minutes: int = 30
    test_cases: List[ApprovedExerciseTestCase] = []


class ApproveAndPublishRequest(BaseModel):
    """Request body for approving exercises and publishing an activity."""
    exercises: List[ApprovedExercisePayload]


# ==================== DEPENDENCY INJECTION ====================

async def get_db_session():
    """Get database session"""
    from backend.src_v3.infrastructure.persistence.database import get_db_session as db_session
    async for session in db_session():
        yield session


async def get_create_activity_use_case(db=Depends(get_db_session)):
    """Inject CreateActivityUseCase"""
    from backend.src_v3.infrastructure.dependencies import get_create_activity_use_case
    return get_create_activity_use_case(db)


async def get_generate_exercise_use_case(db=Depends(get_db_session)):
    """Inject GenerateExerciseUseCase"""
    from backend.src_v3.infrastructure.dependencies import get_generate_exercise_use_case
    return get_generate_exercise_use_case(db)


async def get_publish_activity_use_case(db=Depends(get_db_session)):
    """Inject PublishActivityUseCase"""
    from backend.src_v3.infrastructure.dependencies import get_publish_activity_use_case
    return get_publish_activity_use_case(db)


async def get_activity_exercises_use_case(db=Depends(get_db_session)):
    """Inject GetActivityExercisesUseCase"""
    from backend.src_v3.infrastructure.dependencies import get_activity_exercises_use_case
    return get_activity_exercises_use_case(db)


# ==================== ENDPOINTS ====================

@router.post("/activities", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED)
async def create_activity(
    request: CreateActivityRequest,
    use_case: CreateActivityUseCase = Depends(get_create_activity_use_case)
):
    """
    Create new teaching activity.
    
    Creates activity in draft status with specified policies.
    """
    try:
        # Fallback instructions for legacy payloads
        instructions = request.instructions or request.description or request.title
		
        command = CreateActivityCommand(
            title=request.title,
            course_id=str(request.course_id),
            teacher_id=str(request.teacher_id),
            instructions=instructions,
            policy=request.policy,
            max_ai_help_level=request.max_ai_help_level,
        )
        
        activity = await use_case.execute(command)
        
        return ActivityResponse(
            activity_id=activity.activity_id,
            title=activity.title,
            course_id=activity.course_id,
            teacher_id=activity.teacher_id,
            instructions=activity.instructions,
            policy=activity.policy.name,
            status=activity.status,
            max_ai_help_level=activity.max_ai_help_level,
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create activity: {str(e)}"
        )


@router.post("/activities/{activity_id}/exercises", response_model=ExerciseResponse, status_code=status.HTTP_201_CREATED)
async def generate_exercise(
    activity_id: str,
    request: GenerateExerciseRequest,
    use_case: GenerateExerciseUseCase = Depends(get_generate_exercise_use_case)
):
    """
    Generate exercise with RAG context.
    
    Uses LLM to generate exercise based on topic and difficulty.
    """
    try:
        command = GenerateExerciseCommand(
            activity_id=activity_id,
            topic=request.topic,
            difficulty=request.difficulty,
            unit_number=request.unit_number,
            language=request.language,
            concepts=request.concepts,
            estimated_time_minutes=request.estimated_time_minutes,
        )
        
        exercise = await use_case.execute(command)
        
        test_cases_response = [
            TestCaseResponse(
                test_number=tc.test_number,
                description=tc.description,
                input_data=tc.input_data,
                expected_output=tc.expected_output,
                is_hidden=tc.is_hidden,
                timeout_seconds=tc.timeout_seconds,
            )
            for tc in exercise.test_cases
        ]
        
        return ExerciseResponse(
            exercise_id=exercise.exercise_id,
            title=exercise.title,
            description=exercise.description,
            difficulty=exercise.difficulty,
            language=exercise.language,
            mission_markdown=exercise.mission_markdown,
            starter_code=exercise.starter_code,
            has_solution=exercise.has_solution,
            test_cases=test_cases_response,
            concepts=exercise.concepts,
            learning_objectives=exercise.learning_objectives,
            estimated_time_minutes=exercise.estimated_time_minutes,
            visible_test_count=exercise.visible_test_count,
            hidden_test_count=exercise.hidden_test_count,
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate exercise: {str(e)}"
        )


@router.put("/activities/{activity_id}/publish", response_model=ActivityResponse)
async def publish_activity(
    activity_id: str,
    use_case: PublishActivityUseCase = Depends(get_publish_activity_use_case)
):
    """
    Publish activity to make it available to students.
    
    Validates activity has exercises before publishing.
    """
    try:
        activity = await use_case.execute(activity_id)
        
        return ActivityResponse(
            activity_id=activity.activity_id,
            title=activity.title,
            course_id=activity.course_id,
            teacher_id=activity.teacher_id,
            instructions=activity.instructions,
            policy=activity.policy.name,
            status=activity.status,
            max_ai_help_level=activity.max_ai_help_level,
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to publish activity: {str(e)}"
        )


@router.get("/activities/{activity_id}/exercises", response_model=List[ExerciseResponse])
async def get_activity_exercises(
    activity_id: str,
    use_case: GetActivityExercisesUseCase = Depends(get_activity_exercises_use_case)
):
    """
    Get all exercises for an activity.
    
    Returns list of exercises with full details.
    """
    try:
        exercises = await use_case.execute(activity_id)
        
        response_list = []
        for ex in exercises:
            # Safely process test cases
            raw_test_cases = getattr(ex, "test_cases", []) or []
            # Ensure it's a list
            if not isinstance(raw_test_cases, list):
                raw_test_cases = []
            
            valid_test_cases = []
            for i, tc in enumerate(raw_test_cases):
                if not tc: continue
                
                # Check for dictionary or object access
                is_dict = isinstance(tc, dict)
                
                # Helper to get value
                def get_val(key, default):
                    if is_dict: return tc.get(key) or default
                    return getattr(tc, key, None) or default

                valid_test_cases.append(TestCaseResponse(
                    test_number=get_val("test_number", i + 1),
                    description=get_val("description", ""),
                    input_data=get_val("input_data", ""),
                    expected_output=get_val("expected_output", ""),
                    is_hidden=get_val("is_hidden", False),
                    timeout_seconds=get_val("timeout_seconds", 2),
                ))

            # Calculate counts properly
            visible_count = sum(1 for tc in valid_test_cases if not tc.is_hidden)
            hidden_count = sum(1 for tc in valid_test_cases if tc.is_hidden)

            response_list.append(ExerciseResponse(
                exercise_id=str(ex.exercise_id),
                title=getattr(ex, "title", "Untitled Exercise") or "Untitled Exercise",
                description=getattr(ex, "description", "") or "",
                difficulty=getattr(ex, "difficulty", None) or "mixed",
                language=getattr(ex, "language", None) or "python",
                mission_markdown=getattr(ex, "mission_markdown", "") or "",
                starter_code=getattr(ex, "starter_code", "") or "",
                solution_code=getattr(ex, "solution_code", "") or "",
                has_solution=bool(getattr(ex, "solution_code", None)),
                test_cases=valid_test_cases,
                concepts=[str(c) for c in (getattr(ex, "concepts", []) or []) if c],
                learning_objectives=[str(l) for l in (getattr(ex, "learning_objectives", []) or []) if l],
                estimated_time_minutes=getattr(ex, "estimated_time_minutes", 30) or 30,
                visible_test_count=visible_count,
                hidden_test_count=hidden_count,
            ))
            
        return response_list
    
    except ValueError as e:
        logger.error(f"ValueError fetching exercises: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Unexpected error fetching exercises: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get exercises: {str(e)}"
        )


@router.get("/activities", response_model=List[ActivityListItem])
@cached(ttl=45, key_prefix="teacher_activities_list")  # Cache for 45 seconds
async def list_activities(
    request: Request,
    teacher_id: Optional[str] = None,
    limit: int = 50,
):
    """List activities for teacher dashboard.

    This endpoint provides a minimal view of activities so the
    React teacher dashboard can render "Mis Actividades" without
    depending on the internal domain model.
    """
    try:
        from backend.src_v3.infrastructure.persistence.database import (
            get_db_session as db_session,
        )

        async for db in db_session():
            repo = TeacherRepository(db)
            raw_activities = await repo.list_activities(
                teacher_id=teacher_id,
                limit=limit,
            )

            items: List[ActivityListItem] = [
                ActivityListItem(
                    activity_id=a.get("activity_id", ""),
                    title=a.get("title", ""),
                    course_id=a.get("course_id", ""),
                    teacher_id=a.get("teacher_id", ""),
                    instructions=a.get("instructions") or None,
                    status=a.get("status", "draft"),
                    created_at=a.get("created_at"),
                )
                for a in raw_activities
            ]

            # For compatibility with existing frontend helpers that
            # expect an APIResponse shape when using apiClient directly,
            # we keep the payload as a plain list here; callers that use
            # Axios directly will receive the list in response.data.
            return items

    except Exception as e:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list activities: {str(e)}",
        )


@router.get("/activities/{activity_id}", response_model=ActivityListItem)
@cached(ttl=60, key_prefix="teacher_activity_detail")  # Cache for 1 minute
async def get_activity_detail(request: Request, activity_id: str):
    """Get a single activity by ID for detail view."""
    try:
        from backend.src_v3.infrastructure.persistence.database import (
            get_db_session as db_session,
        )

        async for db in db_session():
            repo = TeacherRepository(db)
            activity = await repo.get_activity_by_id(activity_id)
            
            if not activity:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Activity {activity_id} not found",
                )
            
            return ActivityListItem(
                activity_id=activity.activity_id,
                title=activity.title,
                course_id=activity.course_id,
                teacher_id=activity.teacher_id,
                instructions=activity.instructions or None,
                status=activity.status,
                created_at=None,  # Activity object doesn't have created_at
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get activity: {str(e)}",
        )


@router.put("/activities/{activity_id}")
async def update_activity(
    activity_id: str,
    title: Optional[str] = None,
    instructions: Optional[str] = None,
    activity_status: Optional[str] = None,
):
    """Update basic activity metadata (title, instructions, status)."""
    try:
        from backend.src_v3.infrastructure.persistence.database import (
            get_db_session as db_session,
        )

        async for db in db_session():
            repo = TeacherRepository(db)
            
            # Build update dict with only provided fields
            updates = {}
            if title is not None:
                updates["title"] = title
            if instructions is not None:
                updates["instructions"] = instructions
            if activity_status is not None:
                updates["status"] = activity_status
            
            if not updates:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No fields provided for update",
                )
            
            success = await repo.update_activity(activity_id, updates)
            
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Activity {activity_id} not found",
                )
            
            return {"message": "Activity updated successfully", "activity_id": activity_id}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update activity: {str(e)}",
        )


@router.delete("/activities/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_activity(activity_id: str):
    """Permanently delete an activity."""
    try:
        from backend.src_v3.infrastructure.persistence.database import (
            get_db_session as db_session,
        )

        async for db in db_session():
            repo = TeacherRepository(db)
            success = await repo.delete_activity(activity_id)
            
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Activity {activity_id} not found",
                )
            
            return None  # 204 No Content

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete activity: {str(e)}",
        )


@router.get("/activities/{activity_id}/students")
async def get_activity_students(activity_id: str):
    """Get all students enrolled in an activity with their progress and submissions."""
    try:
        from backend.src_v3.infrastructure.persistence.database import (
            get_db_session as db_session,
        )
        from sqlalchemy import text

        async for db in db_session():
            # Get all students with their sessions and attempts for this activity
            result = await db.execute(text("""
                SELECT DISTINCT
                    u.id as student_id,
                    u.email,
                    u.full_name,
                    COUNT(DISTINCT ex.exercise_id) as total_exercises,
                    COUNT(DISTINCT CASE WHEN att.passed = true THEN ex.exercise_id END) as submitted_exercises,
                    COUNT(DISTINCT CASE WHEN att.passed = true THEN ex.exercise_id END) as graded_exercises,
                    AVG(CASE WHEN att.passed = true THEN 10 ELSE 5 END) as avg_score,
                    MAX(att.submitted_at) as last_submission
                FROM users u
                INNER JOIN sessions_v2 s ON s.user_id = u.id
                CROSS JOIN exercises_v2 ex
                LEFT JOIN exercise_attempts_v2 att ON att.exercise_id = ex.exercise_id AND att.user_id = u.id
                WHERE s.activity_id = :activity_id
                AND u.roles @> '["student"]'::jsonb
                GROUP BY u.id, u.email, u.full_name
                ORDER BY u.full_name
            """), {"activity_id": activity_id})
            
            students = []
            for row in result:
                total = row[3] or 0
                submitted = row[4] or 0
                students.append({
                    "student_id": row[0],
                    "email": row[1],
                    "full_name": row[2],
                    "total_exercises": total,
                    "submitted_exercises": submitted,
                    "graded_exercises": row[5] or 0,
                    "avg_score": float(row[6]) if row[6] else 0,
                    "last_submission": row[7].isoformat() if row[7] else None,
                    "progress_percentage": (submitted / total * 100) if total > 0 else 0
                })
            
            return students

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get students: {str(e)}",
        )


@router.get("/activities/{activity_id}/students/{student_id}/submissions")
async def get_student_submissions(activity_id: str, student_id: str):
    """Get detailed submission history for a student in an activity."""
    try:
        from backend.src_v3.infrastructure.persistence.database import (
            get_db_session as db_session,
        )
        from sqlalchemy import text

        async for db in db_session():
            result = await db.execute(text("""
                SELECT 
                    ex.exercise_id,
                    ex.title as exercise_title,
                    ex.difficulty,
                    ex.estimated_time_minutes,
                    att.attempt_id as submission_id,
                    att.code_submitted as code,
                    CASE WHEN att.passed = true THEN 'graded' ELSE 'submitted' END as status,
                    CASE WHEN att.passed = true THEN 10 ELSE 5 END as score,
                    att.execution_output::text as feedback,
                    att.submitted_at,
                    att.submitted_at as graded_at,
                    1 as attempt_number
                FROM exercises_v2 ex
                LEFT JOIN exercise_attempts_v2 att ON att.exercise_id = ex.exercise_id AND att.user_id = :student_id
                INNER JOIN sessions_v2 s ON s.activity_id = :activity_id AND s.user_id = :student_id
                ORDER BY ex.created_at, att.submitted_at DESC
                LIMIT 50
            """), {"activity_id": activity_id, "student_id": student_id})
            
            submissions = []
            for row in result:
                submissions.append({
                    "exercise_id": row[0],
                    "exercise_title": row[1],
                    "difficulty": row[2],
                    "points": row[3] or 10,
                    "submission_id": row[4],
                    "code": row[5],
                    "status": row[6] if row[6] else 'pending',
                    "score": row[7],
                    "feedback": row[8],
                    "submitted_at": row[9].isoformat() if row[9] else None,
                    "graded_at": row[10].isoformat() if row[10] else None,
                    "attempt_number": row[11]
                })
            
            return submissions

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get submissions: {str(e)}",
        )


@router.post("/activities/{activity_id}/approve-and-publish", response_model=ActivityResponse)
async def approve_and_publish_activity(
    activity_id: str,
    request: ApproveAndPublishRequest,
    db=Depends(get_db_session),
    publish_use_case: PublishActivityUseCase = Depends(get_publish_activity_use_case),
):
    """Persist approved exercises and publish the activity.

    This endpoint is called by the TeacherContentDashboard when the
    teacher clicks "Aprobar y Publicar" after reviewing exercises.
    """
    if not request.exercises:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one exercise is required to publish the activity",
        )

    # Ensure the activity exists
    repo = TeacherRepository(db)
    activity = await repo.get_activity_by_id(activity_id)
    if activity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Activity with id {activity_id} not found",
        )

    # Map approved exercises from the UI into domain entities and
    # persist them in exercises_v2 so they become the canonical set
    # for this activity.
    from uuid import uuid4
    from backend.src_v3.core.domain.teacher.entities import GeneratedExercise, TestCase

    domain_exercises: List[GeneratedExercise] = []
    difficulty_map: Dict[str, str] = {
        "easy": "FACIL",
        "medium": "INTERMEDIO",
        "hard": "DIFICIL",
    }

    for ex in request.exercises:
        # Build domain test cases from the simpler UI structure
        test_cases: List[TestCase] = []
        for idx, tc in enumerate(ex.test_cases or [], start=1):
            test_cases.append(
                TestCase(
                    test_number=idx,
                    description=f"Test {idx}",
                    input_data=tc.input,
                    expected_output=tc.expected_output,
                    is_hidden=not tc.is_public,
                    timeout_seconds=5,
                )
            )

        if not test_cases:
            # Defensive fallback, though in practice the generator
            # always provides test cases.
            test_cases.append(
                TestCase(
                    test_number=1,
                    description="Test básico",
                    input_data="",
                    expected_output="",
                    is_hidden=False,
                    timeout_seconds=5,
                )
            )

        domain_exercises.append(
            GeneratedExercise(
                exercise_id=ex.exercise_id or str(uuid4()),
                title=ex.title,
                description=ex.description or ex.instructions,
                difficulty=difficulty_map.get(ex.difficulty, ex.difficulty.upper()),
                language=ex.language,
                mission_markdown=ex.instructions,
                starter_code=ex.initial_code,
                solution_code=ex.initial_code,
                test_cases=test_cases,
                concepts=[],
                learning_objectives=[],
                estimated_time_minutes=ex.estimated_time_minutes or 30,
                pedagogical_notes=None,
                rag_sources=[],
            )
        )

    try:
        # Replace current exercises for this activity with the approved
        # set, then publish the activity using the existing use case.
        await repo.replace_exercises_for_activity(activity_id, domain_exercises)

        activity = await publish_use_case.execute(activity_id)

        return ActivityResponse(
            activity_id=activity.activity_id,
            title=activity.title,
            course_id=activity.course_id,
            teacher_id=activity.teacher_id,
            instructions=activity.instructions,
            policy=activity.policy.name,
            status=activity.status,
            max_ai_help_level=activity.max_ai_help_level,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:  # pragma: no cover - defensive safety
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve and publish activity: {str(e)}",
        )


@router.post("/activities/{activity_id}/documents")
async def upload_activity_document(
    activity_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db=Depends(get_db_session),
):
    """Upload a pedagogical PDF document for an activity.

    This endpoint:
    - Validates that the activity exists
    - Accepts only PDF files
    - Stores the file under ``uploads/activities/{activity_id}/``
    - Processes the PDF with RAG for exercise generation
    - Returns status with RAG processing info
    """
    # Ensure the activity exists (404 if not)
    repo = TeacherRepository(db)
    activity = await repo.get_activity_by_id(activity_id)
    if activity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Activity with id {activity_id} not found",
        )

    # Basic file validation
    filename = file.filename or ""
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed",
        )

    # Resolve uploads directory (default: ./uploads)
    uploads_root = os.getenv("UPLOADS_DIR", "uploads")
    activity_dir = Path(uploads_root) / "activities" / activity_id
    activity_dir.mkdir(parents=True, exist_ok=True)

    target_path = activity_dir / filename

    try:
        # Read file content into memory and write to disk
        content = await file.read()
        target_path.write_bytes(content)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving uploaded document: {exc}",
        )

    # Process PDF with RAG in background
    async def process_pdf_rag():
        """Background task to process PDF and store in vector database"""
        try:
            from backend.src_v3.infrastructure.ai.rag.chroma_service import ChromaRAGService
            from backend.src_v3.infrastructure.ai.rag.pdf_processor import PDFProcessor
            
            chroma_service = ChromaRAGService()
            pdf_processor = PDFProcessor(chroma_service)
            
            result = await pdf_processor.process_and_store(
                pdf_path=target_path,
                activity_id=activity_id,
                metadata={
                    "activity_title": activity.title,
                    "course_id": str(activity.course_id)
                }
            )
            
            if result['success']:
                print(f"✅ RAG processing completed for {filename}")
                print(f"   Stored {result['chunks_stored']} chunks for activity {activity_id}")
            else:
                print(f"⚠️ RAG processing failed: {result.get('error')}")
                
        except Exception as e:
            print(f"❌ Error in RAG background processing: {e}")
    
    background_tasks.add_task(process_pdf_rag)

    return {
        "success": True,
        "message": "Document uploaded successfully and queued for RAG processing",
        "filename": filename,
        "activity_id": activity_id,
        "rag_processing": "started"
    }


# ==================== GRADING AND SUBMISSIONS ENDPOINTS ====================

class SubmissionResponse(BaseModel):
    """Student submission for an activity"""
    submission_id: str
    student_id: str
    student_name: str
    student_email: str
    activity_id: str
    exercise_id: Optional[str] = None
    code_submitted: str
    passed: Optional[bool] = None
    ai_feedback: Optional[str] = None
    execution_output: Optional[dict] = None
    test_results: Optional[dict] = None
    submitted_at: str
    grade: Optional[float] = None
    teacher_feedback: Optional[str] = None
    graded_at: Optional[str] = None
    graded_by: Optional[str] = None
    
    class Config:
        from_attributes = True


class GradeSubmissionRequest(BaseModel):
    """Request to grade a submission"""
    grade: float = Field(..., ge=0, le=10, description="Grade from 0 to 10")
    feedback: Optional[str] = Field(None, description="Teacher feedback")
    override_ai: bool = Field(True, description="Override AI grade if exists")


@router.get("/activities/{activity_id}/submissions", response_model=List[SubmissionResponse])
async def get_activity_submissions(
    activity_id: str,
    student_id: Optional[str] = None,
    exercise_id: Optional[str] = None,
    passed_only: Optional[bool] = None,
    limit: int = 100
):
    """
    Ver todas las entregas de una actividad.
    
    Permite filtrar por estudiante, ejercicio y estado de aprobación.
    Requiere autenticación de profesor.
    """
    # TODO: Implementar lógica de consulta desde repositorio
    # TODO: Verificar autenticación del profesor
    # TODO: Verificar que el profesor sea titular de la actividad
    # TODO: Aplicar filtros si están presentes
    # TODO: Incluir información del estudiante (join con users)
    
    return []


@router.post("/submissions/{submission_id}/grade", status_code=status.HTTP_200_OK)
async def grade_submission(
    submission_id: str,
    request: GradeSubmissionRequest,
    db=Depends(get_db_session)
):
    """
    Profesor asienta la nota final de una entrega.
    
    Usa GradingService para manejar lógica híbrida (AI + Human).
    Crea audit log del override.
    """
    try:
        from backend.src_v3.application.services.grading_service import GradingService
        
        # TODO: Get teacher_id from auth token (for now, use mock)
        teacher_id = "teacher_mock_123"
        
        # Initialize grading service
        grading_service = GradingService(db)
        
        # Apply manual grade with audit
        result = await grading_service.apply_manual_grade(
            submission_id=submission_id,
            teacher_id=teacher_id,
            manual_grade=request.grade,
            teacher_feedback=request.feedback,
            override_reason="Manual teacher override" if request.override_ai else None
        )
        
        return {
            "message": "Submission graded successfully",
            "submission_id": result["submission_id"],
            "grade": result["grade"],
            "is_manual_grade": result["is_manual_grade"],
            "graded_by": result["graded_by"],
            "graded_at": result["graded_at"],
            "audit_created": result["audit_created"]
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to grade submission: {str(e)}"
        )


@router.post("/activities/{activity_id}/grade-all", status_code=status.HTTP_200_OK)
async def grade_all_passed_submissions(activity_id: str, grade: float = 10.0):
    """
    Calificar automáticamente todas las entregas aprobadas de una actividad.
    
    Útil para actividades con auto-corrección donde la AI ya validó el código.
    Requiere autenticación de profesor.
    """
    # TODO: Implementar calificación masiva
    # TODO: Verificar autenticación del profesor
    # TODO: Verificar que el profesor sea titular de la actividad
    # TODO: Actualizar solo submissions con passed=True y grade=None
    # TODO: Enviar notificaciones a los estudiantes
    
    return {
        "message": "All passed submissions graded",
        "activity_id": activity_id,
        "graded_count": 0,
        "grade": grade
    }


@router.get("/activities/{activity_id}/statistics", status_code=status.HTTP_200_OK)
async def get_activity_statistics(activity_id: str):
    """
    Obtener estadísticas de una actividad.
    
    Incluye: total submissions, pass rate, average grade, etc.
    Requiere autenticación de profesor.
    """
    # TODO: Implementar cálculo de estadísticas
    # TODO: Verificar autenticación del profesor
    # TODO: Verificar que el profesor sea titular de la actividad
    
    return {
        "activity_id": activity_id,
        "total_students": 0,
        "total_submissions": 0,
        "students_with_submissions": 0,
        "passed_submissions": 0,
        "pass_rate": 0.0,
        "graded_submissions": 0,
        "average_grade": 0.0,
        "exercises_count": 0
    }


# ==================== DASHBOARD & TRACEABILITY ====================

class StudentActivityStatus(BaseModel):
    """Estado de un estudiante en una actividad"""
    student_id: str
    student_name: str
    status: str  # not_started, in_progress, submitted, graded
    submissions_count: int
    last_submission_date: Optional[str]
    grade: Optional[float]
    passed: bool
    cognitive_phase: Optional[str]  # N4 phase
    frustration_level: Optional[float]
    understanding_level: Optional[float]


class DashboardResponse(BaseModel):
    """Dashboard completo de actividad"""
    activity_id: str
    activity_title: str
    students: List[StudentActivityStatus]
    total_students: int
    students_started: int
    students_submitted: int
    students_passed: int
    average_grade: float
    pass_rate: float


@router.get("/activities/{activity_id}/dashboard", response_model=DashboardResponse)
async def get_activity_dashboard(activity_id: str):
    """
    Obtener dashboard completo de una actividad.
    
    Incluye:
    - Estado de cada estudiante (status, submissions, grades)
    - Métricas agregadas (pass rate, average grade)
    - Progreso cognitivo (fase N4)
    
    Requiere autenticación de profesor titular de la actividad.
    """
    # TODO: Implementar consulta a base de datos
    # TODO: JOIN students, submissions, grades, tutor_sessions
    # TODO: Calcular métricas agregadas
    # TODO: Verificar autenticación y permisos
    
    return {
        "activity_id": activity_id,
        "activity_title": "Actividad de ejemplo",
        "students": [
            {
                "student_id": "student_1",
                "student_name": "Estudiante Demo",
                "status": "submitted",
                "submissions_count": 3,
                "last_submission_date": "2026-01-25T10:30:00Z",
                "grade": 8.5,
                "passed": True,
                "cognitive_phase": "validation",
                "frustration_level": 0.3,
                "understanding_level": 0.8
            }
        ],
        "total_students": 25,
        "students_started": 20,
        "students_submitted": 15,
        "students_passed": 12,
        "average_grade": 7.8,
        "pass_rate": 0.8
    }


class CognitiveTraceability(BaseModel):
    """N4 Cognitive Traceability - Full learning journey"""
    student_id: str
    activity_id: str
    cognitive_journey: List[Dict[str, Any]]  # Timeline of phases
    interactions: List[Dict[str, Any]]  # All tutor interactions
    code_evolution: List[Dict[str, Any]]  # Code snapshots
    frustration_curve: List[float]
    understanding_curve: List[float]
    total_hints: int
    total_time_minutes: int
    final_phase: str
    completed: bool


@router.get(
    "/students/{student_id}/activities/{activity_id}/traceability",
    response_model=CognitiveTraceability
)
async def get_student_traceability(student_id: str, activity_id: str):
    """
    Obtener trazabilidad cognitiva completa (N4) de un estudiante en una actividad.
    
    Devuelve:
    - Evolución por fases cognitivas (7 fases)
    - Todas las interacciones con el tutor
    - Snapshots de código en cada fase
    - Curvas de frustración y comprensión
    - Hints recibidos
    - Tiempo total invertido
    
    Requiere autenticación de profesor titular de la actividad.
    """
    # TODO: Consultar tutor_sessions table
    # TODO: Reconstruir journey completo desde messages y states
    # TODO: Extraer code_snapshots por fase
    # TODO: Calcular métricas temporales
    
    return {
        "student_id": student_id,
        "activity_id": activity_id,
        "cognitive_journey": [
            {
                "phase": "exploration",
                "start_time": "2026-01-25T09:00:00Z",
                "end_time": "2026-01-25T09:15:00Z",
                "duration_minutes": 15,
                "interactions": 5,
                "hints_given": 1
            },
            {
                "phase": "decomposition",
                "start_time": "2026-01-25T09:15:00Z",
                "end_time": "2026-01-25T09:35:00Z",
                "duration_minutes": 20,
                "interactions": 8,
                "hints_given": 2
            }
        ],
        "interactions": [
            {
                "timestamp": "2026-01-25T09:00:00Z",
                "role": "student",
                "message": "No entiendo el enunciado",
                "cognitive_phase": "exploration"
            },
            {
                "timestamp": "2026-01-25T09:01:00Z",
                "role": "tutor",
                "message": "¿Qué parte específica del enunciado te resulta confusa?",
                "cognitive_phase": "exploration",
                "was_hint": False
            }
        ],
        "code_evolution": [
            {
                "timestamp": "2026-01-25T09:20:00Z",
                "phase": "implementation",
                "code": "def solution():\n    # TODO",
                "lines_count": 2
            }
        ],
        "frustration_curve": [0.5, 0.6, 0.4, 0.3, 0.2],
        "understanding_curve": [0.3, 0.4, 0.6, 0.7, 0.8],
        "total_hints": 5,
        "total_time_minutes": 85,
        "final_phase": "reflection",
        "completed": True
    }


# ==================== EXERCISE GENERATOR (LangGraph) ====================

class GenerateExercisesFromPDFRequest(BaseModel):
    """Request to start PDF-based exercise generation"""
    course_id: str
    topic: str = Field(..., description="Topic covered in the PDF")
    difficulty: str = Field("mixed", description="easy, medium, hard, or mixed")
    language: str = Field("python", description="Programming language")
    concepts: List[str] = Field([], description="Key concepts to cover")


class GeneratorJobResponse(BaseModel):
    """Response for generator job"""
    job_id: str
    status: str  # ingestion, generation, review, published, error
    awaiting_approval: bool
    error: Optional[str]


class DraftExercise(BaseModel):
    """Draft exercise from generator"""
    title: str
    description: str
    difficulty: str
    concepts: List[str]
    mission_markdown: str
    starter_code: str
    solution_code: str
    test_cases: List[Dict[str, Any]]


class DraftResponse(BaseModel):
    """Response with draft exercises"""
    job_id: str
    status: str
    draft_exercises: List[DraftExercise]
    awaiting_approval: bool
    created_at: str
    updated_at: str


class ApproveExercisesRequest(BaseModel):
    """Request to approve exercises"""
    approved_indices: Optional[List[int]] = Field(
        None,
        description="Indices of exercises to approve (null = approve all)"
    )
    activity_title: Optional[str] = Field(
        None,
        description="Title for the created activity"
    )
    activity_description: Optional[str] = Field(
        None,
        description="Description for the activity"
    )
    module_id: Optional[str] = Field(
        None,
        description="Module ID to link the activity to"
    )


@router.post("/generator/upload", response_model=GeneratorJobResponse, status_code=status.HTTP_201_CREATED)
async def upload_pdf_and_start_generation(
    teacher_id: str,
    course_id: str,
    topic: str,
    file: UploadFile = File(..., description="PDF file with course material"),
    difficulty: str = "mixed",
    language: str = "python",
    concepts: str = "",  # Comma-separated concepts
    background_tasks: BackgroundTasks = None
):
    """
    Upload PDF and start exercise generation workflow (LangGraph).
    
    Workflow:
    1. INGESTION: Extract text, vectorize to ChromaDB
    2. GENERATION: Use Mistral + RAG to generate 10 exercises
    3. REVIEW: Human checkpoint (teacher approval)
    4. PUBLISH: Save approved exercises to database
    
    Returns job_id to track progress.
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are allowed"
            )
        
        # Save file temporarily
        import uuid
        from backend.src_v3.infrastructure.ai.teacher_generator_graph import TeacherGeneratorGraph
        from backend.src_v3.core.domain.teacher.entities import ExerciseRequirements
        
        job_id = str(uuid.uuid4())
        upload_dir = Path(os.getenv("UPLOADS_DIR", "./uploads")) / "generator_pdfs"
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        pdf_path = upload_dir / f"{job_id}_{file.filename}"
        
        # Write file to disk
        content = await file.read()
        with open(pdf_path, "wb") as f:
            f.write(content)
        
        # Parse concepts
        concepts_list = [c.strip() for c in concepts.split(",")] if concepts else [topic]
        
        # Create requirements
        requirements = ExerciseRequirements(
            topic=topic,
            difficulty=difficulty,
            unit_number=1,
            language=language,
            estimated_time_minutes=30,
            concepts=concepts_list,
            count=10
        )
        
        # Initialize generator graph
        mistral_api_key = os.getenv("MISTRAL_API_KEY")
        if not mistral_api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="MISTRAL_API_KEY not configured"
            )
        
        generator = TeacherGeneratorGraph(
            mistral_api_key=mistral_api_key,
            model_name="mistral-small-latest"
        )
        
        # Start generation asynchronously
        async def run_generation():
            try:
                result = await generator.start_generation(
                    teacher_id=teacher_id,
                    course_id=course_id,
                    pdf_path=str(pdf_path),
                    requirements=requirements,
                    job_id=job_id  # Pass the job_id created in the endpoint
                )
                logger.info(f"Generation job {job_id} completed: {result['status']}")
            except Exception as e:
                logger.error(f"Generation job {job_id} failed: {e}", exc_info=True)
        
        # Run in background if BackgroundTasks available
        if background_tasks:
            background_tasks.add_task(run_generation)
        else:
            # For testing without background tasks
            import asyncio
            asyncio.create_task(run_generation())
        
        return {
            "job_id": job_id,
            "status": "processing",
            "awaiting_approval": False,
            "error": None
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start generation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start generation: {str(e)}"
        )


@router.get("/generator/{job_id}/status", response_model=GeneratorJobResponse)
async def get_generation_status(job_id: str):
    """
    Check status of generation job.
    
    Returns current status without full draft data.
    Used for polling during generation.
    """
    try:
        from backend.src_v3.infrastructure.ai.teacher_generator_graph import TeacherGeneratorGraph
        
        # Initialize generator
        mistral_api_key = os.getenv("MISTRAL_API_KEY")
        if not mistral_api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="MISTRAL_API_KEY not configured"
            )
        
        generator = TeacherGeneratorGraph(
            mistral_api_key=mistral_api_key,
            model_name="mistral-small-latest",
        )
        
        # Get current state
        state = await generator.get_state(job_id)
        
        logger.info(f"📋 State for job {job_id}: {state}")
        
        # Check if state is missing or has an actual error (not just None)
        if not state or (state.get("error") and state.get("error") != ""):
            # Job not found or error occurred
            error_msg = state.get("error", "Job not found") if state else "Job not found"
            
            logger.warning(f"⚠️ Returning failed status for job {job_id}, error: {error_msg}")
            
            if error_msg and "not found" in error_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Job {job_id} not found"
                )
            
            return {
                "job_id": job_id,
                "status": "failed",
                "awaiting_approval": False,
                "error": error_msg
            }
        
        # Determine status from state
        current_step = state.get("current_step", "unknown")
        draft_ready = state.get("draft_ready", False)
        published = state.get("published", False)
        
        logger.info(f"🎯 Job {job_id} - current_step: {current_step}, draft_ready: {draft_ready}, published: {published}")
        
        # Map graph phases to API statuses
        if published or current_step == "published":
            job_status = "completed"
        elif draft_ready or current_step == "review":
            # When the graph reaches human_review node, it's ready for approval
            job_status = "awaiting_approval"
        elif current_step in ["ingestion", "ingest_pdf", "ingestion_complete"]:
            job_status = "processing"
        elif current_step in ["generation", "generate_draft"]:
            job_status = "processing"
        elif current_step == "error":
            job_status = "failed"
        else:
            job_status = "processing"
        
        logger.info(f"✅ Returning status '{job_status}' for job {job_id}")
        
        return {
            "job_id": job_id,
            "status": job_status,
            "awaiting_approval": draft_ready and not published,
            "error": state.get("error")
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get status for job {job_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job status: {str(e)}"
        )


@router.get("/generator/{job_id}/draft", response_model=DraftResponse)
async def get_generation_draft(job_id: str):
    """
    Retrieve draft exercises for review.
    
    Polls the LangGraph state to check if draft is ready.
    Returns 404 if job not found, 202 if still processing.
    """
    try:
        from backend.src_v3.infrastructure.ai.teacher_generator_graph import TeacherGeneratorGraph
        
        # Initialize generator
        mistral_api_key = os.getenv("MISTRAL_API_KEY")
        if not mistral_api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="MISTRAL_API_KEY not configured"
            )
        
        generator = TeacherGeneratorGraph(
            mistral_api_key=mistral_api_key,
            model_name="mistral-small-latest",
        )
        
        # Get draft state
        result = await generator.get_draft(job_id)
        
        if "error" in result:
            if "not found" in result["error"].lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Job {job_id} not found"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result["error"]
                )
        
        # Check if still processing
        status_value = result.get("status", "unknown")
        if status_value in ["ingestion", "generation"]:
            raise HTTPException(
                status_code=status.HTTP_202_ACCEPTED,
                detail=f"Job still processing (phase: {status_value})"
            )
        
        # Convert draft exercises to response format
        draft_exercises = []
        for ex in result.get("draft_exercises", []):
            draft_exercises.append(DraftExercise(
                title=ex.get("title", ""),
                description=ex.get("description", ""),
                difficulty=ex.get("difficulty", ""),
                test_cases=ex.get("test_cases", [])
            ))
        
        return DraftResponse(
            job_id=job_id,
            status=status_value,
            exercises=draft_exercises
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get draft for job {job_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve draft: {str(e)}"
        )


@router.put("/generator/{job_id}/approve", response_model=GeneratorJobResponse)
async def approve_draft_and_resume(
    job_id: str,
    approval: ApproveExercisesRequest
):
    """
    Approve draft exercises and resume LangGraph workflow.
    
    Resumes the LangGraph workflow from the human review checkpoint.
    The graph will automatically save approved exercises to the database.
    """
    try:
        from backend.src_v3.infrastructure.ai.teacher_generator_graph import TeacherGeneratorGraph
        
        # Initialize generator
        mistral_api_key = os.getenv("MISTRAL_API_KEY")
        if not mistral_api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="MISTRAL_API_KEY not configured"
            )
        
        generator = TeacherGeneratorGraph(
            mistral_api_key=mistral_api_key,
            model_name="mistral-small-latest",
        )
        
        # Approve and publish
        result = await generator.approve_and_publish(
            job_id=job_id,
            approved_exercise_indices=approval.approved_indices
        )
        
        if "error" in result:
            if "not found" in result["error"].lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Job {job_id} not found"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result["error"]
                )
        
        return GeneratorJobResponse(
            job_id=job_id,
            status=result.get("status", "published"),
            awaiting_approval=False,
            error=result.get("error")
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to approve job {job_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve and publish: {str(e)}"
        )


@router.put("/generator/{job_id}/publish", response_model=GeneratorJobResponse)
async def approve_and_publish_exercises(
    job_id: str,
    approval: ApproveExercisesRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Approve draft exercises and publish to database.
    
    After reviewing the draft, teacher can:
    - Approve all exercises (approved_indices = null)
    - Approve specific exercises (approved_indices = [0, 2, 5])
    
    Approved exercises will be saved to the database and available
    for students.
    
    Requiere autenticación de profesor.
    """
    try:
        from backend.src_v3.infrastructure.ai.teacher_generator_graph import TeacherGeneratorGraph
        
        # Get Mistral API key
        mistral_api_key = os.getenv("MISTRAL_API_KEY")
        if not mistral_api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Mistral API key not configured"
            )
        
        # Initialize generator graph
        generator = TeacherGeneratorGraph(
            mistral_api_key=mistral_api_key,
            model_name=os.getenv("MISTRAL_MODEL", "mistral-small-latest")
        )
        
        # Approve and publish with DB persistence
        result = await generator.approve_and_publish(
            job_id=job_id,
            approved_exercise_indices=approval.approved_indices,
            db_session=db,
            activity_title=approval.activity_title,
            activity_description=approval.activity_description,
            module_id=approval.module_id
        )
        
        if result.get("error"):
            if "not found" in result["error"]:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=result["error"]
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )
        
        logger.info(
            f"Published exercises for job {job_id}",
            extra={
                "job_id": job_id,
                "activity_id": result.get("activity_id"),
                "approved_count": result.get("approved_count")
            }
        )
        
        return {
            "job_id": job_id,
            "status": result["status"],
            "awaiting_approval": False,
            "error": None,
            "activity_id": result.get("activity_id"),
            "exercise_count": result.get("approved_count")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to publish exercises: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to publish exercises: {str(e)}"
        )


# ==================== AI PEDAGOGICAL ANALYST ====================

class AnalyticsAuditRequest(BaseModel):
    """Request for AI pedagogical analysis"""
    teacher_id: str
    activity_id: Optional[str] = None
    include_traceability: bool = True


class AnalyticsAuditResponse(BaseModel):
    """AI-generated pedagogical assessment"""
    analysis_id: str
    student_id: str
    risk_score: float
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    
    # AI Analysis
    diagnosis: str
    evidence: List[str]
    intervention: str
    confidence_score: float
    
    # Metadata
    status: str
    error_message: Optional[str] = None
    created_at: str
    updated_at: str


@router.post("/analytics/audit/{student_id}", response_model=AnalyticsAuditResponse)
async def generate_pedagogical_audit(
    student_id: str,
    request: AnalyticsAuditRequest
):
    """
    Generate AI-powered pedagogical audit using Mistral AI.
    
    This endpoint analyzes a student's N4 traceability logs and generates:
    - Diagnosis: Why is the student struggling?
    - Evidence: Specific quotes from interaction logs
    - Intervention: Actionable recommendations for the teacher
    
    The analysis uses the TeacherAnalystGraph (LangGraph + Mistral) to
    provide deep insights into student learning patterns.
    
    Requires teacher authentication.
    """
    try:
        # TODO: Get student's risk profile from analytics service
        # For now, use mock data
        risk_score = 0.75
        risk_level = "HIGH"
        cognitive_phase = "implementation"
        frustration_level = 0.8
        understanding_level = 0.3
        
        # TODO: Get traceability logs from database
        # For now, use mock logs
        traceability_logs = [
            {
                "timestamp": "2026-01-26T10:00:00Z",
                "action": "code_submit",
                "cognitive_phase": "implementation",
                "details": "Submitted code with syntax error: missing colon after if statement",
                "duration_seconds": 120
            },
            {
                "timestamp": "2026-01-26T10:02:00Z",
                "action": "error",
                "cognitive_phase": "debugging",
                "details": "SyntaxError: invalid syntax at line 5",
                "duration_seconds": 30
            },
            {
                "timestamp": "2026-01-26T10:05:00Z",
                "action": "tutor_interaction",
                "cognitive_phase": "debugging",
                "details": "Student asked: 'Why doesn't this work?' Tutor responded with Socratic question about syntax rules",
                "duration_seconds": 180
            },
            {
                "timestamp": "2026-01-26T10:10:00Z",
                "action": "hint_requested",
                "cognitive_phase": "debugging",
                "details": "Hint given about checking line endings",
                "duration_seconds": 60
            },
            {
                "timestamp": "2026-01-26T10:15:00Z",
                "action": "code_submit",
                "cognitive_phase": "validation",
                "details": "Submitted code with same error repeated",
                "duration_seconds": 90
            }
        ]
        
        # Check if logs exist
        if not traceability_logs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No traceability logs found for student {student_id}"
            )
        
        # Initialize TeacherAnalystGraph
        import os
        from backend.src_v3.infrastructure.ai.teacher_analyst_graph import TeacherAnalystGraph
        
        mistral_api_key = os.getenv("MISTRAL_API_KEY")
        if not mistral_api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="MISTRAL_API_KEY not configured"
            )
        
        analyst_graph = TeacherAnalystGraph(
            mistral_api_key=mistral_api_key,
            model_name="mistral-small-latest",
            temperature=0.3  # Lower for analytical
        )
        
        # Run analysis
        result = await analyst_graph.analyze_student(
            student_id=student_id,
            teacher_id=request.teacher_id,
            risk_score=risk_score,
            risk_level=risk_level,
            traceability_logs=traceability_logs,
            cognitive_phase=cognitive_phase,
            frustration_level=frustration_level,
            understanding_level=understanding_level
        )
        
        return AnalyticsAuditResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate pedagogical audit: {str(e)}"
        )


@router.get("/analytics/audit/{student_id}/history")
async def get_audit_history(
    student_id: str,
    teacher_id: str,
    limit: int = 10
):
    """
    Get history of AI audits for a student.
    
    Returns previous analyses to track improvement over time.
    """
    # TODO: Implement database query for audit history
    
    return {
        "student_id": student_id,
        "audits": [],
        "total": 0,
        "message": "Audit history retrieval not yet implemented"
    }


# ==================== MODULE MANAGEMENT (LMS Hierarchy) ====================

@router.post("/courses/{course_id}/modules", response_model=ModuleRead, status_code=status.HTTP_201_CREATED)
async def create_module(
    course_id: str,
    module_data: ModuleCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Create a new module within a course.
    
    Modules organize activities hierarchically: Course -> Module -> Activity
    """
    try:
        # Verify course exists and teacher has access (via enrollment)
        # TODO: Add proper authorization check via enrollments
        
        # Create module
        module_id = str(uuid.uuid4())
        module = ModuleModel(
            module_id=module_id,
            course_id=course_id,
            title=module_data.title,
            description=module_data.description,
            order_index=module_data.order_index,
            is_published=module_data.is_published,
            metadata_json=module_data.metadata_json,
        )
        
        db.add(module)
        await db.commit()
        await db.refresh(module)
        
        logger.info(f"Created module {module_id} in course {course_id}")
        
        return ModuleRead.model_validate(module)
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create module: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create module: {str(e)}"
        )


@router.get("/courses/{course_id}/modules", response_model=List[ModuleRead])
async def list_course_modules(
    course_id: str,
    include_unpublished: bool = True,
    db: AsyncSession = Depends(get_db_session)
):
    """
    List all modules in a course.
    
    Returns modules ordered by order_index.
    """
    try:
        query = select(ModuleModel).where(ModuleModel.course_id == course_id)
        
        if not include_unpublished:
            query = query.where(ModuleModel.is_published == True)
        
        query = query.order_by(ModuleModel.order_index)
        
        result = await db.execute(query)
        modules = result.scalars().all()
        
        return [ModuleRead.model_validate(m) for m in modules]
        
    except Exception as e:
        logger.error(f"Failed to list modules: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list modules: {str(e)}"
        )


@router.put("/modules/{module_id}", response_model=ModuleRead)
async def update_module(
    module_id: str,
    module_data: ModuleUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Update module details.
    
    Can update title, description, order_index, and publication status.
    """
    try:
        result = await db.execute(
            select(ModuleModel).where(ModuleModel.module_id == module_id)
        )
        module = result.scalar_one_or_none()
        
        if not module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Module {module_id} not found"
            )
        
        # Update fields if provided
        if module_data.title is not None:
            module.title = module_data.title
        if module_data.description is not None:
            module.description = module_data.description
        if module_data.order_index is not None:
            module.order_index = module_data.order_index
        if module_data.is_published is not None:
            module.is_published = module_data.is_published
        if module_data.metadata_json is not None:
            module.metadata_json = module_data.metadata_json
        
        await db.commit()
        await db.refresh(module)
        
        logger.info(f"Updated module {module_id}")
        
        return ModuleRead.model_validate(module)
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to update module: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update module: {str(e)}"
        )


@router.delete("/modules/{module_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_module(
    module_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Delete a module.
    
    Activities within the module will have their module_id set to NULL (CASCADE).
    """
    try:
        result = await db.execute(
            select(ModuleModel).where(ModuleModel.module_id == module_id)
        )
        module = result.scalar_one_or_none()
        
        if not module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Module {module_id} not found"
            )
        
        await db.delete(module)
        await db.commit()
        
        logger.info(f"Deleted module {module_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to delete module: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete module: {str(e)}"
        )


@router.put("/courses/{course_id}/modules/reorder")
async def reorder_modules(
    course_id: str,
    module_ids: List[str],
    db: AsyncSession = Depends(get_db_session)
):
    """
    Reorder modules within a course.
    
    Accepts ordered list of module_ids and updates their order_index.
    """
    try:
        for index, module_id in enumerate(module_ids):
            result = await db.execute(
                select(ModuleModel).where(
                    ModuleModel.module_id == module_id,
                    ModuleModel.course_id == course_id
                )
            )
            module = result.scalar_one_or_none()
            
            if module:
                module.order_index = index
        
        await db.commit()
        
        logger.info(f"Reordered {len(module_ids)} modules in course {course_id}")
        
        return {"message": f"Reordered {len(module_ids)} modules", "course_id": course_id}
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to reorder modules: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reorder modules: {str(e)}"
        )


# ==================== ENROLLMENT MANAGEMENT ====================

@router.post("/enrollments", response_model=EnrollmentRead, status_code=status.HTTP_201_CREATED)
async def create_enrollment(
    enrollment_data: EnrollmentCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Enroll a user in a course with a specific role.
    
    Replaces old course_id foreign key in user_profiles.
    """
    try:
        # Check if enrollment already exists for this user+course+module combo
        query = select(EnrollmentModel).where(
            EnrollmentModel.user_id == enrollment_data.user_id,
            EnrollmentModel.course_id == enrollment_data.course_id
        )
        # If module_id is specified, check for duplicate in same module
        if enrollment_data.module_id:
            query = query.where(EnrollmentModel.module_id == enrollment_data.module_id)
        
        existing = await db.execute(query)
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already enrolled in this course/module"
            )
        
        # Create enrollment
        enrollment_id = str(uuid.uuid4())
        enrollment = EnrollmentModel(
            enrollment_id=enrollment_id,
            user_id=enrollment_data.user_id,
            course_id=enrollment_data.course_id,
            module_id=enrollment_data.module_id,
            role=enrollment_data.role,
            status=enrollment_data.status,
            metadata_json=enrollment_data.metadata_json,
        )
        
        db.add(enrollment)
        await db.commit()
        await db.refresh(enrollment)
        
        logger.info(f"Enrolled user {enrollment_data.user_id} in course {enrollment_data.course_id} as {enrollment_data.role}")
        
        return EnrollmentRead.model_validate(enrollment)
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create enrollment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create enrollment: {str(e)}"
        )


@router.get("/users/{user_id}/enrollments", response_model=List[EnrollmentRead])
async def list_user_enrollments(
    user_id: str,
    status_filter: Optional[str] = "ACTIVE",
    db: AsyncSession = Depends(get_db_session)
):
    """
    List all enrollments for a user.
    
    Supports filtering by status (ACTIVE, INACTIVE, COMPLETED, DROPPED).
    """
    try:
        query = select(EnrollmentModel).where(EnrollmentModel.user_id == user_id)
        
        if status_filter:
            query = query.where(EnrollmentModel.status == status_filter)
        
        result = await db.execute(query)
        enrollments = result.scalars().all()
        
        return [EnrollmentRead.model_validate(e) for e in enrollments]
        
    except Exception as e:
        logger.error(f"Failed to list enrollments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list enrollments: {str(e)}"
        )


@router.get("/modules/{module_id}/students")
async def get_module_students(
    module_id: str,
    status_filter: Optional[str] = "ACTIVE",
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get all students enrolled in a specific module/commission.
    
    Returns user details with enrollment info.
    """
    try:
        from sqlalchemy import text
        
        query_str = """
            SELECT 
                e.enrollment_id,
                e.user_id,
                e.role,
                e.status,
                e.enrolled_at,
                u.full_name,
                u.email
            FROM enrollments e
            JOIN users u ON e.user_id = u.id
            WHERE e.module_id = :module_id
        """
        
        if status_filter:
            query_str += " AND e.status = :status"
            
        query_str += " ORDER BY e.enrolled_at DESC"
        
        params = {"module_id": module_id}
        if status_filter:
            params["status"] = status_filter
            
        result = await db.execute(text(query_str), params)
        rows = result.fetchall()
        
        students = []
        for row in rows:
            students.append({
                "enrollment_id": row.enrollment_id,
                "user_id": row.user_id,
                "role": row.role,
                "status": row.status,
                "enrolled_at": row.enrolled_at.isoformat() if row.enrolled_at else None,
                "full_name": row.full_name,
                "email": row.email,
            })
        
        return students
        
    except Exception as e:
        logger.error(f"Failed to get module students: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get module students: {str(e)}"
        )


@router.get("/modules/{module_id}/available-students")
async def get_available_students_for_module(
    module_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get all students (users with 'student' role) that are NOT enrolled in the specified module.
    
    Returns list of students available to be added to the module.
    """
    try:
        from sqlalchemy import text
        
        query_str = """
            SELECT 
                u.id as user_id,
                u.full_name,
                u.email,
                u.username
            FROM users u
            WHERE u.roles @> '["student"]'::jsonb
              AND u.id NOT IN (
                  SELECT e.user_id 
                  FROM enrollments e 
                  WHERE e.module_id = :module_id
              )
            ORDER BY u.full_name, u.email
        """
        
        result = await db.execute(text(query_str), {"module_id": module_id})
        rows = result.fetchall()
        
        available_students = []
        for row in rows:
            available_students.append({
                "user_id": row.user_id,
                "full_name": row.full_name or row.username,
                "email": row.email,
                "username": row.username,
            })
        
        return available_students
        
    except Exception as e:
        logger.error(f"Failed to get available students: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get available students: {str(e)}"
        )


@router.get("/modules/{module_id}/activities")
async def get_module_activities(
    module_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get all activities in a specific module/commission.
    """
    try:
        from sqlalchemy import text
        
        query_str = """
            SELECT 
                a.activity_id,
                a.title,
                a.instructions,
                a.difficulty,
                a.estimated_duration_minutes,
                a.order_index,
                a.status,
                a.created_at,
                COUNT(DISTINCT s.submission_id) as total_submissions,
                COUNT(DISTINCT CASE WHEN s.status = 'graded' THEN s.submission_id END) as graded_submissions
            FROM activities a
            LEFT JOIN submissions s ON a.activity_id = s.activity_id
            WHERE a.module_id = :module_id
            GROUP BY a.activity_id
            ORDER BY a.order_index ASC, a.created_at DESC
        """
        
        result = await db.execute(text(query_str), {"module_id": module_id})
        rows = result.fetchall()
        
        logger.info(f"📊 Module {module_id} - Found {len(rows)} activities")
        
        activities = []
        for row in rows:
            activities.append({
                "activity_id": row.activity_id,
                "title": row.title,
                "instructions": row.instructions,
                "difficulty": row.difficulty,
                "estimated_duration_minutes": row.estimated_duration_minutes,
                "order_index": row.order_index,
                "status": row.status,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "total_submissions": row.total_submissions or 0,
                "graded_submissions": row.graded_submissions or 0,
            })
        
        logger.info(f"📊 Returning {len(activities)} activities")
        return activities
        
    except Exception as e:
        logger.error(f"Failed to get module activities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get module activities: {str(e)}"
        )


@router.get("/modules/{module_id}/stats")
async def get_module_stats(
    module_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get statistics for a module: students count, activities count, submissions, etc.
    """
    try:
        from sqlalchemy import text
        
        stats_query = """
            SELECT 
                (SELECT COUNT(*) FROM enrollments WHERE module_id = :module_id AND status = 'ACTIVE') as active_students,
                (SELECT COUNT(*) FROM activities WHERE module_id = :module_id) as total_activities,
                (SELECT COUNT(DISTINCT s.student_id) 
                 FROM submissions s 
                 JOIN activities a ON s.activity_id = a.activity_id 
                 WHERE a.module_id = :module_id) as students_with_submissions,
                (SELECT COUNT(*) 
                 FROM submissions s 
                 JOIN activities a ON s.activity_id = a.activity_id 
                 WHERE a.module_id = :module_id) as total_submissions,
                (SELECT AVG(s.final_grade) 
                 FROM submissions s 
                 JOIN activities a ON s.activity_id = a.activity_id 
                 WHERE a.module_id = :module_id AND s.status = 'graded') as average_grade
        """
        
        result = await db.execute(text(stats_query), {"module_id": module_id})
        row = result.fetchone()
        
        return {
            "active_students": row.active_students or 0,
            "total_activities": row.total_activities or 0,
            "students_with_submissions": row.students_with_submissions or 0,
            "total_submissions": row.total_submissions or 0,
            "average_grade": float(row.average_grade) if row.average_grade else None,
        }
        
    except Exception as e:
        logger.error(f"Failed to get module stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get module stats: {str(e)}"
        )
