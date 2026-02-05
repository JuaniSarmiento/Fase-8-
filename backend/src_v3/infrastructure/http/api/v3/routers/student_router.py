"""
Student HTTP Router - API v3

Endpoints for student learning interactions.
"""
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Request
from pydantic import BaseModel, Field, computed_field
from typing import Optional, List
from datetime import datetime
import logging
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

# Redis cache decorator
from backend.src_v3.infrastructure.cache.decorators import cached

from backend.src_v3.application.student.use_cases import (
    StartLearningSessionUseCase,
    SendMessageToTutorUseCase,
    GetSessionHistoryUseCase,
    SubmitCodeForReviewUseCase,
    StartSessionCommand,
    SendMessageCommand,
    GetSessionHistoryCommand,
)

from backend.src_v3.infrastructure.ai.agents import SocraticTutorAgent
from backend.src_v3.application.schemas.lms_hierarchy_schemas import (
    CourseWithModules,
    ModuleRead,
    UserGamificationRead,
)
from backend.src_v3.infrastructure.persistence.sqlalchemy.models import (
    ModuleModel,
    EnrollmentModel,
    EnrollmentStatus,
    UserGamificationModel,
    ActivityModel,
)
from sqlalchemy import select
from sqlalchemy.orm import selectinload

# Logger
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/student", tags=["Student"])


# ==================== REQUEST/RESPONSE MODELS ====================

class StartSessionRequest(BaseModel):
    """Request to start session.

    Accepts both string and integer IDs for backward compatibility with
    legacy tests that send numeric identifiers.
    """
    student_id: str | int = Field(..., description="Student user ID")
    activity_id: str | int = Field(..., description="Activity ID")
    course_id: Optional[str | int] = Field(None, description="Course ID")
    mode: str = Field("SOCRATIC", description="Tutor mode")


class StartSessionResponse(BaseModel):
    """Response with session details"""
    session_id: str
    student_id: str
    activity_id: str
    mode: str
    cognitive_phase: str
    start_time: datetime
    is_active: bool


class SendMessageRequest(BaseModel):
    """Request to send message"""
    message: str = Field(..., min_length=1, description="Student message")
    current_code: Optional[str] = Field(None, description="Current code context")
    error_context: Optional[dict] = Field(None, description="Error details if any")
    exercise_context: Optional[dict] = Field(None, description="Current exercise details (title, description, mission)")


class TutorMessageResponse(BaseModel):
    """Response with tutor message"""
    message_id: str
    session_id: str
    sender: str
    content: str
    timestamp: datetime
    cognitive_phase: str
    frustration_level: float
    understanding_level: float

    @computed_field
    @property
    def response(self) -> str:
        """Backward compatible field alias for content.

        Some legacy tests expect a top-level "response" key in the
        JSON payload. We expose it as a computed field that mirrors
        the content field so both shapes are supported.
        """
        return self.content


class SessionHistoryResponse(BaseModel):
    """Response with conversation history"""
    session_id: str
    student_id: str
    activity_id: str
    message_count: int
    messages: List[TutorMessageResponse]
    average_frustration: float
    requires_intervention: bool


class SubmitCodeRequest(BaseModel):
    """Request to submit code"""
    code: str = Field(..., min_length=1, description="Code to review")
    language: str = Field("python", description="Programming language")
    exercise_id: Optional[str] = Field(None, description="Exercise ID for grading")
    is_final_submission: bool = Field(False, description="Is final submission")
    all_exercise_codes: Optional[dict] = Field(None, description="All exercise codes (exercise_id -> code) for final submission")


class SubmitCodeResponse(BaseModel):
    """Response with code review and grade"""
    feedback: str
    execution: dict
    passed: bool
    grade: int = 0
    suggestion: str = ""
    tests_passed: bool = False
    details: dict = {}



# ==================== READ MODELS ====================

class ActivityInfo(BaseModel):
    activity_id: str
    title: str
    instructions: str
    status: str
    created_at: Optional[datetime]
    # Simplified view for students

class ExerciseInfo(BaseModel):
    exercise_id: str
    title: str
    description: str
    difficulty: str
    language: str
    mission_markdown: str
    starter_code: str
    # Hide solution and hidden tests

# ==================== DEPENDENCY INJECTION ====================

async def get_db_session():
    """Get database session"""
    from backend.src_v3.infrastructure.persistence.database import get_db_session as db_session
    async for session in db_session():
        yield session


async def get_start_session_use_case(db=Depends(get_db_session)):
    """Inject StartLearningSessionUseCase"""
    from backend.src_v3.infrastructure.dependencies import get_start_session_use_case
    return get_start_session_use_case(db)


async def get_send_message_use_case(db=Depends(get_db_session)):
    """Inject SendMessageToTutorUseCase"""
    from backend.src_v3.infrastructure.dependencies import get_send_message_use_case
    return get_send_message_use_case(db)


async def get_history_use_case(db=Depends(get_db_session)):
    """Inject GetSessionHistoryUseCase"""
    from backend.src_v3.infrastructure.dependencies import get_session_history_use_case
    return get_session_history_use_case(db)


async def get_submit_code_use_case(db=Depends(get_db_session)):
    """Inject SubmitCodeForReviewUseCase"""
    from backend.src_v3.infrastructure.dependencies import get_submit_code_use_case
    return get_submit_code_use_case(db)


async def get_teacher_repo(db=Depends(get_db_session)):
    """Inject TeacherRepository for reading activities"""
    from backend.src_v3.infrastructure.dependencies import get_teacher_repository
    return get_teacher_repository(db)


# ==================== ENDPOINTS ====================

@router.get("/activities", response_model=List[ActivityInfo])
@cached(ttl=45, key_prefix="student_activities")  # Cache for 45 seconds
async def list_available_activities(
    request: Request,
    student_id: Optional[str] = None,
    repo = Depends(get_teacher_repo)
):
    """List available activities for student."""
    try:
        activities = await repo.get_published_activities()
        return [
            ActivityInfo(
                activity_id=a.activity_id,
                title=a.title,
                instructions=a.instructions,
                status=a.status,
                created_at=None # simplified
            ) for a in activities
        ]
    except Exception as e:
        logger.error(f"Error listing activities: {e}")
        raise HTTPException(status_code=500, detail="Error fetching activities")


