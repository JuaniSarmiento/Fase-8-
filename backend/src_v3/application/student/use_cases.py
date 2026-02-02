"""
Student Use Cases - Application Layer

Complete workflow for student learning interactions.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from uuid import uuid4

from backend.src_v3.core.domain.student.entities import (
    StudentSession,
    TutorMessage,
    SocraticDialogue,
    CognitivePhase,
    TutorMode,
)
from backend.src_v3.infrastructure.persistence.repositories.student_repository import StudentRepository
from backend.src_v3.infrastructure.ai.agents import SocraticTutorAgent


# ==================== COMMANDS ====================

@dataclass
class StartSessionCommand:
    """Command to start new learning session"""
    student_id: str
    activity_id: str
    course_id: Optional[str]
    mode: str = "SOCRATIC"


@dataclass
class SendMessageCommand:
    """Command to send message to tutor"""
    session_id: str
    message: str
    current_code: Optional[str] = None
    error_context: Optional[dict] = None
    exercise_context: Optional[dict] = None


@dataclass
class GetSessionHistoryCommand:
    """Command to get session history"""
    session_id: str
    limit: int = 50


# ==================== USE CASES ====================

class StartLearningSessionUseCase:
    """
    Use case: Start new learning session.
    
    Flow:
    1. Create session domain entity
    2. Persist session
    3. Return session details
    """
    
    def __init__(self, repository: StudentRepository):
        self.repository = repository
    
    async def execute(self, command: StartSessionCommand) -> StudentSession:
        """Execute use case"""
        # Normalize mode to TutorMode, accepting both enum names and values
        mode_str = command.mode or "SOCRATIC"
        try:
            mode_enum = TutorMode[mode_str.upper()]
        except KeyError:
            try:
                mode_enum = TutorMode(mode_str.lower())
            except ValueError:
                mode_enum = TutorMode.SOCRATIC

        # Create domain entity
        session = StudentSession(
            session_id=str(uuid4()),
            student_id=command.student_id,
            activity_id=command.activity_id,
            course_id=command.course_id,
            mode=mode_enum,
            cognitive_phase=CognitivePhase.EXPLORATION,
            start_time=datetime.utcnow(),
        )
        
        # Persist
        created_session = await self.repository.create_session(session)
        
        return created_session


class SendMessageToTutorUseCase:
    """
    Use case: Send message to Socratic tutor.
    
    Flow:
    1. Get session and conversation history
    2. Create message domain entity
    3. Get RAG context (TODO: integrate RAG)
    4. Generate tutor response using agent
    5. Save both messages
    6. Update session metrics
    7. Return tutor response
    """
    
    def __init__(
        self,
        repository: StudentRepository,
        tutor_agent: SocraticTutorAgent,
        governance_agent=None, # Optional injection
    ):
        self.repository = repository
        self.tutor_agent = tutor_agent
        self.governance_agent = governance_agent
    
    async def execute(self, command: SendMessageCommand) -> TutorMessage:
        """Execute use case"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"💬 SendMessage: session_id={command.session_id}, message={command.message[:50]}")
        
        # Get session
        session = await self.repository.get_session_by_id(command.session_id)
        logger.info(f"📦 Session found: {session is not None}")
        if not session:
            logger.error(f"❌ Session {command.session_id} NOT FOUND!")
            raise ValueError(f"Session {command.session_id} not found")
        
        # Get conversation history
        try:
            history = await self.repository.get_session_messages(command.session_id)
            logger.info(f"📜 History length: {len(history)}")
        except Exception as e:
            logger.error(f"❌ ERROR getting history: {type(e).__name__}: {str(e)}")
            raise
        
        # Create student message
        student_message = TutorMessage(
            message_id=str(uuid4()),
            session_id=command.session_id,
            sender='student',
            content=command.message,
            timestamp=datetime.utcnow(),
            cognitive_phase=session.cognitive_phase,
            current_code=command.current_code,
            error_context=command.error_context,
        )
        
        # Save student message
        await self.repository.save_message(student_message)
        
        # Format conversation history for agent
        history_for_agent = []
        for msg in history:
            history_for_agent.append({
                "role": "assistant" if msg.sender == "tutor" else "user",
                "content": msg.content
            })
        
        # Get activity/topic - will be used by RAG service
        topic = command.current_code or "programming"  # Fallback topic
        
        # Generate tutor response using Mistral + RAG
        response_data = await self.tutor_agent.respond(
            student_message=command.message,
            session_id=command.session_id,
            conversation_history=history_for_agent,
            cognitive_phase=session.cognitive_phase.value if hasattr(session.cognitive_phase, 'value') else str(session.cognitive_phase),
            topic=topic,
            exercise_context=command.exercise_context,
        )
        
        # Create TutorMessage from response
        tutor_response = TutorMessage(
            message_id=str(uuid4()),
            session_id=command.session_id,
            sender="tutor",
            content=response_data["response"],
            timestamp=datetime.utcnow(),
            cognitive_phase=CognitivePhase(response_data.get("cognitive_phase", session.cognitive_phase)),
            current_code=command.current_code,
            rag_context=response_data.get("rag_context"),
        )
        
        # Save tutor response
        await self.repository.save_message(tutor_response)
        
        # Update session metrics
        await self.repository.update_session_metrics(
            session_id=command.session_id,
            metrics_update={
                "total_interactions": session.total_interactions + 1,
            }
        )
        
        # --- GOVERNANCE ANALYSIS ---
        if self.governance_agent:
            # Analyze asynchronous (don't block response) or sync?
            # For simplicity in V3, we do it sync but catch errors
            try:
                # Add current interaction to history for analysis
                full_history = history + [student_message, tutor_response]
                
                analysis = await self.governance_agent.analyze_session(
                    session_metrics={
                        "total_interactions": session.total_interactions + 1,
                        "hints_used": session.hints_used,
                        "ai_dependency_score": session.ai_dependency_score
                    },
                    recent_messages=full_history[-10:] # Analyze last 10 messages
                )
                
                # Save if risk is detected (Low, Medium, High)
                # We save mostly everything for detailed analytics
                await self.repository.save_governance_log(command.session_id, analysis)
                
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Governance analysis failed: {e}")
        
        return tutor_response


