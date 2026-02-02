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
)
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from pathlib import Path
import os
import logging

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

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/teacher", tags=["Teacher"])


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
        
        return [
            ExerciseResponse(
                exercise_id=ex.exercise_id,
                title=ex.title,
                description=ex.description,
                difficulty=ex.difficulty,
                language=ex.language,
                mission_markdown=ex.mission_markdown,
                starter_code=ex.starter_code,
                has_solution=ex.has_solution,
                test_cases=[
                    TestCaseResponse(
                        test_number=tc.test_number,
                        description=tc.description,
                        input_data=tc.input_data,
                        expected_output=tc.expected_output,
                        is_hidden=tc.is_hidden,
                        timeout_seconds=tc.timeout_seconds,
                    )
                    for tc in ex.test_cases
                ],
                concepts=ex.concepts,
                learning_objectives=ex.learning_objectives,
                estimated_time_minutes=ex.estimated_time_minutes,
                visible_test_count=ex.visible_test_count,
                hidden_test_count=ex.hidden_test_count,
            )
            for ex in exercises
        ]
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get exercises: {str(e)}"
        )


@router.get("/activities", response_model=List[ActivityListItem])
async def list_activities(
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
        concepts_list = [c.strip() for c in concepts.split(",")] if concepts else []
        
        # Create requirements
        requirements = ExerciseRequirements(
            topic=topic,
            difficulty=difficulty,
            language=language,
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
            model_name="mistral-small-latest",
            temperature=0.7
        )
        
        # Start generation asynchronously
        async def run_generation():
            try:
                result = await generator.start_generation(
                    teacher_id=teacher_id,
                    course_id=course_id,
                    pdf_path=str(pdf_path),
                    requirements=requirements
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
            temperature=0.7
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
            temperature=0.7
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
        )   )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get draft for job {job_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve draft: {str(e)}"
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
            activity_title=approval.activity_title if hasattr(approval, 'activity_title') else None,
            activity_description=approval.activity_description if hasattr(approval, 'activity_description') else None
        )
        
        if "error" in result:
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