@router.get("/activities/{activity_id}", response_model=ActivityInfo)
async def get_activity_detail(
    activity_id: str,
    student_id: Optional[str] = None,
    repo = Depends(get_teacher_repo)
):
    """Get activity detail."""
    try:
        activity = await repo.get_activity_by_id(activity_id)
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")
        
        return ActivityInfo(
            activity_id=activity.activity_id,
            title=activity.title,
            instructions=activity.instructions,
            status=activity.status,
            created_at=None
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting activity: {e}")
        raise HTTPException(status_code=500, detail="Error fetching activity")


@router.get("/activities/{activity_id}/exercises", response_model=List[ExerciseInfo])
async def get_activity_exercises(
    activity_id: str,
    student_id: Optional[str] = None,
    repo = Depends(get_teacher_repo)
):
    """Get exercises for an activity."""
    try:
        activity = await repo.get_activity_by_id(activity_id)
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")
            
        exercises = await repo.get_exercises_for_activity(activity_id)
        
        return [
            ExerciseInfo(
                exercise_id=ex.exercise_id,
                title=ex.title,
                description=ex.description,
                difficulty=ex.difficulty,
                language=ex.language,
                mission_markdown=ex.mission_markdown,
                starter_code=ex.starter_code
            ) for ex in exercises
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching exercises: {e}")
        raise HTTPException(status_code=500, detail="Error fetching exercises")


@router.post("/sessions", response_model=StartSessionResponse, status_code=status.HTTP_201_CREATED)
async def start_session(
    request: StartSessionRequest,
    use_case: StartLearningSessionUseCase = Depends(get_start_session_use_case)
):
    """
    Start new learning session.
    
    Creates a new session with initial cognitive state.
    """
    try:
        command = StartSessionCommand(
            student_id=str(request.student_id),
            activity_id=str(request.activity_id),
            course_id=str(request.course_id) if request.course_id is not None else None,
            mode=request.mode,
        )
        
        session = await use_case.execute(command)
        
        return StartSessionResponse(
            session_id=session.session_id,
            student_id=session.student_id,
            activity_id=session.activity_id,
            mode=session.mode.name,
            cognitive_phase=session.cognitive_phase.name,
            start_time=session.start_time,
            is_active=session.is_active,
        )
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Failed to start session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start session: {str(e)}"
        )


@router.post("/sessions/{session_id}/chat", response_model=TutorMessageResponse)
async def send_message(
    session_id: str,
    request: SendMessageRequest,
    use_case: SendMessageToTutorUseCase = Depends(get_send_message_use_case)
):
    """
    Send message to Socratic tutor.
    
    Returns tutor response following Socratic methodology.
    """
    try:
        command = SendMessageCommand(
            session_id=session_id,
            message=request.message,
            current_code=request.current_code,
            error_context=request.error_context,
            exercise_context=request.exercise_context,
        )
        
        tutor_message = await use_case.execute(command)
        
        # Handle cognitive_phase being either enum or string
        phase = tutor_message.cognitive_phase
        phase_name = phase.name if hasattr(phase, 'name') else str(phase)
        
        return TutorMessageResponse(
            message_id=tutor_message.message_id,
            session_id=tutor_message.session_id,
            sender=tutor_message.sender,
            content=tutor_message.content,
            timestamp=tutor_message.timestamp,
            cognitive_phase=phase_name,
            frustration_level=tutor_message.frustration_level,
            understanding_level=tutor_message.understanding_level,
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        import traceback
        logger.error(f"CHAT ERROR: {type(e).__name__}: {str(e)}")
        logger.error(f"CHAT TRACEBACK: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}"
        )


@router.get("/sessions/{session_id}/history", response_model=SessionHistoryResponse)
async def get_history(
    session_id: str,
    limit: int = 50,
    use_case: GetSessionHistoryUseCase = Depends(get_history_use_case)
):
    """
    Get session conversation history.
    
    Returns all messages with cognitive metrics.
    """
    try:
        command = GetSessionHistoryCommand(
            session_id=session_id,
            limit=limit,
        )
        
        dialogue = await use_case.execute(command)
        
        messages_response = [
            TutorMessageResponse(
                message_id=msg.message_id,
                session_id=msg.session_id,
                sender=msg.sender,
                content=msg.content,
                timestamp=msg.timestamp,
                cognitive_phase=msg.cognitive_phase.name,
                frustration_level=msg.frustration_level,
                understanding_level=msg.understanding_level,
            )
            for msg in dialogue.messages
        ]
        
        return SessionHistoryResponse(
            session_id=dialogue.session_id,
            student_id=dialogue.student_id,
            activity_id=dialogue.activity_id,
            message_count=dialogue.message_count,
            messages=messages_response,
            average_frustration=dialogue.average_frustration,
            requires_intervention=dialogue.requires_intervention,
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get history: {str(e)}"
        )


class SubmitSessionCodeResponse(BaseModel):
    """Response code submission in session"""
    grade: int
    feedback: str
    suggestion: str
    tests_passed: bool
    passed: bool
    details: dict
    execution: dict


@router.post("/sessions/{session_id}/submit", response_model=SubmitSessionCodeResponse)
async def submit_code(
    session_id: str,
    request: SubmitCodeRequest,
    use_case: SubmitCodeForReviewUseCase = Depends(get_submit_code_use_case),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Submit code for auditor review.
    
    Executes code in sandbox and provides AI feedback.
    If is_final_submission=True, evaluates ALL exercises in the activity.
    """
    from sqlalchemy import text
    
    logger.info(f"--- SUBMIT CODE CMD --- Session: {session_id}, Final: {request.is_final_submission}")
    
    try:
        # 0. Si es final submission, verificar que no haya sido ya completada
        if request.is_final_submission:
            # Primero obtener user_id y activity_id de la sesión
            session_check = await db.execute(text("""
                SELECT user_id, activity_id FROM sessions_v2 WHERE session_id = :sid
            """), {"sid": session_id})
            session_data = session_check.fetchone()
            
            if session_data:
                user_id, activity_id = session_data
                # Verificar si ya existe una submission final previa en la tabla submissions
                # Estados válidos: submitted, graded, reviewed (no 'completed')
                attempt_check = await db.execute(text("""
                    SELECT final_grade FROM submissions
                    WHERE student_id = :uid AND activity_id = :aid 
                      AND status IN ('submitted', 'graded', 'reviewed') AND final_grade IS NOT NULL
                    ORDER BY submitted_at DESC
                    LIMIT 1
                """), {"uid": user_id, "aid": activity_id})
                previous_submission = attempt_check.fetchone()
                
                if previous_submission:
                    logger.warning(f"Actividad ya completada previamente con nota {previous_submission.final_grade}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Esta actividad ya fue completada. Nota final: {previous_submission.final_grade}/100. No se pueden hacer múltiples submissions."
                    )
        
        # 1. Execute current code (Draft or Final)
        logger.info(f"Submitting code for session {session_id}, exercise {request.exercise_id}")
        result = await use_case.execute(
            session_id=session_id,
            code=request.code,
            language=request.language,
            exercise_id=request.exercise_id,
        )
        logger.info(f"Submit execution success. Result keys: {result.keys()}")
        
        # 2. If Final Submission, Perform Full Activity Audit
        if request.is_final_submission:
            logger.info("Performing Full Activity Audit (Final Submission detected)")
            try:
                from sqlalchemy import text
                import json
                import os
                from langchain_mistralai import ChatMistralAI
                from datetime import datetime
                
                # A. Get Context (Activity & Student) from Session
                logger.info(f"Fetching session context for {session_id}")
                session_result = await db.execute(text("""
                    SELECT activity_id, user_id FROM sessions_v2 WHERE session_id = :sid
                """), {"sid": session_id})
                session_row = session_result.fetchone()
                
                if session_row:
                    activity_id, student_id = session_row
                    logger.info(f"Context found: Activity={activity_id}, Student={student_id}")
                    
                    # A.1. SAVE ALL EXERCISE CODES from frontend (if provided)
                    if request.all_exercise_codes:
                        logger.info(f"Saving {len(request.all_exercise_codes)} exercise codes from frontend")
                        for exercise_id, code_text in request.all_exercise_codes.items():
                            if code_text and code_text.strip():
                                try:
                                    # Insert or update exercise attempt
                                    await db.execute(text("""
                                        INSERT INTO exercise_attempts_v2 
                                        (user_id, exercise_id, code_submitted, passed, grade, ai_feedback, submitted_at, session_id)
                                        VALUES (:user_id, :exercise_id, :code, false, 0, 'Pendiente de evaluación', :submitted_at, :session_id)
                                    """), {
                                        "user_id": student_id,
                                        "exercise_id": exercise_id,
                                        "code": code_text,
                                        "submitted_at": datetime.utcnow(),
                                        "session_id": session_id
                                    })
                                    logger.info(f"Saved code for exercise {exercise_id}")
                                except Exception as save_error:
                                    logger.warning(f"Could not save exercise {exercise_id}: {save_error}")
                        
                        await db.commit()
                        logger.info("All exercise codes saved successfully")
                    
                    # B. Fetch ALL Exercises & Attempts
                    exercises_result = await db.execute(text("""
                        WITH latest_attempts AS (
                            SELECT 
                                exercise_id,
                                code_submitted,
                                passed,
                                submitted_at,
                                ROW_NUMBER() OVER (PARTITION BY exercise_id ORDER BY submitted_at DESC) as rn
                            FROM exercise_attempts_v2
                            WHERE user_id = :student_id
                        )
                        SELECT 
                            e.exercise_id,
                            e.title,
                            e.difficulty,
                            COALESCE(la.code_submitted, '') as code_submitted,
                            COALESCE(la.passed, false) as passed
                        FROM exercises_v2 e
                        LEFT JOIN latest_attempts la ON e.exercise_id = la.exercise_id AND la.rn = 1
                        WHERE e.activity_id = :activity_id AND e.deleted_at IS NULL
                        ORDER BY e.unit_number
                    """), {"activity_id": activity_id, "student_id": student_id})
                    
                    all_exercises = exercises_result.fetchall()
                    
                    # C. Build Comprehensive Prompt
                    exercises_text = ""
                    for i, ex in enumerate(all_exercises):
                        status_text = "✅ CORRECTO" if ex[4] else "❌ INCORRECTO/NO INTENTADO"
                        code_snippet = ex[3][:400] if ex[3] else "(Sin código)"
                        exercises_text += f"\nEJERCICIO {i+1}: {ex[1]} ({ex[2]})\nEstado: {status_text}\nCódigo:\n{code_snippet}\n"

                    audit_prompt = f"""Actúas como un Profesor Senior de Programación.
El estudiante ha finalizado la actividad. Tu tarea es evaluar TODOS los {len(all_exercises)} ejercicios y dar un feedback específico para cada uno.

LISTADO DE EJERCICIOS:
{exercises_text}

INSTRUCCIONES:
Para CADA ejercicio, analiza:
1. Si está vacío o incorrecto: Explica qué falta o por qué falla. Nota: 0-40
2. Si está parcialmente correcto o mejorable: Indica qué falta mejorar. Nota: 50-70
3. Si está correcto: Elogia brevemente una buena práctica usada. Nota: 80-100

IMPORTANTE: 
- Asigna una NOTA NUMÉRICA (0-100) a cada ejercicio
- La nota final debe ser el PROMEDIO de todas las notas individuales
- NO uses la palabra "Mejorable" como status, usa "Correcto" o "Incorrecto"

FORMATO DE RESPUESTA (JSON estricto):
Devuelve un JSON con esta estructura exacta:
{{
  "final_grade": <promedio de todas las notas individuales>,
  "general_feedback": "<Resumen general de 2 líneas>",
  "exercises_audit": [
    {{
      "order": <número 1..N>,
      "title": "<título del ejercicio>",
      "grade": <0-100 número entero>,
      "status": "<Correcto | Incorrecto>",
      "feedback": "<Razón específica de 1 o 2 frases>"
    }},
    ...
  ]
}}
"""
                    # D. Call AI
                    mistral_api_key = os.getenv("MISTRAL_API_KEY")
                    logger.info(f"Mistral Key Present: {bool(mistral_api_key)}, Length: {len(mistral_api_key) if mistral_api_key else 0}")
                    if mistral_api_key:
                        llm = ChatMistralAI(
                            model="mistral-large-latest", # Use large for better analysis
                            api_key=mistral_api_key,
                            temperature=0.4
                        )
                        ai_response = await llm.ainvoke(audit_prompt)
                        
                        # E. Parse & Enrich Result
                        try:
                            # Clean markdown code blocks if present
                            clean_content = ai_response.content.replace("```json", "").replace("```", "").strip()
                            audit_data = json.loads(clean_content)
                            
                            # Initialize details if not present
                            if 'details' not in result:
                                result['details'] = {}
                            
                            # Inject into details
                            result['details']['full_audit'] = audit_data
                            result['feedback'] = audit_data.get('general_feedback', result['feedback'])
                            
                            # Override final grade with calculated average
                            calculated_grade = audit_data.get('final_grade', 0)
                            result['grade'] = calculated_grade
                            
                            # F. PERSIST: Update exercise attempts with grades and feedback
                            exercises_audit = audit_data.get('exercises_audit', [])
                            for ex_audit in exercises_audit:
                                ex_order = ex_audit.get('order', 0)
                                if ex_order > 0 and ex_order <= len(all_exercises):
                                    ex_data = all_exercises[ex_order - 1]
                                    ex_id = ex_data[0]  # exercise_id
                                    
                                    # Use grade from AI response
                                    ex_grade = ex_audit.get('grade', 0)
                                    
                                    # Ensure grade is within valid range
                                    ex_grade = max(0, min(100, ex_grade))
                                    
                                    # Update the latest attempt for this exercise with grade and feedback
                                    await db.execute(text("""
                                        UPDATE exercise_attempts_v2 
                                        SET grade = :grade, ai_feedback = :feedback, passed = :passed
                                        WHERE attempt_id = (
                                            SELECT attempt_id FROM exercise_attempts_v2 
                                            WHERE exercise_id = :ex_id AND user_id = :student_id 
                                            ORDER BY submitted_at DESC LIMIT 1
                                        )
                                    """), {
                                        "grade": ex_grade,
                                        "feedback": ex_audit.get('feedback', ''),
                                        "passed": ex_grade >= 60,
                                        "ex_id": ex_id,
                                        "student_id": student_id
                                    })
                            
                            # G. RISK ANALYSIS: Calculate AI dependency with message quality analysis
                            import uuid
                            import re
                            
                            logger.info(f"Starting risk analysis for session {session_id}")
                            
                            # Count tutor interactions (AI dependency metric)
                            tutor_count_result = await db.execute(text("""
                                SELECT COUNT(*) FROM cognitive_traces_v2 
                                WHERE session_id = :sid AND interaction_type = 'tutor_response'
                            """), {"sid": session_id})
                            tutor_messages = tutor_count_result.scalar() or 0
                            
                            logger.info(f"Tutor messages: {tutor_messages}")
                            
                            # Get student messages for content analysis
                            student_messages_result = await db.execute(text("""
                                SELECT interactional_data->>'content' as content
                                FROM cognitive_traces_v2
                                WHERE session_id = :sid AND interaction_type = 'student_message'
                                ORDER BY timestamp
                            """), {"sid": session_id})
                            student_messages = [row[0] for row in student_messages_result.fetchall()]
                            
                            logger.info(f"Student messages count: {len(student_messages)}")
                            
                            # Count student code submissions (all exercises in all_exercise_codes)
                            total_submissions = len(request.all_exercise_codes) if request.all_exercise_codes else 1
                            
                            logger.info(f"Total submissions (exercises): {total_submissions}")
                            
                            # === MESSAGE QUALITY ANALYSIS ===
                            # Patterns for high-risk messages
                            code_request_patterns = [
                                r'dame\s+(el\s+)?c[óo]digo',
                                r'haz(me)?(\s+el)?\s+(ejercicio|c[óo]digo)',
                                r'resuelve(\s+el)?\s+(ejercicio|problema)',
                                r'c[óo]digo\s+completo',
                                r'necesito\s+(el\s+)?c[óo]digo',
                                r'env[íi]ame\s+(el\s+)?c[óo]digo',
                                r'cu[áa]l\s+es\s+(el\s+)?c[óo]digo',
                                r'p[áa]same\s+(el\s+)?c[óo]digo',
                                r'quiero\s+(el\s+)?c[óo]digo'
                            ]
                            
                            profanity_patterns = [
                                r'\bmierda\b',
                                r'\bcarajo\b',
                                r'\bchingad',
                                r'\bchucha\b',
                                r'\bctm\b',
                                r'\bptm\b',
                                r'\bput[ao]',
                                r'\bcoñ[oa]',
                                r'\bverga\b',
                                r'\bpend[eé]j',
                                r'\bconchetumare\b'
                            ]
                            
                            # Count message types
                            code_requests = 0
                            profanity_count = 0
                            
                            for msg in student_messages:
                                msg_lower = msg.lower()
                                
                                # Check for code requests
                                for pattern in code_request_patterns:
                                    if re.search(pattern, msg_lower):
                                        code_requests += 1
                                        break
                                
                                # Check for profanity
                                for pattern in profanity_patterns:
                                    if re.search(pattern, msg_lower):
                                        profanity_count += 1
                                        break
                            
                            # Calculate risk metrics
                            ai_dependency_ratio = tutor_messages / max(total_submissions, 1)
                            code_request_ratio = code_requests / max(len(student_messages), 1)
                            profanity_ratio = profanity_count / max(len(student_messages), 1)
                            
                            # === COMPREHENSIVE RISK SCORING ===
                            risk_score = 0
                            risk_factors = []
                            
                            # Factor 1: Message quantity (0-40 points)
                            if ai_dependency_ratio > 3:
                                risk_score += 40
                                risk_factors.append(f"Alta frecuencia de consultas ({tutor_messages} msgs / {total_submissions} ejercicios)")
                            elif ai_dependency_ratio > 1.5:
                                risk_score += 20
                                risk_factors.append(f"Frecuencia moderada de consultas ({tutor_messages} msgs / {total_submissions} ejercicios)")
                            
                            # Factor 2: Code requests (0-40 points)
                            if code_request_ratio > 0.5:
                                risk_score += 40
                                risk_factors.append(f"Solicita código directamente en {code_requests}/{len(student_messages)} mensajes")
                            elif code_request_ratio > 0.2:
                                risk_score += 25
                                risk_factors.append(f"Algunas peticiones de código ({code_requests} mensajes)")
                            elif code_requests > 0:
                                risk_score += 10
                                risk_factors.append(f"Pocas peticiones de código ({code_requests} mensajes)")
                            
                            # Factor 3: Profanity/frustration (0-20 points) 1. 
                            if profanity_ratio > 0.3:
                                risk_score += 20
                                risk_factors.append(f"Alta frustración/lenguaje inapropiado ({profanity_count} mensajes)")
                            elif profanity_ratio > 0.1:
                                risk_score += 10
                                risk_factors.append(f"Signos de frustración ({profanity_count} mensajes)")
                            
                            # Determine risk level based on score
                            if risk_score >= 60:
                                risk_level = "high"
                                risk_description = f"Riesgo ALTO detectado (score: {risk_score}/100). " + "; ".join(risk_factors)
                            elif risk_score >= 30:
                                risk_level = "medium"
                                risk_description = f"Riesgo MODERADO (score: {risk_score}/100). " + "; ".join(risk_factors)
                            else:
                                risk_level = "low"
                                risk_description = f"Uso apropiado de IA (score: {risk_score}/100). Consultas conceptuales y trabajo autónomo."
                            
                            # Save risk analysis
                            risk_id = str(uuid.uuid4())
                            await db.execute(text("""
                                INSERT INTO risks_v2 
                                (risk_id, session_id, activity_id, risk_level, risk_dimension, description, recommendations, resolved, created_at)
                                VALUES (:risk_id, :session_id, :activity_id, :risk_level, :risk_dimension, :description, :recommendations, false, NOW())
                            """), {
                                "risk_id": risk_id,
                                "session_id": session_id,
                                "activity_id": activity_id,
                                "risk_level": risk_level,
                                "risk_dimension": "ai_dependency",
                                "description": risk_description,
                                "recommendations": json.dumps({
                                    "risk_score": risk_score,
                                    "ai_dependency_ratio": round(ai_dependency_ratio, 2),
                                    "tutor_messages": tutor_messages,
                                    "code_submissions": total_submissions,
                                    "code_requests": code_requests,
                                    "code_request_ratio": round(code_request_ratio, 2),
                                    "profanity_count": profanity_count,
                                    "profanity_ratio": round(profanity_ratio, 2),
                                    "total_student_messages": len(student_messages),
                                    "risk_factors": risk_factors,
                                    "final_grade": audit_data.get('final_grade', 0),
                                    "grade_justification": audit_data.get('general_feedback', '')
                                })
                            })
                            
                            # Add risk info to result
                            result['details']['risk_analysis'] = {
                                "level": risk_level,
                                "risk_score": risk_score,
                                "ai_dependency_ratio": round(ai_dependency_ratio, 2),
                                "tutor_messages": tutor_messages,
                                "code_submissions": total_submissions,
                                "code_requests": code_requests,
                                "profanity_count": profanity_count,
                                "risk_factors": risk_factors
                            }
                            
                            logger.info(f"Risk analysis complete: level={risk_level}, score={risk_score}, code_requests={code_requests}, profanity={profanity_count}")
                            
                            # H. SAVE FINAL SUBMISSION to submissions table
                            submission_id = str(uuid.uuid4())
                            final_grade_value = audit_data.get('final_grade', 0)
                            await db.execute(text("""
                                INSERT INTO submissions (
                                    submission_id, student_id, activity_id, code_snapshot,
                                    status, submitted_at, auto_grade, final_grade, ai_feedback,
                                    created_at, updated_at
                                )
                                VALUES (:id, :student_id, :activity_id, :code, :status, :submitted_at, 
                                        :auto_grade, :final_grade, :ai_feedback, NOW(), NOW())
                                ON CONFLICT (submission_id) DO UPDATE SET
                                    final_grade = EXCLUDED.final_grade,
                                    ai_feedback = EXCLUDED.ai_feedback,
                                    updated_at = NOW()
                            """), {
                                "id": submission_id,
                                "student_id": student_id,
                                "activity_id": activity_id,
                                "code": "",  # El código está en exercise_attempts_v2
                                "status": "submitted",
                                "submitted_at": datetime.utcnow(),
                                "auto_grade": final_grade_value,
                                "final_grade": final_grade_value,
                                "ai_feedback": audit_data.get('general_feedback', '')
                            })
                            
                            await db.commit()
                            logger.info(f"Full activity audit completed. Risk level: {risk_level}, AI dependency: {ai_dependency_ratio:.2f}, Final grade: {final_grade_value}")
                        except Exception as parse_err:
                            logger.error(f"Failed to parse audit JSON: {parse_err}")
                
            except Exception as audit_err:
                logger.error(f"Full audit failed: {audit_err}")
                # Don't fail the request, just log it.

        return SubmitSessionCodeResponse(**result)
    
    except ValueError as e:
        logger.error(f"ValueError in submit_code: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Validation failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error in submit_code: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit code: {str(e)}"
        )


@router.websocket("/ws/sessions/{session_id}/chat")
async def websocket_chat(
    websocket: WebSocket,
    session_id: str,
):
    """WebSocket para chat en tiempo real con el tutor socrático.

    Envía y recibe JSON con la forma:
    - Cliente → servidor: {"message": str, "topic": str | null, "cognitive_phase": str}
    - Servidor → cliente:
        - {"type": "chunk", "content": str}
        - {"type": "end", "content": str}
        - {"type": "error", "detail": str}

    Nota: Esta vía está pensada para UX (streaming). El almacenamiento
    completo de historial sigue haciéndose vía los endpoints HTTP.
    """
    await websocket.accept()
    agent = SocraticTutorAgent()
    conversation_history: List[dict] = []

    try:
        while True:
            data = await websocket.receive_json()
            message = (data.get("message") or "").strip()
            topic = data.get("topic")
            cognitive_phase = data.get("cognitive_phase", "exploration")

            if not message:
                await websocket.send_json({"type": "error", "detail": "Mensaje vacío"})
                continue

            conversation_history.append({"role": "user", "content": message})

            full_response = ""
            async for chunk in agent.respond_stream(
                student_message=message,
                session_id=session_id,
                conversation_history=conversation_history,
                cognitive_phase=cognitive_phase,
                topic=topic,
            ):
                full_response += chunk
                await websocket.send_json({"type": "chunk", "content": chunk})

            conversation_history.append({"role": "assistant", "content": full_response})
            await websocket.send_json({"type": "end", "content": full_response})

    except WebSocketDisconnect:
        return
    except Exception as exc:  # pragma: no cover - defensive
        await websocket.send_json({"type": "error", "detail": str(exc)})
        await websocket.close()


# ==================== GRADES ENDPOINTS ====================

class GradeResponse(BaseModel):
    """Student grade for an activity/course"""
    grade_id: str
    student_id: str
    activity_id: str
    course_id: Optional[str]
    grade: float
    max_grade: float = 10.0
    passed: bool
    teacher_feedback: Optional[str] = None
    submission_count: int
    last_submission_at: Optional[datetime] = None
    graded_at: Optional[datetime] = None
    graded_by: Optional[str] = None
    activity_title: str
    course_name: Optional[str] = None
    
    class Config:
        from_attributes = True


@router.get("/grades", response_model=List[GradeResponse])
async def get_my_grades(
    student_id: str,
    course_id: Optional[str] = None,
    passed_only: Optional[bool] = None
):
    """
    Obtener libreta de calificaciones del estudiante.
    
    Muestra todas las calificaciones por actividad.
    Filtros opcionales por curso y estado de aprobación.
    """
    from backend.src_v3.infrastructure.persistence.database import get_db_session
    from sqlalchemy import text
    
    async for db in get_db_session():
        try:
            # Build query with optional filters
            query = """
                SELECT 
                    s.submission_id as grade_id,
                    s.student_id,
                    s.activity_id,
                    a.course_id,
                    COALESCE(s.final_grade, s.auto_grade, 0) as grade,
                    10.0 as max_grade,
                    CASE WHEN COALESCE(s.final_grade, s.auto_grade, 0) >= 60 THEN true ELSE false END as passed,
                    s.teacher_feedback,
                    1 as submission_count,
                    s.submitted_at as last_submission_at,
                    s.graded_at,
                    s.graded_by,
                    a.title as activity_title,
                    COALESCE(c.name, 'Sin curso') as course_name
                FROM submissions s
                INNER JOIN activities a ON s.activity_id = a.activity_id
                LEFT JOIN courses c ON a.course_id = c.course_id
                LEFT JOIN subjects sub ON c.subject_code = sub.code
                WHERE s.student_id = :student_id
                  AND s.status IN ('submitted', 'graded', 'reviewed')
            """
            
            params = {"student_id": student_id}
            
            if course_id:
                query += " AND a.course_id = :course_id"
                params["course_id"] = course_id
            
            if passed_only:
                query += " AND COALESCE(s.final_grade, s.auto_grade, 0) >= 60"
            
            query += " ORDER BY s.submitted_at DESC"
            
            result = await db.execute(text(query), params)
            
            grades = []
            for row in result:
                grades.append({
                    "grade_id": row[0],
                    "student_id": row[1],
                    "activity_id": row[2],
                    "course_id": row[3],
                    "grade": float(row[4]) if row[4] else 0.0,
                    "max_grade": float(row[5]),
                    "passed": row[6],
                    "teacher_feedback": row[7],
                    "submission_count": row[8],
                    "last_submission_at": row[9],
                    "graded_at": row[10],
                    "graded_by": row[11],
                    "activity_title": row[12],
                    "course_name": row[13]
                })
            
            return grades
            
        except Exception as e:
            logger.error(f"Error fetching grades: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching grades: {str(e)}"
            )


@router.get("/grades/summary", status_code=status.HTTP_200_OK)
async def get_grades_summary(student_id: str):
    """
    Obtener resumen de calificaciones del estudiante.
    
    Incluye: promedio general, actividades completadas, pendientes, etc.
    """
    from backend.src_v3.infrastructure.persistence.database import get_db_session
    from sqlalchemy import text
    
    async for db in get_db_session():
        try:
            # Get aggregated statistics
            result = await db.execute(text("""
                SELECT 
                    COUNT(DISTINCT a.activity_id) as total_activities,
                    COUNT(DISTINCT CASE WHEN s.status IN ('graded', 'reviewed') THEN s.activity_id END) as graded_activities,
                    COUNT(DISTINCT CASE WHEN s.status = 'pending' OR s.status IS NULL THEN a.activity_id END) as pending_activities,
                    COUNT(DISTINCT CASE WHEN COALESCE(s.final_grade, s.auto_grade, 0) >= 60 THEN s.activity_id END) as passed_activities,
                    COUNT(DISTINCT CASE WHEN s.status IN ('graded', 'reviewed') AND COALESCE(s.final_grade, s.auto_grade, 0) < 60 THEN s.activity_id END) as failed_activities,
                    COALESCE(AVG(COALESCE(s.final_grade, s.auto_grade)), 0) as average_grade,
                    COALESCE(MAX(COALESCE(s.final_grade, s.auto_grade)), 0) as highest_grade,
                    COALESCE(MIN(NULLIF(COALESCE(s.final_grade, s.auto_grade), 0)), 0) as lowest_grade
                FROM activities a
                INNER JOIN sessions_v2 sv ON sv.activity_id = a.activity_id
                LEFT JOIN submissions s ON s.activity_id = a.activity_id AND s.student_id = :student_id
                WHERE sv.user_id = :student_id
            """), {"student_id": student_id})
            
            row = result.fetchone()
            
            if row:
                return {
                    "student_id": student_id,
                    "total_activities": row[0] or 0,
                    "graded_activities": row[1] or 0,
                    "pending_activities": row[2] or 0,
                    "passed_activities": row[3] or 0,
                    "failed_activities": row[4] or 0,
                    "average_grade": round(float(row[5]) if row[5] else 0.0, 2),
                    "highest_grade": round(float(row[6]) if row[6] else 0.0, 2),
                    "lowest_grade": round(float(row[7]) if row[7] else 0.0, 2)
                }
            
            return {
                "student_id": student_id,
                "total_activities": 0,
                "graded_activities": 0,
                "pending_activities": 0,
                "passed_activities": 0,
                "failed_activities": 0,
                "average_grade": 0.0,
                "highest_grade": 0.0,
                "lowest_grade": 0.0
            }
            
        except Exception as e:
            logger.error(f"Error fetching grades summary: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching grades summary: {str(e)}"
            )


@router.get("/grades/course/{course_id}", response_model=List[GradeResponse])
async def get_course_grades(course_id: str, student_id: str):
    """
    Obtener calificaciones del estudiante para un curso específico.
    
    Útil para ver el desempeño en una materia particular.
    """
    # Reutiliza la función get_my_grades con filtro de curso
    return await get_my_grades(student_id=student_id, course_id=course_id)


# ==================== STUDENT PANEL ====================

class ActivityHistoryItem(BaseModel):
    """Item de historial de actividades"""
    activity_id: str
    activity_title: str
    course_id: str
    course_name: str
    status: str  # not_started, in_progress, submitted, graded
    last_interaction: Optional[str]
    grade: Optional[float]
    passed: bool
    cognitive_phase: Optional[str]
    completion_percentage: float


@router.get("/activities/history", response_model=List[ActivityHistoryItem])
async def get_activities_history(student_id: str):
    """
    Obtener historial de actividades del estudiante.
    
    Incluye:
    - Todas las actividades de cursos en los que está inscrito
    - Estado actual (not_started, in_progress, submitted, graded)
    - Última interacción y fase cognitiva
    - Calificación y estado de aprobación
    - Porcentaje de completado
    
    Requiere autenticación de estudiante.
    """
    # TODO: Consultar enrollments del estudiante
    # TODO: JOIN con activities, submissions, tutor_sessions
    # TODO: Calcular completion_percentage por fase cognitiva
    # TODO: Ordenar por last_interaction DESC
    
    return [
        {
            "activity_id": "act_1",
            "activity_title": "Introducción a Python",
            "course_id": "course_1",
            "course_name": "Programación I",
            "status": "graded",
            "last_interaction": "2026-01-20T15:30:00Z",
            "grade": 8.5,
            "passed": True,
            "cognitive_phase": "reflection",
            "completion_percentage": 100.0
        },
        {
            "activity_id": "act_2",
            "activity_title": "Estructuras de Control",
            "course_id": "course_1",
            "course_name": "Programación I",
            "status": "in_progress",
            "last_interaction": "2026-01-25T10:00:00Z",
            "grade": None,
            "passed": False,
            "cognitive_phase": "implementation",
            "completion_percentage": 57.0
        }
    ]


class JoinCourseRequest(BaseModel):
    """Request para unirse a un curso/actividad con código"""
    access_code: str = Field(..., min_length=6, max_length=20)


class EnrollmentResponse(BaseModel):
    """Response de inscripción exitosa"""
    enrollment_id: str
    student_id: str
    course_id: str
    activity_id: Optional[str]
    enrolled_at: str
    message: str


@router.post("/enrollments/join", response_model=EnrollmentResponse, status_code=status.HTTP_201_CREATED)
async def join_with_access_code(student_id: str, request: JoinCourseRequest):
    """
    Unirse a un curso o actividad usando código de acceso.
    
    El código puede ser:
    - Código de curso (enrollment a nivel curso)
    - Código de actividad específica (enrollment directo a actividad)
    
    Valida:
    - Código válido y no expirado
    - Estudiante no está ya inscrito
    - Capacidad del curso no excedida
    
    Requiere autenticación de estudiante.
    """
    # TODO: Validar access_code en tabla access_codes
    # TODO: Verificar expiration_date
    # TODO: Verificar que estudiante no esté inscrito
    # TODO: Crear enrollment record
    # TODO: Enviar notificación de bienvenida
    
    import uuid
    from datetime import datetime
    
    return {
        "enrollment_id": str(uuid.uuid4()),
        "student_id": student_id,
        "course_id": "course_1",
        "activity_id": None,
        "enrolled_at": datetime.utcnow().isoformat(),
        "message": "Te has inscrito exitosamente al curso"
    }


# ==================== WORKSPACE & TUTOR (LangGraph) ====================

class WorkspaceResponse(BaseModel):
    """Response con contexto del workspace"""
    activity_id: str
    activity_title: str
    instructions: str
    expected_concepts: List[str]
    starter_code: str
    template_code: str
    tutor_context: str  # RAG context preview
    language: str
    difficulty: str
    estimated_time_minutes: int


@router.get("/activities/{activity_id}/workspace", response_model=WorkspaceResponse)
async def get_activity_workspace(activity_id: str, student_id: str):
    """
    Obtener workspace para trabajar en una actividad.
    
    Devuelve:
    - Instrucciones completas de la actividad
    - Código template/starter
    - Conceptos esperados
    - Preview del contexto RAG (material del curso)
    
    Este endpoint prepara todo lo necesario para que el estudiante
    comience a trabajar y para iniciar la sesión de tutoría.
    
    Requiere autenticación de estudiante inscrito en el curso.
    """
    # TODO: Consultar activity details
    # TODO: Verificar enrollment del estudiante
    # TODO: Obtener starter_code si existe
    # TODO: Cargar preview de RAG context desde ChromaDB
    
    return {
        "activity_id": activity_id,
        "activity_title": "Introducción a Funciones",
        "instructions": """## Misión

Implementa una función que calcule el factorial de un número.

### Requisitos:
- La función debe llamarse `factorial`
- Debe recibir un entero positivo `n`
- Debe retornar el factorial de `n`
- Usa recursión o iteración (tu elección)

### Ejemplo:
```python
factorial(5)  # Retorna 120
factorial(0)  # Retorna 1
```
""",
        "expected_concepts": [
            "funciones",
            "recursión",
            "iteración",
            "casos base",
            "validación de entrada"
        ],
        "starter_code": "def factorial(n):\n    # TODO: Implementa tu solución aquí\n    pass\n",
        "template_code": "def factorial(n):\n    # TODO: Implementa tu solución aquí\n    pass\n",
        "tutor_context": "Fragmentos del material del curso sobre funciones y recursión...",
        "language": "python",
        "difficulty": "medium",
        "estimated_time_minutes": 45
    }


class TutorChatRequest(BaseModel):
    """Request para chat con tutor (usando LangGraph)"""
    student_message: str = Field(..., min_length=1)
    current_code: Optional[str] = None
    error_message: Optional[str] = None


class TutorChatResponse(BaseModel):
    """Response del tutor Socrático"""
    tutor_response: str
    cognitive_phase: str
    frustration_level: float
    understanding_level: float
    hint_count: int
    rag_context_used: str


@router.post("/activities/{activity_id}/tutor", response_model=TutorChatResponse)
async def chat_with_tutor(
    activity_id: str,
    student_id: str,
    request: TutorChatRequest
):
    """
    Interactuar con el tutor Socrático (StudentTutorGraph).
    
    El tutor:
    - Guía mediante preguntas (no da respuestas directas)
    - Adapta su estilo según frustración/comprensión
    - Usa contexto RAG del material del curso
    - Rastrea la fase cognitiva N4 actual
    - Limita hints a 3 por fase
    
    Requiere sesión activa de tutoría.
    """
    # TODO: Verificar/crear session si no existe
    # TODO: Initialize StudentTutorGraph
    # TODO: Call graph.send_message(session_id, message, code, error)
    # TODO: Retornar respuesta Socrática
    
    return {
        "tutor_response": "Interesante enfoque. ¿Por qué elegiste usar recursión en lugar de iteración? ¿Qué ventajas ves en tu solución?",
        "cognitive_phase": "implementation",
        "frustration_level": 0.3,
        "understanding_level": 0.7,
        "hint_count": 1,
        "rag_context_used": "Fragmento del curso: La recursión es elegante pero consume más memoria..."
    }


# ==================== STUDENT DASHBOARD & ACTIVITY MANAGEMENT ====================

class StudentActivityListItem(BaseModel):
    """Activity item for student dashboard"""
    activity_id: str
    title: str
    course_id: Optional[str] = None
    course_name: Optional[str] = "Curso General"
    difficulty: Optional[str] = None
    estimated_duration_minutes: Optional[int] = None
    status: str  # "not_started", "in_progress", "submitted", "graded"
    submission_id: Optional[str] = None
    current_grade: Optional[float]
    submitted_at: Optional[datetime]
    instructions: Optional[str]


@router.get("/activities", response_model=List[StudentActivityListItem])
async def list_student_activities(student_id: str):
    """
    List all activities available to the student from enrolled courses.
    
    For each activity, includes submission status:
    - not_started: No submission yet
    - in_progress: Has a draft submission
    - submitted: Submitted but not graded
    - graded: Teacher has graded
    
    Requires student authentication.
    """
    from backend.src_v3.infrastructure.persistence.database import get_db_session
    from sqlalchemy import text
    
    async for db in get_db_session():
        try:
            # Query activities from courses where student is enrolled, with submission status
            result = await db.execute(text("""
                SELECT DISTINCT
                    a.activity_id,
                    a.title,
                    COALESCE(a.course_id, 'general') as course_id,
                    'Curso General' as course_name,
                    NULL as difficulty,
                    60 as estimated_duration_minutes,
                    a.instructions,
                    COALESCE(s.status, 'pending') as status,
                    s.submission_id,
                    s.final_grade,
                    s.submitted_at,
                    a.created_at
                FROM activities a
                INNER JOIN sessions_v2 sv ON sv.activity_id = a.activity_id
                LEFT JOIN submissions s ON s.activity_id = a.activity_id AND s.student_id = :student_id
                WHERE sv.user_id = :student_id
                ORDER BY a.created_at DESC
            """), {"student_id": student_id})
            
            activities = []
            for row in result:
                # Map submission status to student-friendly status
                submission_status = row[7]
                if submission_status == 'pending':
                    activity_status = 'not_started'
                elif submission_status == 'submitted':
                    activity_status = 'submitted'
                elif submission_status == 'graded':
                    activity_status = 'graded'
                else:
                    activity_status = 'in_progress'
                
                activities.append({
                    "activity_id": row[0],
                    "title": row[1],
                    "course_id": row[2],
                    "course_name": row[3],
                    "difficulty": row[4],
                    "estimated_duration_minutes": row[5],
                    "instructions": row[6],
                    "status": activity_status,
                    "submission_id": row[8],
                    "current_grade": float(row[9]) if row[9] else None,
                    "submitted_at": row[10]
                })
            
            return activities
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching activities: {str(e)}"
            )


class ActivityDetailResponse(BaseModel):
    """Complete activity details for student workspace"""
    activity_id: str
    title: str
    instructions: str
    difficulty: Optional[str] = None
    estimated_duration_minutes: Optional[int] = 60
    course_id: Optional[str] = "general"
    course_name: Optional[str] = "Curso General"
    starter_code: Optional[str] = None
    language: str = "python"
    # Current submission data (if exists)
    current_code: Optional[str] = None
    submission_status: str = "pending"
    last_saved_at: Optional[datetime] = None


@router.get("/activities/{activity_id}", response_model=ActivityDetailResponse)
async def get_activity_detail(activity_id: str, student_id: str):
    """
    Get complete activity details including any existing submission/draft.
    
    Used to load the 3-column workspace:
    - Returns activity instructions (for left panel)
    - Returns starter code or previously saved code (for editor)
    - Returns submission status
    
    Requires student authentication.
    """
    from backend.src_v3.infrastructure.persistence.database import get_db_session
    from sqlalchemy import text
    
    async for db in get_db_session():
        try:
            # Get activity details
            result = await db.execute(text("""
                SELECT 
                    a.activity_id,
                    a.title,
                    COALESCE(a.instructions, 'Completa el ejercicio siguiendo las instrucciones.') as instructions,
                    NULL as difficulty,
                    60 as estimated_duration_minutes,
                    COALESCE(a.course_id, 'general') as course_id,
                    'Curso General' as course_name,
                    s.code_snapshot,
                    COALESCE(s.status, 'pending') as status,
                    s.updated_at
                FROM activities a
                LEFT JOIN submissions s ON s.activity_id = a.activity_id AND s.student_id = :student_id
                WHERE a.activity_id = :activity_id
                LIMIT 1
            """), {"activity_id": activity_id, "student_id": student_id})
            
            row = result.fetchone()
            
            if not row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Activity not found"
                )
            
            # Default starter code if no submission exists
            starter_code = "# Escribe tu código aquí\n\ndef resolver():\n    pass\n"
            current_code = row[7] if row[7] else starter_code
            
            return {
                "activity_id": row[0],
                "title": row[1],
                "instructions": row[2] or "Completa el ejercicio siguiendo las instrucciones del profesor.",
                "difficulty": row[3],
                "estimated_duration_minutes": row[4],
                "course_id": row[5],
                "course_name": row[6],
                "starter_code": starter_code,
                "language": "python",
                "current_code": current_code,
                "submission_status": row[8],
                "last_saved_at": row[9]
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching activity: {str(e)}"
            )


# ==================== EXERCISES ENDPOINTS ====================

class ExerciseResponse(BaseModel):
    """Individual exercise for an activity"""
    exercise_id: str
    title: str
    difficulty: str
    mission_markdown: str
    starter_code: Optional[str] = ""
    language: str = "python"
    order_index: int
    total_exercises: int


@router.get("/activities/{activity_id}/exercises", response_model=List[ExerciseResponse])
async def get_activity_exercises(activity_id: str, student_id: str):
    """
    Get all exercises for an activity.
    Returns exercises ordered by unit_number.
    """
    from backend.src_v3.infrastructure.persistence.database import get_db_session
    from sqlalchemy import text
    
    async for db in get_db_session():
        try:
            result = await db.execute(text("""
                SELECT 
                    exercise_id,
                    title,
                    difficulty::text,
                    mission_markdown,
                    starter_code,
                    language::text,
                    unit_number,
                    COUNT(*) OVER() as total_count
                FROM exercises_v2
                WHERE activity_id = :activity_id
                  AND deleted_at IS NULL
                ORDER BY unit_number
            """), {"activity_id": activity_id})
            
            exercises = []
            for row in result:
                exercises.append({
                    "exercise_id": row[0],
                    "title": row[1],
                    "difficulty": row[2],
                    "mission_markdown": row[3],
                    "starter_code": row[4] or "# Escribe tu código aquí\n",
                    "language": row[5] or "python",
                    "order_index": row[6],
                    "total_exercises": row[7]
                })
            
            return exercises
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching exercises: {str(e)}"
            )


class SubmitCodeRequest(BaseModel):
    """Request to save or submit code"""
    code: str = Field(..., description="Student code")
    is_final_submission: bool = Field(False, description="True for final submit, False for draft save")
    exercise_id: Optional[str] = Field(None, description="Exercise ID if submitting individual exercise")


class SubmitCodeResponse(BaseModel):
    """Response after code submission"""
    submission_id: str
    status: str
    message: str
    grade: Optional[float] = None
    ai_feedback: Optional[str] = None
    next_exercise_id: Optional[str] = None
    is_activity_complete: bool = False
    exercises_details: Optional[List[dict]] = Field(default_factory=list, description="Detailed feedback per exercise")


@router.post("/activities/{activity_id}/submit", response_model=SubmitCodeResponse)
async def submit_activity_code(activity_id: str, student_id: str, request: SubmitCodeRequest):
    """
    Submit entire activity for final evaluation.
    
    For activities with exercises:
    - Retrieves all exercise attempts from student
    - Uses AI to evaluate overall performance
    - Generates final grade and comprehensive feedback
    - Calculates risk analysis based on patterns
    
    For activities without exercises:
    - Evaluates submitted code directly
    
    Stores submission in database for teacher review with full traceability.
    """
    from backend.src_v3.infrastructure.persistence.database import get_db_session
    from sqlalchemy import text
    import uuid
    from datetime import datetime
    
    async for db in get_db_session():
        try:
            # Get activity details
            activity_result = await db.execute(text("""
                SELECT title, instructions FROM activities
                WHERE activity_id = :activity_id
            """), {"activity_id": activity_id})
            activity_row = activity_result.fetchone()
            
            if not activity_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Activity not found"
                )
            
            activity_title = activity_row[0]
            activity_instructions = activity_row[1]
            
            # Get ALL exercises for this activity with their latest attempt (if any)
            exercises_result = await db.execute(text("""
                WITH latest_attempts AS (
                    SELECT 
                        exercise_id,
                        code_submitted,
                        passed,
                        test_results,
                        submitted_at,
                        attempt_id,
                        ROW_NUMBER() OVER (PARTITION BY exercise_id ORDER BY submitted_at DESC) as rn
                    FROM exercise_attempts_v2
                    WHERE user_id = :student_id
                )
                SELECT 
                    e.exercise_id,
                    e.title,
                    e.difficulty::text,
                    e.unit_number,
                    e.mission_markdown,
                    COALESCE(la.code_submitted, '') as code_submitted,
                    COALESCE(la.passed, false) as passed,
                    la.test_results,
                    la.submitted_at,
                    la.attempt_id
                FROM exercises_v2 e
                LEFT JOIN latest_attempts la ON e.exercise_id = la.exercise_id AND la.rn = 1
                WHERE e.activity_id = :activity_id 
                  AND e.deleted_at IS NULL
                ORDER BY e.unit_number
            """), {"activity_id": activity_id, "student_id": student_id})
            
            all_exercises = exercises_result.fetchall()
            
            logger.info(f"Found {len(all_exercises)} total exercises for activity {activity_id}")
            
            logger.info(f"Found {len(all_exercises)} total exercises for activity {activity_id}")
            
            # Build evaluation context with individual feedback
            exercises_summary = []
            exercises_details = []  # For frontend display
            completed_count = 0
            
            for row in all_exercises:
                test_results = row[7] if row[7] else {}
                grade = test_results.get('grade', 0) if isinstance(test_results, dict) else 0
                feedback = test_results.get('feedback', 'No intentado aún') if isinstance(test_results, dict) else 'No intentado aún'
                is_passed = row[6]
                has_attempt = row[9] is not None  # Check if attempt_id exists
                
                # If no attempt, feedback should indicate that
                if not has_attempt:
                    grade = 0
                    feedback = "❌ Ejercicio no intentado. Debes completar este ejercicio."
                    is_passed = False
                else:
                    completed_count += 1
                
                logger.info(f"Processing exercise: {row[1]}, grade: {grade}, passed: {is_passed}, has_attempt: {has_attempt}")
                
                exercises_summary.append({
                    "title": row[1],
                    "difficulty": row[2],
                    "code": row[5] if has_attempt else "",
                    "passed": is_passed
                })
                
                exercises_details.append({
                    "title": row[1],
                    "difficulty": row[2],
                    "passed": is_passed,
                    "grade": grade,
                    "feedback": feedback
                })
            
            logger.info(f"Built exercises_details with {len(exercises_details)} exercises ({completed_count} completed)")
            
            # AI-powered final evaluation
            final_grade = None
            ai_feedback = None
            risk_analysis = "BAJO"
            
            if request.is_final_submission:
                try:
                    from langchain_mistralai import ChatMistralAI
                    import os
                    import json
                    
                    mistral_api_key = os.getenv("MISTRAL_API_KEY")
                    if mistral_api_key and exercises_summary:
                        llm = ChatMistralAI(
                            model="mistral-small-latest",
                            api_key=mistral_api_key,
                            temperature=0.3
                        )
                        
                        # Build comprehensive evaluation prompt
                        exercises_text = "\\n\\n".join([
                            f"**{i+1}. {ex['title']}** (Dificultad: {ex['difficulty']})\\n"
                            f"Estado: {'✓ Aprobado' if ex['passed'] else '✗ No aprobado'}\\n"
                            f"Código:\\n```python\\n{ex['code'][:300]}...\\n```"
                            for i, ex in enumerate(exercises_summary[:10])  # Limit to avoid token limits
                        ])
                        
                        evaluation_prompt = f"""Eres un profesor evaluando el desempeño completo de un estudiante en una actividad.

ACTIVIDAD: {activity_title}
TOTAL DE EJERCICIOS: {len(exercises_summary)}

EJERCICIOS COMPLETADOS:
{exercises_text}

ANÁLISIS REQUERIDO:
1. **NOTA FINAL**: Calcula una nota del 0 al 100 basada en:
   - Cantidad de ejercicios completados correctamente
   - Calidad del código (claridad, eficiencia, buenas prácticas)
   - Progresión en dificultad (FACIL → INTERMEDIO → DIFICIL)

2. **FEEDBACK INTEGRAL**: Proporciona un análisis de 4-6 líneas que incluya:
   - Fortalezas principales del estudiante
   - Áreas específicas de mejora
   - Recomendaciones concretas para el siguiente nivel

3. **ANÁLISIS DE RIESGO**: Evalúa el riesgo académico:
   - BAJO: >80% ejercicios correctos, código de calidad
   - MEDIO: 60-80% correctos, algunos problemas de comprensión
   - ALTO: <60% correctos, múltiples errores conceptuales

Responde ÚNICAMENTE con JSON válido:
{{
  "final_grade": 85,
  "feedback": "Excelente dominio de bucles y estructuras de control. El código es limpio y eficiente. Se recomienda practicar más con casos edge y validación de entrada. Muy buen progreso en ejercicios de dificultad intermedia.",
  "risk_level": "BAJO",
  "strengths": ["Bucles anidados", "List comprehensions", "Sintaxis clara"],
  "improvements": ["Validación de entrada", "Manejo de errores"]
}}"""
                        
                        response = llm.invoke(evaluation_prompt)
                        
                        try:
                            eval_data = json.loads(response.content)
                            final_grade = eval_data.get("final_grade", 75.0)
                            ai_feedback = eval_data.get("feedback", "Evaluación completada.")
                            risk_analysis = eval_data.get("risk_level", "MEDIO")
                        except json.JSONDecodeError:
                            logger.warning(f"Could not parse final evaluation: {response.content}")
                            # Calculate basic grade from passed exercises
                            passed_count = sum(1 for ex in exercises_summary if ex.get('passed'))
                            final_grade = (passed_count / len(exercises_summary) * 100) if exercises_summary else 70.0
                            ai_feedback = f"Completaste {passed_count} de {len(exercises_summary)} ejercicios correctamente."
                            risk_analysis = "BAJO" if final_grade >= 80 else ("MEDIO" if final_grade >= 60 else "ALTO")
                    else:
                        # Fallback calculation
                        if exercises_summary:
                            passed_count = sum(1 for ex in exercises_summary if ex.get('passed'))
                            final_grade = (passed_count / len(exercises_summary) * 100)
                            ai_feedback = f"Actividad completada. {passed_count}/{len(exercises_summary)} ejercicios correctos."
                            risk_analysis = "BAJO" if final_grade >= 80 else ("MEDIO" if final_grade >= 60 else "ALTO")
                        else:
                            final_grade = 75.0
                            ai_feedback = "Actividad enviada para revisión."
                            risk_analysis = "MEDIO"
                        
                except Exception as e:
                    logger.error(f"Error in final AI evaluation: {str(e)}")
                    final_grade = 70.0
                    ai_feedback = "Actividad completada. Evaluación manual pendiente."
                    risk_analysis = "MEDIO"
            
            # Check if submission already exists
            result = await db.execute(text("""
                SELECT submission_id, status FROM submissions
                WHERE activity_id = :activity_id AND student_id = :student_id
            """), {"activity_id": activity_id, "student_id": student_id})
            
            existing = result.fetchone()
            
            if existing:
                # Update existing submission
                submission_id = existing[0]
                new_status = 'submitted' if request.is_final_submission else existing[1]
                
                await db.execute(text("""
                    UPDATE submissions
                    SET code_snapshot = :code,
                        status = :status,
                        submitted_at = :submitted_at,
                        auto_grade = :auto_grade,
                        final_grade = :final_grade,
                        ai_feedback = :ai_feedback,
                        updated_at = NOW()
                    WHERE submission_id = :submission_id
                """), {
                    "code": request.code or "",
                    "status": new_status,
                    "submitted_at": datetime.utcnow() if request.is_final_submission else None,
                    "auto_grade": final_grade,
                    "final_grade": final_grade,
                    "ai_feedback": ai_feedback,
                    "submission_id": submission_id
                })
                
                message = f"¡Actividad enviada! Nota final: {final_grade:.0f}/100" if request.is_final_submission else "Progreso guardado"
            else:
                # Create new submission
                submission_id = str(uuid.uuid4())
                new_status = 'submitted' if request.is_final_submission else 'pending'
                
                await db.execute(text("""
                    INSERT INTO submissions (
                        submission_id, student_id, activity_id, code_snapshot,
                        status, submitted_at, auto_grade, final_grade, ai_feedback,
                        created_at, updated_at
                    )
                    VALUES (:id, :student_id, :activity_id, :code, :status, :submitted_at, 
                            :auto_grade, :final_grade, :ai_feedback, NOW(), NOW())
                """), {
                    "id": submission_id,
                    "student_id": student_id,
                    "activity_id": activity_id,
                    "code": request.code or "",
                    "status": new_status,
                    "submitted_at": datetime.utcnow() if request.is_final_submission else None,
                    "auto_grade": final_grade,
                    "final_grade": final_grade,
                    "ai_feedback": ai_feedback
                })
                
                message = f"¡Actividad enviada! Nota final: {final_grade:.0f}/100" if request.is_final_submission else "Código guardado como borrador"
            
            # Store risk analysis metadata in test_results JSON field
            if request.is_final_submission and exercises_summary:
                test_results_json = json.dumps({
                    "risk_level": risk_analysis,
                    "total_exercises": len(exercises_summary),
                    "passed_exercises": sum(1 for ex in exercises_summary if ex.get('passed')),
                    "completion_rate": (sum(1 for ex in exercises_summary if ex.get('passed')) / len(exercises_summary) * 100) if exercises_summary else 0
                })
                
                await db.execute(text("""
                    UPDATE submissions
                    SET test_results = CAST(:test_results AS jsonb)
                    WHERE submission_id = :submission_id
                """), {
                    "test_results": test_results_json,
                    "submission_id": submission_id
                })
            
            await db.commit()
            
            logger.info(f"Returning response with exercises_details length: {len(exercises_details)}")
            logger.info(f"exercises_details content: {exercises_details}")
            
            return {
                "submission_id": submission_id,
                "status": new_status,
                "message": message,
                "grade": final_grade,
                "ai_feedback": ai_feedback,
                "next_exercise_id": None,
                "is_activity_complete": True,
                "exercises_details": exercises_details if request.is_final_submission else []
            }
            
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error submitting code: {str(e)}"
            )


@router.get("/activities/{activity_id}/attempt")
async def get_activity_attempt(
    activity_id: str,
    student_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get the previous attempt for this activity by the student.
    Returns attempt details including status and final_grade.
    """
    try:
        result = await db.execute(text("""
            SELECT status, final_grade, submitted_at, ai_feedback
            FROM submissions
            WHERE student_id = :student_id AND activity_id = :activity_id
              AND status IN ('submitted', 'graded', 'reviewed') AND final_grade IS NOT NULL
            ORDER BY submitted_at DESC
            LIMIT 1
        """), {"student_id": student_id, "activity_id": activity_id})
        
        attempt = result.fetchone()
        
        if not attempt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No attempt found"
            )
        
        return {
            "status": attempt.status,
            "final_grade": attempt.final_grade,
            "submitted_at": attempt.submitted_at.isoformat() if attempt.submitted_at else None,
            "ai_feedback": attempt.ai_feedback
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting activity attempt: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting attempt: {str(e)}"
        )


@router.post("/activities/{activity_id}/exercises/{exercise_id}/submit", response_model=SubmitCodeResponse)
async def submit_exercise_code(activity_id: str, exercise_id: str, student_id: str, request: SubmitCodeRequest):
    """
    Submit code for an individual exercise.
    Returns the next exercise_id if there are more exercises.
    """
    from backend.src_v3.infrastructure.persistence.database import get_db_session
    from sqlalchemy import text
    import uuid
    from datetime import datetime
    
    async for db in get_db_session():
        try:
            # Get active session for this student and activity
            session_result = await db.execute(text("""
                SELECT session_id, user_id
                FROM sessions_v2
                WHERE user_id = :student_id AND activity_id = :activity_id
                  AND status != 'completed'
                ORDER BY start_time DESC
                LIMIT 1
            """), {"student_id": student_id, "activity_id": activity_id})
            session_row = session_result.fetchone()
            
            if not session_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No active session found for student {student_id} in activity {activity_id}"
                )
            
            session_id = session_row[0]
            user_id_from_session = session_row[1]
            
            # Get exercise details for AI evaluation
            exercise_result = await db.execute(text("""
                SELECT title, mission_markdown, difficulty
                FROM exercises_v2
                WHERE exercise_id = :exercise_id AND deleted_at IS NULL
            """), {"exercise_id": exercise_id})
            exercise_row = exercise_result.fetchone()
            
            if not exercise_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Exercise not found"
                )
            
            exercise_title = exercise_row[0]
            exercise_mission = exercise_row[1]
            exercise_difficulty = exercise_row[2]
            
            # AI Evaluation using Mistral
            ai_grade = None
            ai_feedback = None
            is_correct = None
            
            try:
                from langchain_mistralai import ChatMistralAI
                import os
                
                mistral_api_key = os.getenv("MISTRAL_API_KEY")
                if mistral_api_key:
                    llm = ChatMistralAI(
                        model="mistral-small-latest",
                        api_key=mistral_api_key,
                        temperature=0.3
                    )
                    
                    evaluation_prompt = f"""Eres un profesor evaluando código Python de un estudiante.

EJERCICIO: {exercise_title}
DIFICULTAD: {exercise_difficulty}

CONSIGNA:
{exercise_mission}

CÓDIGO DEL ESTUDIANTE:
```python
{request.code}
```

Evalúa el código ESTRICTAMENTE y proporciona:
1. NOTA (0-100): 
   - 90-100: Código excelente, limpio, eficiente, maneja casos edge
   - 70-89: Código correcto pero con áreas de mejora
   - 50-69: Código funcional pero con errores menores o ineficiencias
   - 30-49: Código incompleto o con errores significativos
   - 0-29: Código vacío, solo comentarios/TODOs, o no cumple la consigna

2. CORRECTO (true/false): true SOLO si el código cumple TODOS los requisitos y funciona correctamente

3. FEEDBACK (2-4 líneas): EXPLICA ESPECÍFICAMENTE:
   - ¿Por qué esa nota? (menciona qué hizo bien o mal)
   - Si tiene errores, ¿cuáles?
   - ¿Qué debe mejorar para obtener mejor nota?
   
EJEMPLOS DE BUEN FEEDBACK:
- "✅ 85/100: Implementación correcta del bucle for. Falta manejo de listas vacías (-10) y nombres de variables poco descriptivos (-5)."
- "❌ 45/100: El código tiene error de sintaxis en línea 3 (falta ':' en el for). La lógica es correcta pero no ejecuta."
- "❌ 20/100: Solo tiene comentarios y 'pass'. No hay implementación real del ejercicio."

Respuesta OBLIGATORIA en formato JSON:
{{
  "grade": 85,
  "is_correct": true,
  "feedback": "✅ 85/100: Implementación correcta. Falta validación de entrada (-10) y documentación (-5)."
}}"""
                    
                    response = llm.invoke(evaluation_prompt)
                    
                    # Parse JSON response (handle markdown code blocks)
                    try:
                        response_text = response.content.strip()
                        
                        # Remove markdown code blocks if present
                        if response_text.startswith('```'):
                            # Remove ```json or ``` at start
                            response_text = response_text.split('\n', 1)[1] if '\n' in response_text else response_text[3:]
                            # Remove ``` at end
                            if response_text.endswith('```'):
                                response_text = response_text[:-3]
                            response_text = response_text.strip()
                        
                        eval_data = json.loads(response_text)
                        ai_grade = eval_data.get("grade")
                        is_correct = eval_data.get("is_correct", False)
                        ai_feedback = eval_data.get("feedback", "Evaluación completada.")
                        
                        logger.info(f"Mistral evaluation: grade={ai_grade}, is_correct={is_correct}")
                        
                    except json.JSONDecodeError as e:
                        logger.warning(f"Could not parse AI evaluation response: {response.content}")
                        logger.warning(f"JSON decode error: {str(e)}")
                        # Fallback: evaluación básica
                        code_lines = [line.strip() for line in request.code.split('\n') if line.strip() and not line.strip().startswith('#')]
                        has_real_code = any(line and line not in ['pass', 'TODO', '...'] for line in code_lines)
                        
                        if has_real_code and len(code_lines) >= 2:
                            ai_grade = 55.0
                            is_correct = False
                            ai_feedback = f"⚠️ 55/100: Se detectó código pero no se pudo evaluar automáticamente. Tiene {len(code_lines)} líneas de código. Necesita revisión manual del profesor para confirmar funcionamiento."
                        elif len(code_lines) == 1:
                            ai_grade = 30.0
                            is_correct = False
                            ai_feedback = "❌ 30/100: Código muy breve (1 línea). Implementación incompleta. Desarrolla la solución completa según la consigna."
                        else:
                            ai_grade = 10.0
                            is_correct = False
                            ai_feedback = "❌ 10/100: Código vacío o solo comentarios/TODOs. No hay implementación real. Debes escribir código que resuelva el ejercicio."
                else:
                    logger.warning("MISTRAL_API_KEY not found, using basic evaluation")
                    # Evaluación básica sin IA
                    code_lines = [line.strip() for line in request.code.split('\n') if line.strip() and not line.strip().startswith('#')]
                    has_real_code = any(line and line not in ['pass', 'TODO', '...'] for line in code_lines)
                    
                    if has_real_code and len(code_lines) >= 2:
                        ai_grade = 55.0
                        is_correct = False
                        ai_feedback = f"⚠️ 55/100: Código enviado ({len(code_lines)} líneas detectadas). Sin evaluación automática disponible, se requiere revisión manual del profesor."
                    elif len(code_lines) == 1:
                        ai_grade = 30.0
                        is_correct = False
                        ai_feedback = "❌ 30/100: Solo 1 línea de código detectada. Solución incompleta. Revisa la consigna y desarrolla la implementación completa."
                    else:
                        ai_grade = 10.0
                        is_correct = False
                        ai_feedback = "❌ 10/100: Código vacío, solo comentarios o TODOs. No se detectó implementación real. Lee la consigna y escribe código que resuelva el problema."
                    
            except Exception as e:
                logger.error(f"Error in AI evaluation: {str(e)}")
                # Evaluación básica en caso de error
                code_lines = [line.strip() for line in request.code.split('\n') if line.strip() and not line.strip().startswith('#')]
                has_real_code = any(line and line not in ['pass', 'TODO', '...'] for line in code_lines)
                
                if has_real_code and len(code_lines) >= 2:
                    ai_grade = 50.0
                    is_correct = False
                    ai_feedback = "Error en evaluación automática. Requiere revisión manual."
                else:
                    ai_grade = 10.0
                    is_correct = False
                    ai_feedback = "Código vacío o incompleto."
            
            # Save exercise attempt with AI evaluation
            attempt_id = str(uuid.uuid4())
            
            # Build INSERT - usar session_id como vínculo principal, user_id puede ser NULL
            insert_query = text("""
                INSERT INTO exercise_attempts_v2 (
                    attempt_id, session_id, user_id, exercise_id, code_submitted,
                    passed, grade, ai_feedback, execution_output, submitted_at
                )
                VALUES (:attempt_id, :session_id, NULL, :exercise_id, :code, :passed, :grade, :ai_feedback, CAST(:execution_output AS jsonb), NOW())
            """)
            
            test_results_data = json.dumps({
                "grade": ai_grade,
                "feedback": ai_feedback,
                "evaluated_at": datetime.utcnow().isoformat()
            })
            
            await db.execute(insert_query, {
                "attempt_id": attempt_id,
                "session_id": session_id,
                "exercise_id": exercise_id,
                "code": request.code,
                "passed": is_correct,
                "grade": int(ai_grade) if ai_grade else None,
                "ai_feedback": ai_feedback,
                "execution_output": test_results_data
            })
            
            # Get next exercise
            result = await db.execute(text("""
                SELECT 
                    e2.exercise_id,
                    e2.unit_number,
                    COUNT(*) OVER() as total_exercises,
                    e1.unit_number as current_unit
                FROM exercises_v2 e1
                LEFT JOIN exercises_v2 e2 ON e2.activity_id = e1.activity_id 
                    AND e2.unit_number > e1.unit_number 
                    AND e2.deleted_at IS NULL
                WHERE e1.exercise_id = :exercise_id
                  AND e1.deleted_at IS NULL
                ORDER BY e2.unit_number
                LIMIT 1
            """), {"exercise_id": exercise_id})
            
            row = result.fetchone()
            next_exercise_id = row[0] if row and row[0] else None
            is_complete = next_exercise_id is None
            
            await db.commit()
            
            return {
                "submission_id": attempt_id,
                "status": "submitted",
                "message": "¡Ejercicio completado!" if not is_complete else "¡Actividad completada!",
                "grade": ai_grade,
                "ai_feedback": ai_feedback,
                "next_exercise_id": next_exercise_id,
                "is_activity_complete": is_complete
            }
            
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error submitting exercise: {str(e)}"
            )


