"""
Student Repository - Persistence for student sessions and interactions.

Clean Architecture: Infrastructure → Domain mapping.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
import json
from sqlalchemy import text

from backend.src_v3.core.domain.student.entities import (
    StudentSession,
    TutorMessage,
    SocraticDialogue,
    CognitivePhase,
    TutorMode,
)
from backend.src_v3.infrastructure.persistence.sqlalchemy.models import (
    SessionModelV2,
    SessionStatus,
    SessionMode,
    CognitiveTraceModelV2,
    InteractionType,
)


class StudentRepository:
    """
    Repository for student domain operations.
    
    Handles persistence of sessions, messages, and cognitive traces.
    """
    
    def __init__(self, db_session):
        """Initialize with database session"""
        self.db = db_session
    
    async def create_session(self, session: StudentSession) -> StudentSession:
        """Create new learning session"""
        # Preparar datos JSONB como strings JSON
        context_data = json.dumps({
            "cognitive_phase": session.cognitive_phase.value if hasattr(session.cognitive_phase, 'value') else str(session.cognitive_phase),
            "autonomy_level": session.autonomy_level,
            "engagement_score": session.engagement_score,
            "ai_dependency_score": session.ai_dependency_score,
        })
        
        cognitive_state = json.dumps({
            "total_interactions": session.total_interactions,
            "hints_used": session.hints_used,
            "errors_encountered": session.errors_encountered,
        })
        
        # Usar SQL directo para insertar. Usamos user_id y session_id según SessionModelV2
        query = text("""
            INSERT INTO sessions_v2 (session_id, user_id, activity_id, mode, status, cognitive_status, session_metrics, start_time)
            VALUES (:session_id, :user_id, :activity_id, :mode, :status, CAST(:cognitive_status AS jsonb), CAST(:session_metrics AS jsonb), NOW())
            RETURNING session_id
        """)
        
        result = await self.db.execute(query, {
            "session_id": str(session.session_id),
            "user_id": str(session.student_id),
            "activity_id": str(session.activity_id),
            "mode": session.mode.value if hasattr(session.mode, 'value') else session.mode.lower(),
            "status": "active",
            "cognitive_status": context_data,
            "session_metrics": cognitive_state,
        })
        
        # Confirmamos el commit
        await self.db.commit()
        
        return session
    
    async def get_session_by_id(self, session_id: str) -> Optional[StudentSession]:
        """Get session by ID"""
        from sqlalchemy import select, text
        
        # Usar SQL directo para obtener. Columnas corregidas a esquema V2
        query = text("""
            SELECT session_id, user_id, activity_id, mode, status, 
                   cognitive_status, session_metrics, start_time, end_time
            FROM sessions_v2
            WHERE session_id = :session_id
        """)
        
        result = await self.db.execute(query, {"session_id": session_id})
        row = result.fetchone()
        
        if not row:
            return None
        
        # Map row to domain
        context_data = row[5] or {}
        cognitive_state = row[6] or {}
        
        return StudentSession(
            session_id=str(row[0]),
            student_id=str(row[1]),
            activity_id=str(row[2]),
            course_id=None,
            mode=TutorMode(row[3]) if isinstance(row[3], str) else TutorMode.SOCRATIC,
            cognitive_phase=CognitivePhase(context_data.get("cognitive_phase", "exploration")),
            start_time=row[7],
            end_time=row[8],
            is_active=row[4] == "active",
            autonomy_level=context_data.get("autonomy_level", 0.5),
            engagement_score=context_data.get("engagement_score", 0.5),
            ai_dependency_score=context_data.get("ai_dependency_score", 0.0),
            total_interactions=cognitive_state.get("total_interactions", 0),
            hints_used=cognitive_state.get("hints_used", 0),
            errors_encountered=cognitive_state.get("errors_encountered", 0),
        )
    
    async def update_session_metrics(
        self,
        session_id: str,
        metrics_update: Dict[str, Any]
    ) -> None:
        """Update session metrics"""
        from sqlalchemy import text
        import json
        
        # Obtener métricas actuales
        query_get = text("SELECT session_metrics FROM sessions_v2 WHERE session_id = :session_id")
        result = await self.db.execute(query_get, {"session_id": session_id})
        row = result.fetchone()
        
        if row:
            current_metrics = row[0] or {}
            # Actualizar
            query_update = text("""
                UPDATE sessions_v2 
                SET session_metrics = CAST(:metrics AS jsonb)
                WHERE session_id = :session_id
            """)
            await self.db.execute(query_update, {
                "session_id": session_id,
                "metrics": json.dumps(current_metrics)
            })
            await self.db.commit()
    
    async def save_message(self, message: TutorMessage) -> None:
        """Save message as cognitive trace"""
        from sqlalchemy import text
        import json
        import uuid
        
        # Schema V2: No 'content' or 'metadata' columns. 
        # We store chat content in 'interactional_data' and 'semantic_understanding'.
        # 'interactional_data' will hold the message content and basic metadata.
        
        interactional_data = json.dumps({
            "content": message.content,
            "metadata": {
                "current_code": message.current_code,
                "error_context": message.error_context,
                "rag_context": message.rag_context,
                "frustration_level": message.frustration_level,
                "understanding_level": message.understanding_level,
                "cognitive_phase": message.cognitive_phase.value,
            }
        })

        query = text("""
            INSERT INTO cognitive_traces_v2 
            (trace_id, session_id, trace_level, interaction_type, interactional_data, timestamp)
            VALUES (:trace_id, :session_id, :trace_level, :interaction_type, CAST(:interactional_data AS jsonb), NOW())
        """)
        
        await self.db.execute(query, {
            "trace_id": str(uuid.uuid4()),
            "session_id": message.session_id,
            "trace_level": "surface",
            "interaction_type": "student_message" if message.is_from_student else "tutor_response",
            "interactional_data": interactional_data,
        })
        await self.db.commit()
    
    async def save_governance_log(self, session_id: str, analysis: Dict[str, Any]) -> None:
        """Save governance agent analysis log"""
        import json
        import uuid
        from sqlalchemy import text
        
        interactional_data = json.dumps(analysis)
        
        query = text("""
            INSERT INTO cognitive_traces_v2 
            (trace_id, session_id, trace_level, interaction_type, interactional_data, timestamp)
            VALUES (:trace_id, :session_id, :trace_level, :interaction_type, CAST(:interactional_data AS jsonb), NOW())
        """)
        
        await self.db.execute(query, {
            "trace_id": str(uuid.uuid4()),
            "session_id": session_id,
            "trace_level": "meta",
            "interaction_type": "governance_log",
            "interactional_data": interactional_data,
        })
        await self.db.commit()
    
    async def get_session_messages(
        self,
        session_id: str,
        limit: int = 50
    ) -> List[TutorMessage]:
        """Get messages for a session"""
        query = text("""
            SELECT trace_id, session_id, interaction_type, interactional_data, timestamp
            FROM cognitive_traces_v2
            WHERE session_id = :session_id 
            AND interaction_type IN ('student_message', 'tutor_response', 'student_prompt')
            ORDER BY timestamp ASC
            LIMIT :limit
        """)
        result = await self.db.execute(query, {"session_id": session_id, "limit": limit})
        rows = result.fetchall()
        
        messages = []
        for row in rows:
            interaction_type = row[2]
            sender = 'student' if interaction_type == 'student_message' else 'tutor' # Adjusted fallback
             # Fallback if interaction_type is differnt in legacy
            if interaction_type == 'student_prompt': sender = 'student'
            
            data = row[3] or {}
            content = data.get("content", "")
            metadata = data.get("metadata", {})
            
            # Handle legacy data structure if needed (optional)
            
            message = TutorMessage(
                message_id=str(row[0]),
                session_id=str(row[1]),
                sender=sender,
                content=content,
                timestamp=row[4],
                cognitive_phase=CognitivePhase(metadata.get("cognitive_phase", "exploration")),
                current_code=metadata.get("current_code"),
                error_context=metadata.get("error_context"),
                rag_context=metadata.get("rag_context"),
                frustration_level=metadata.get("frustration_level", 0.0),
                understanding_level=metadata.get("understanding_level", 0.5),
            )
            messages.append(message)
        
        return messages
    
    async def get_active_sessions_for_student(
        self,
        student_id: str
    ) -> List[StudentSession]:
        """Get all active sessions for a student"""
        query = text("""
            SELECT session_id, user_id, activity_id, mode, status,
                   cognitive_status, session_metrics, start_time, end_time, created_at
            FROM sessions_v2
            WHERE user_id = :student_id AND status = 'active'
            ORDER BY created_at DESC
        """)
        result = await self.db.execute(query, {"student_id": student_id})
        rows = result.fetchall()
        
        sessions = []
        for row in rows:
            context_data = row[5] or {}
            cognitive_state = row[6] or {}
            
            session = StudentSession(
                session_id=str(row[0]),
                student_id=str(row[1]),
                activity_id=str(row[2]),
                course_id=None,
                mode=TutorMode(row[3]) if isinstance(row[3], str) else TutorMode.SOCRATIC,
                cognitive_phase=CognitivePhase(context_data.get("cognitive_phase", "exploration")),
                start_time=row[7],
                end_time=row[8],
                is_active=row[4] == "active",
                autonomy_level=context_data.get("autonomy_level", 0.5),
                engagement_score=context_data.get("engagement_score", 0.5),
                ai_dependency_score=context_data.get("ai_dependency_score", 0.0),
                total_interactions=cognitive_state.get("total_interactions", 0),
                hints_used=cognitive_state.get("hints_used", 0),
                errors_encountered=cognitive_state.get("errors_encountered", 0),
            )
            sessions.append(session)
        
        return sessions
    
    async def _map_to_domain(self, model: SessionModelV2) -> StudentSession:
        """Map ORM model to domain entity"""
        cognitive_status = model.cognitive_status or {}
        metrics = model.session_metrics or {}
        
        return StudentSession(
            session_id=model.id,
            student_id=model.student_id,
            activity_id=model.activity_id,
            course_id=model.course_id,
            mode=TutorMode[model.mode.name],
            cognitive_phase=CognitivePhase(cognitive_status.get("cognitive_phase", "exploration")),
            start_time=model.start_time,
            end_time=model.end_time,
            is_active=model.status == SessionStatus.ACTIVE,
            autonomy_level=cognitive_status.get("autonomy_level", 0.5),
            engagement_score=cognitive_status.get("engagement_score", 0.5),
            ai_dependency_score=cognitive_status.get("ai_dependency_score", 0.0),
            total_interactions=metrics.get("total_interactions", 0),
            hints_used=metrics.get("hints_used", 0),
            errors_encountered=metrics.get("errors_encountered", 0),
        )
    
    async def save_exercise_attempt(
        self,
        session_id: str,
        user_id: str,
        exercise_id: str,
        code: str,
        passed: bool,
        grade: int = None,
        ai_feedback: str = None,
        execution_output: dict = None
    ) -> str:
        """Save an exercise attempt to database. Returns attempt_id."""
        import uuid
        attempt_id = str(uuid.uuid4())
        
        query = text("""
            INSERT INTO exercise_attempts_v2 
            (attempt_id, session_id, user_id, exercise_id, code_submitted, passed, grade, ai_feedback, execution_output, submitted_at)
            VALUES (:attempt_id, :session_id, NULL, :exercise_id, :code, :passed, :grade, :ai_feedback, CAST(:execution_output AS jsonb), NOW())
        """)
        
        await self.db.execute(query, {
            "attempt_id": attempt_id,
            "session_id": session_id,
            "exercise_id": exercise_id,
            "code": code,
            "passed": passed,
            "grade": grade,
            "ai_feedback": ai_feedback,
            "execution_output": json.dumps(execution_output) if execution_output else None
        })
        await self.db.commit()
        
        return attempt_id