class GetSessionHistoryUseCase:
    """
    Use case: Get session conversation history.
    
    Flow:
    1. Get session by ID
    2. Get messages
    3. Return dialogue
    """
    
    def __init__(self, repository: StudentRepository):
        self.repository = repository
    
    async def execute(self, command: GetSessionHistoryCommand) -> SocraticDialogue:
        """Execute use case"""
        # Get session
        session = await self.repository.get_session_by_id(command.session_id)
        if not session:
            raise ValueError(f"Session {command.session_id} not found")
        
        # Get messages
        messages = await self.repository.get_session_messages(
            command.session_id,
            limit=command.limit
        )
        
        # Create dialogue aggregate
        dialogue = SocraticDialogue(
            session_id=session.session_id,
            student_id=session.student_id,
            activity_id=session.activity_id,
            messages=messages,
            current_phase=session.cognitive_phase,
            is_active=session.is_active,
        )
        
        return dialogue


class SubmitCodeForReviewUseCase:
    """
    Use case: Submit code for auditor review and grading.
    
    Flow:
    1. Get session
    2. Get exercise (if exercise_id provided)
    3. Build test runner with student code + test cases
    4. Execute in sandbox
    5. Run code auditor agent (if enabled)
    6. Calculate grade (60% tests, 40% AI)
    7. Save audit/grade trace
    8. Return result
    """
    
    def __init__(
        self,
        student_repository: StudentRepository,
        teacher_repository, # Type: TeacherRepository
        auditor_agent=None,
        sandbox_service=None,
    ):
        self.student_repository = student_repository
        self.teacher_repository = teacher_repository
        self.auditor_agent = auditor_agent
        self.sandbox_service = sandbox_service
    
    async def execute(
        self,
        session_id: str,
        code: str,
        language: str = "python",
        exercise_id: Optional[str] = None
    ) -> dict:
        """Execute use case"""
        # Get session
        session = await self.student_repository.get_session_by_id(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        if self.sandbox_service is None:
            raise RuntimeError("Sandbox service is not configured")

        # 1. Prepare code for execution
        code_to_run = code
        exercise_context = None
        test_score = 0
        tests_passed = False
        total_tests = 0
        passed_tests = 0
        solution_code = None
        
        # If exercise provided, wrap with test runner
        if exercise_id:
            exercise = await self.teacher_repository.get_exercise_by_id(exercise_id)
            if exercise:
                # Build detailed exercise context with full mission
                exercise_context = f"""## Ejercicio: {exercise.title}

**Descripción:** {exercise.description}

**Misión/Consigna:**
{getattr(exercise, 'mission_markdown', '') or exercise.description}
"""
                # Get solution code for comparison
                solution_code = getattr(exercise, 'solution_code', None)
                
                if exercise.test_cases:
                    code_to_run = self._build_test_runner(code, exercise.test_cases)
                    total_tests = len(exercise.test_cases)

        # 2. Execute code in sandbox
        execution_result = await self.sandbox_service.execute_code(
            code=code_to_run,
            language=language,
            timeout=10,
        )

        # 3. Analyze execution results (Test Score)
        if total_tests > 0:
            # Parse unittest output from stdout/stderr to count dots/failures
            # This is a naive parser for standard unittest output
            output = execution_result.stderr + "\n" + execution_result.stdout
            
            # Simple heuristic: count OK vs FAIL in unittest output
            if "OK" in output and "Ran" in output:
                # Assuming all passed if final status is OK
                passed_tests = total_tests
                test_score = 100
                tests_passed = True
            else:
                # Count failures? Hard to parse precisely without structured runner
                # Fallback: if exit code 0 -> 100, else 0 (strict)
                # Or try to run regex
                pass
            
            # Use exit code as primary truth for now (unittest returns non-zero on failure)
            if execution_result.exit_code == 0:
                test_score = 100
                tests_passed = True
            else:
                # If failed, score is 0? Or partial?
                # For Phase 8 simple implementation: Binary pass/fail based on exit code
                test_score = 0
                tests_passed = False
        else:
            # No tests provided or syntax error pre-execution
            test_score = 100 if execution_result.exit_code == 0 else 0
            tests_passed = execution_result.exit_code == 0

        # 4. Run AI Auditor (Quality Score)
        ai_score = 0
        ai_feedback = ""
        ai_suggestion = ""
        
        if self.auditor_agent is not None:
            audit_result = await self.auditor_agent.audit(
                code=code,
                language=language,
                execution_result={
                    "exit_code": execution_result.exit_code,
                    "stdout": execution_result.stdout,
                    "stderr": execution_result.stderr,
                },
                exercise_description=exercise_context,
                solution_code=solution_code
            )
            
            if isinstance(audit_result, dict):
                ai_score = audit_result.get("score", 50)
                ai_feedback = audit_result.get("feedback", "")
                ai_suggestion = audit_result.get("suggestion", "")
            else:
                # Legacy string response
                ai_score = 70 # Default neutral
                ai_feedback = str(audit_result)
                ai_suggestion = "Revisar código."
        else:
            # Deterministic fallback
            ai_score = 80 if tests_passed else 40
            ai_feedback = "Análisis automático (AI no disponible)."
            ai_suggestion = "Habilitar auditor IA para feedback detallado."

        # 5. Calculate Final Grade
        # 100% AI-Based Evaluation (tests are informational only)
        final_grade = ai_score
        
        # Save audit as message
        audit_message = TutorMessage(
            message_id=str(uuid4()),
            session_id=session_id,
            sender='tutor',
            content=f"**Evaluación IA:** {final_grade}/100\n\n**Análisis:** {ai_feedback}\n\n💡 **Sugerencia:** {ai_suggestion}",
            timestamp=datetime.utcnow(),
            cognitive_phase=CognitivePhase.VALIDATION,
            current_code=code,
        )
        await self.student_repository.save_message(audit_message)
        
        # Save exercise attempt to database
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"=== EXERCISE ATTEMPT SAVE CHECK === exercise_id={exercise_id}, session={session is not None}")
        
        if exercise_id and session:
            logger.info(f"Saving exercise attempt: session_id={session_id}, user_id={session.student_id}, exercise_id={exercise_id}, grade={final_grade}")
            try:
                await self.student_repository.save_exercise_attempt(
                    session_id=session_id,
                    user_id=session.student_id,
                    exercise_id=exercise_id,
                    code=code,
                    passed=tests_passed,
                    grade=final_grade,
                    ai_feedback=ai_feedback,
                    execution_output={
                        "exit_code": execution_result.exit_code,
                        "stdout": execution_result.stdout[:500] if execution_result.stdout else "",
                        "stderr": execution_result.stderr[:500] if execution_result.stderr else "",
                    }
                )
                logger.info(f"Exercise attempt saved successfully!")
            except Exception as e:
                # Log but don't fail the request
                logger.error(f"Failed to save exercise attempt: {e}", exc_info=True)
        else:
            logger.warning(f"Skipping exercise attempt save: exercise_id={exercise_id}, session_exists={session is not None}")

        return {
            "grade": final_grade,
            "feedback": ai_feedback,
            "suggestion": ai_suggestion,
            "tests_passed": tests_passed,
            "passed": tests_passed, # Required by SubmitCodeResponse
            "details": {
                "test_score": test_score,
                "ai_score": ai_score,
            },
            "execution": {
                "exit_code": execution_result.exit_code,
                "stdout": execution_result.stdout,
                "stderr": execution_result.stderr,
            }
        }

    def _build_test_runner(self, student_code: str, test_cases: list) -> str:
        """Build a python script that runs unittest with student code."""
        # Escape code for safe inclusion
        # Better strategy: Put student code first, then append test class
        
        test_methods = ""
        for i, tc in enumerate(test_cases):
            # Create a test method for each case
            # Assumes student code defines functions that tests call
            # For Phase 8 simple exercises, we might just append assertions?
            # Or assume a specific function name?
            # Let's assume input_data is python code like "foo(1)" and expected is result
            
            # Clean inputs
            inp = tc.input_data.strip()
            exp = tc.expected_output.strip()
            
            if not inp: continue # Skip empty tests
            
            test_methods += f"""
    def test_case_{i+1}(self):
        # {tc.description}
        result = {inp}
        expected = {exp}
        self.assertEqual(result, expected, "Falló caso {i+1}: {tc.description}")
"""

        runner_script = f"""
import unittest
import sys
import io

# --- STUDENT CODE START ---
{student_code}
# --- STUDENT CODE END ---

class TestSubmission(unittest.TestCase):
{test_methods}

if __name__ == '__main__':
    unittest.main()
"""
        return runner_script