# ==================== TUTOR IA WITH RAG ====================

class ChatWithTutorRequest(BaseModel):
    """Request for AI tutor chat with RAG context"""
    message: str = Field(..., min_length=1, description="Student question")
    current_code: Optional[str] = Field(None, description="Current code in editor")
    error_context: Optional[str] = Field(None, description="Error message if any")


class ChatWithTutorResponse(BaseModel):
    """Response from AI tutor with RAG-enhanced context"""
    response: str
    rag_context_used: bool
    context_snippets: List[str]
    cognitive_phase: str
    hint_level: int


@router.post("/activities/{activity_id}/chat", response_model=ChatWithTutorResponse)
async def chat_with_ai_tutor(activity_id: str, student_id: str, request: ChatWithTutorRequest):
    """
    Chat with AI tutor using RAG for contextual help.
    
    Process:
    1. Get activity's course_id
    2. Query ChromaDB/RAG for relevant course materials based on student question
    3. Build system prompt with: activity instructions + RAG context + current code
    4. Send to Mistral for Socratic-style response
    5. Return helpful guidance without giving direct answers
    
    Requires active session.
    """
    from backend.src_v3.infrastructure.persistence.database import get_db_session
    from sqlalchemy import text
    from backend.src_v3.infrastructure.ai.rag.chroma_store import ChromaVectorStore
    from langchain_mistralai import ChatMistralAI
    import os
    
    async for db in get_db_session():
        try:
            # Get activity and course info
            result = await db.execute(text("""
                SELECT a.course_id, a.title, a.instructions
                FROM activities a
                WHERE a.activity_id = :activity_id
            """), {"activity_id": activity_id})
            
            row = result.fetchone()
            
            if not row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Activity not found"
                )
            
            course_id = row[0]
            activity_title = row[1]
            activity_instructions = row[2]
            
            # Query RAG/ChromaDB for relevant course materials
            rag_context = []
            rag_context_used = False
            
            try:
                vector_store = ChromaVectorStore(persist_directory="./chroma_data")
                collection_name = f"activity_{activity_id}"
                
                # Try to query RAG context
                results = vector_store.query(
                    query_text=request.message,
                    collection_name=collection_name,
                    n_results=3
                )
                
                if results:
                    rag_context = [doc.get("content", "") for doc in results]
                    rag_context_used = True
            except Exception as e:
                logger.warning(f"RAG query failed, using fallback: {e}")
                # Fallback to generic context
                rag_context = [
                    "Los bucles permiten repetir código múltiples veces.",
                    "El bucle 'for' se usa cuando conoces el número de iteraciones.",
                    "El bucle 'while' se usa con una condición que puede cambiar."
                ]
            
            # Build system prompt
            system_prompt = f"""Eres un tutor Socrático experto en programación. 

CONTEXTO DEL CURSO:
{chr(10).join(f'- {ctx}' for ctx in rag_context) if rag_context else 'No hay contexto específico disponible.'}

ACTIVIDAD ACTUAL: {activity_title}
INSTRUCCIONES: {activity_instructions}

CÓDIGO ACTUAL DEL ESTUDIANTE:
```python
{request.current_code or 'Sin código aún'}
```

ESTILO DE TUTORÍA:
- Guía mediante preguntas, NO des la respuesta directa
- Ayuda a razonar paso a paso
- Usa el contexto del curso para explicar conceptos
- Si hay un error, ayuda a identificar la causa sin resolverlo
- Sé paciente y motivador

PREGUNTA DEL ESTUDIANTE: {request.message}
"""
            
            # Call Mistral API
            tutor_response = "Excelente pregunta. Antes de continuar, ¿podrías explicarme qué crees que hace cada línea de tu código? Esto me ayudará a entender tu razonamiento."
            
            try:
                mistral_api_key = os.getenv("MISTRAL_API_KEY")
                if mistral_api_key:
                    llm = ChatMistralAI(
                        model="mistral-small-latest",
                        api_key=mistral_api_key,
                        temperature=0.7
                    )
                    
                    response = llm.invoke(system_prompt)
                    tutor_response = response.content
            except Exception as e:
                logger.warning(f"Mistral API call failed, using fallback: {e}")
            
            return {
                "response": tutor_response,
                "rag_context_used": rag_context_used,
                "context_snippets": rag_context,
                "cognitive_phase": "implementation",
                "hint_level": 1
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error in tutor chat: {str(e)}"
            )


# ==================== LMS HIERARCHY ENDPOINTS ====================

@router.get("/courses", response_model=List[CourseWithModules])
@cached(ttl=120, key_prefix="student_courses")  # Cache for 2 minutes
async def list_student_courses(
    request: Request,
    student_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    List all courses enrolled by the student, grouped by modules.
    
    Returns courses with nested modules and activities.
    Uses Enrollment table to show only modules where student is enrolled.
    """
    try:
        # Get active enrollments for student (grouped by course)
        enrollments_query = await db.execute(
            select(EnrollmentModel).where(
                EnrollmentModel.user_id == student_id,
                EnrollmentModel.status == EnrollmentStatus.ACTIVE
            )
        )
        enrollments = enrollments_query.scalars().all()
        
        if not enrollments:
            return []
        
        logger.info(f"📚 Found {len(enrollments)} enrollments for student {student_id}")
        
        # Group enrollments by course
        courses_dict = {}
        for enrollment in enrollments:
            if enrollment.course_id not in courses_dict:
                courses_dict[enrollment.course_id] = {
                    'enrollment': enrollment,
                    'module_ids': []
                }
            # Collect module_ids for this course
            if enrollment.module_id:
                courses_dict[enrollment.course_id]['module_ids'].append(enrollment.module_id)
                logger.info(f"   📁 Enrollment has module_id: {enrollment.module_id}")
        
        logger.info(f"📊 Grouped into {len(courses_dict)} courses")
        for course_id, data in courses_dict.items():
            logger.info(f"   Course {course_id}: {len(data['module_ids'])} modules")
        
        courses_with_modules = []
        
        for course_id, data in courses_dict.items():
            # Query course directly with SQL (avoid model mismatch)
            course_query = await db.execute(
                text("""
                    SELECT course_id, subject_code, year, semester
                    FROM courses
                    WHERE course_id = :course_id
                """),
                {"course_id": course_id}
            )
            course_row = course_query.first()
            
            if not course_row:
                continue
            
            # Get ONLY the modules where student is enrolled
            modules_with_activities = []
            for module_id in data['module_ids']:
                module_query = await db.execute(
                    select(ModuleModel)
                    .where(
                        ModuleModel.module_id == module_id,
                        ModuleModel.is_published == True
                    )
                )
                module = module_query.scalar_one_or_none()
                
                if not module:
                    continue
                
                # Get activities for this module with status='active' or 'published'
                activities_query = await db.execute(
                    text("""
                        SELECT activity_id, title, instructions, status, subject, unit_id, 
                               difficulty_level, created_at, order_index
                        FROM activities
                        WHERE module_id = :module_id
                          AND (status = 'active' OR status = 'published')
                        ORDER BY order_index ASC, created_at DESC
                    """),
                    {"module_id": module_id}
                )
                activities_rows = activities_query.fetchall()
                
                # Convert activities to response format
                activities = []
                for act in activities_rows:
                    activities.append({
                        "activity_id": act.activity_id,
                        "title": act.title,
                        "instructions": act.instructions,
                        "status": act.status,
                        "difficulty": act.difficulty_level,
                        "order_index": act.order_index or 0,
                        "created_at": act.created_at.isoformat() if act.created_at else None
                    })
                
                module_read = ModuleRead.model_validate(module)
                module_read.activities = activities  # Attach activities
                modules_with_activities.append(module_read)
            
            # Build course name from subject_code
            course_name = f"{course_row.subject_code} - {course_row.year}/{course_row.semester}"
            
            course_data = CourseWithModules(
                course_id=course_row.course_id,
                name=course_name,
                year=course_row.year,
                semester=str(course_row.semester),
                modules=modules_with_activities,
                enrollment_role=data['enrollment'].role,
                enrollment_status=data['enrollment'].status
            )
            courses_with_modules.append(course_data)
        
        return courses_with_modules
        
    except Exception as e:
        logger.error(f"Failed to list student courses: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list courses: {str(e)}"
        )


@router.get("/gamification", response_model=UserGamificationRead)
@cached(ttl=30, key_prefix="student_gamification")  # Cache for 30 seconds
async def get_student_gamification(
    request: Request,
    student_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get gamification stats for a student.
    
    Returns XP, level, streaks, achievements.
    Auto-creates a gamification record if it doesn't exist.
    """
    try:
        gamification_query = await db.execute(
            select(UserGamificationModel).where(UserGamificationModel.user_id == student_id)
        )
        gamification = gamification_query.scalar_one_or_none()
        
        if not gamification:
            # Create a default gamification record for the user
            from datetime import datetime, timezone, date
            gamification = UserGamificationModel(
                user_id=student_id,
                xp=0,
                level=1,
                streak_days=0,
                longest_streak=0,
                achievements=[],
                badges=[],
                total_exercises_completed=0,
                total_activities_completed=0,
                total_hints_used=0,
                last_activity_date=date.today()
            )
            db.add(gamification)
            await db.commit()
            await db.refresh(gamification)
        
        return UserGamificationRead.model_validate(gamification)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get gamification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get gamification: {str(e)}"
        )


# ==================== STUDENT PERSONAL DASHBOARD ====================

class StudentActivitySummary(BaseModel):
    """Summary of student activity"""
    activity_id: str
    title: str
    status: str
    grade: Optional[float]
    submitted_at: Optional[datetime]
    module_name: Optional[str]
    exercises_completed: int
    total_exercises: int

class StudentStats(BaseModel):
    """Student overall statistics"""
    total_activities: int
    completed_activities: int
    in_progress_activities: int
    average_grade: float
    total_exercises_completed: int
    total_submissions: int
    best_grade: Optional[float]
    worst_grade: Optional[float]
    recent_activities: List[StudentActivitySummary]

class StudentPersonalData(BaseModel):
    """Student personal information"""
    user_id: str
    full_name: str
    email: str
    username: str
    role: str
    created_at: datetime

class StudentDashboardResponse(BaseModel):
    """Complete student dashboard data"""
    personal_data: StudentPersonalData
    stats: StudentStats
    gamification: Optional[UserGamificationRead]

@router.get("/dashboard", response_model=StudentDashboardResponse)
@cached(ttl=60, key_prefix="student_dashboard")  # Cache for 1 minute
async def get_student_dashboard(
    request: Request,
    student_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get complete student dashboard with personal data, statistics, and recent activities.
    
    Returns:
    - Personal information
    - Overall statistics (grades, activities, submissions)
    - Recent activities with details
    - Gamification data (XP, level, badges)
    """
    try:
        # 1. Get student personal data
        user_result = await db.execute(text("""
            SELECT id, full_name, email, username, roles, created_at
            FROM users
            WHERE id = :student_id
        """), {"student_id": student_id})
        user_row = user_result.fetchone()
        
        if not user_row:
            raise HTTPException(status_code=404, detail="Student not found")
        
        # roles is a JSON array, extract first role or default to 'student'
        roles_data = user_row[4]
        role_value = 'student'
        if roles_data:
            if isinstance(roles_data, list):
                role_value = roles_data[0] if roles_data else 'student'
            elif isinstance(roles_data, str):
                import json
                try:
                    roles_list = json.loads(roles_data)
                    role_value = roles_list[0] if roles_list else 'student'
                except:
                    role_value = roles_data
        
        personal_data = StudentPersonalData(
            user_id=user_row[0],
            full_name=user_row[1] or user_row[3],
            email=user_row[2],
            username=user_row[3],
            role=role_value,
            created_at=user_row[5]
        )
        
        # 2. Get student submissions and grades
        submissions_result = await db.execute(text("""
            SELECT 
                s.submission_id,
                s.activity_id,
                a.title,
                s.status,
                s.final_grade,
                s.submitted_at,
                m.title as module_name
            FROM submissions s
            JOIN activities a ON s.activity_id = a.activity_id
            LEFT JOIN modules m ON a.module_id = m.module_id
            WHERE s.student_id = :student_id
            ORDER BY s.submitted_at DESC
        """), {"student_id": student_id})
        
        submissions = submissions_result.fetchall()
        
        # 3. Get exercise completion data
        activity_exercises_result = await db.execute(text("""
            SELECT 
                a.activity_id,
                COUNT(DISTINCT e.exercise_id) as total_exercises,
                COUNT(DISTINCT ea.exercise_id) as completed_exercises
            FROM activities a
            LEFT JOIN exercises_v2 e ON a.activity_id = e.activity_id
            LEFT JOIN exercise_attempts_v2 ea ON e.exercise_id = ea.exercise_id 
                AND ea.user_id = :student_id AND ea.passed = true
            WHERE a.activity_id IN (
                SELECT DISTINCT activity_id FROM submissions WHERE student_id = :student_id
            )
            GROUP BY a.activity_id
        """), {"student_id": student_id})
        
        exercises_by_activity = {row[0]: {"total": row[1], "completed": row[2]} 
                                for row in activity_exercises_result.fetchall()}
        
        # 4. Build activity summaries
        recent_activities = []
        completed_count = 0
        in_progress_count = 0
        grades = []
        
        for sub in submissions:
            activity_id = sub[1]
            grade = sub[4]
            status_value = sub[3]
            
            # Determine status
            if status_value in ['graded', 'reviewed'] and grade is not None:
                activity_status = "completed"
                completed_count += 1
                grades.append(grade)
            elif status_value == 'submitted':
                activity_status = "submitted"
                in_progress_count += 1
            else:
                activity_status = "in_progress"
                in_progress_count += 1
            
            exercise_data = exercises_by_activity.get(activity_id, {"total": 0, "completed": 0})
            
            recent_activities.append(StudentActivitySummary(
                activity_id=activity_id,
                title=sub[2],
                status=activity_status,
                grade=grade,
                submitted_at=sub[5],
                module_name=sub[6],
                exercises_completed=exercise_data["completed"],
                total_exercises=exercise_data["total"]
            ))
        
        # 5. Calculate statistics
        total_activities = len(submissions)
        average_grade = sum(grades) / len(grades) if grades else 0.0
        best_grade = max(grades) if grades else None
        worst_grade = min(grades) if grades else None
        
        # Count total exercises completed
        total_exercises_result = await db.execute(text("""
            SELECT COUNT(DISTINCT exercise_id)
            FROM exercise_attempts_v2
            WHERE user_id = :student_id AND passed = true
        """), {"student_id": student_id})
        total_exercises_completed = total_exercises_result.scalar() or 0
        
        stats = StudentStats(
            total_activities=total_activities,
            completed_activities=completed_count,
            in_progress_activities=in_progress_count,
            average_grade=round(average_grade, 2),
            total_exercises_completed=total_exercises_completed,
            total_submissions=len(submissions),
            best_grade=best_grade,
            worst_grade=worst_grade,
            recent_activities=recent_activities[:10]  # Last 10 activities
        )
        
        # 6. Get gamification data
        gamification_query = await db.execute(
            select(UserGamificationModel).where(UserGamificationModel.user_id == student_id)
        )
        gamification = gamification_query.scalar_one_or_none()
        
        gamification_data = None
        if gamification:
            gamification_data = UserGamificationRead.model_validate(gamification)
        
        return StudentDashboardResponse(
            personal_data=personal_data,
            stats=stats,
            gamification=gamification_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get student dashboard: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard: {str(e)}"
        )
