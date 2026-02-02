"""Dependency Injection Container

Provides instances of services, repositories, and use cases.

Some AI-powered components (like the CodeAuditorAgent) are optional and
can be enabled/disabled via environment variables so that the system
remains testable without external LLMs.
"""
import os
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src_v3.infrastructure.persistence.repositories.student_repository import StudentRepository
from backend.src_v3.infrastructure.persistence.repositories.teacher_repository import TeacherRepository
from backend.src_v3.infrastructure.persistence.repositories.user_repository import UserRepository
from backend.src_v3.infrastructure.ai.agents import SocraticTutorAgent, CodeAuditorAgent, GovernanceAgent
from backend.src_v3.infrastructure.sandbox.service import SimpleSandboxService, DockerSandboxService
from backend.src_v3.infrastructure.ai.rag import ChromaRAGService
from backend.src_v3.infrastructure.ai.exercise_generator import ExerciseGeneratorAgent

from backend.src_v3.application.student.use_cases import (
    StartLearningSessionUseCase,
    SendMessageToTutorUseCase,
    GetSessionHistoryUseCase,
    SubmitCodeForReviewUseCase,
)
from backend.src_v3.application.teacher.use_cases import (
    CreateActivityUseCase,
    GenerateExerciseUseCase,
    PublishActivityUseCase,
    GetActivityExercisesUseCase,
)
from backend.src_v3.application.auth.use_cases import (
    LoginUseCase,
    RegisterUserUseCase,
    GetUserByIdUseCase,
)


logger = logging.getLogger(__name__)


# ==================== REPOSITORIES ====================

def get_student_repository(db_session: AsyncSession) -> StudentRepository:
    """Get student repository instance"""
    return StudentRepository(db_session)


def get_teacher_repository(db_session: AsyncSession) -> TeacherRepository:
    """Get teacher repository instance"""
    return TeacherRepository(db_session)


def get_user_repository(db_session: AsyncSession) -> UserRepository:
    """Get user repository instance"""
    return UserRepository(db_session)


# ==================== AI AGENTS ====================

def get_socratic_tutor_agent() -> SocraticTutorAgent:
    """Get Socratic tutor agent instance"""
    # TODO: Inject LLM client
    return SocraticTutorAgent()


def get_code_auditor_agent() -> Optional[CodeAuditorAgent]:
    """Get code auditor agent instance (optional).

    Controlled by the CODE_AUDITOR_ENABLED env var. When disabled or
    misconfigured, this returns ``None`` so the submit flow falls back to
    deterministic, non-LLM feedback (keeps tests stable).
    """
    enabled = os.getenv("CODE_AUDITOR_ENABLED", "false").lower() in {"1", "true", "yes"}
    if not enabled:
        return None

    try:
        return CodeAuditorAgent()
    except Exception as exc:  # pragma: no cover - defensive safety
        logger.warning("CodeAuditorAgent could not be initialized: %s", exc)
        return None


def get_governance_agent() -> Optional[GovernanceAgent]:
    """Get governance agent instance (optional).

    Controlled by the GOVERNANCE_AGENT_ENABLED env var. When disabled
    or misconfigured, this returns ``None`` so governance endpoints can
    fall back to pure DB-based risk data.
    """
    # Default to TRUE if not set
    enabled = os.getenv("GOVERNANCE_AGENT_ENABLED", "true").lower() in {"1", "true", "yes"}
    if not enabled:
        return None

    try:
        return GovernanceAgent()
    except Exception as exc:  # pragma: no cover - defensive safety
        logger.warning("GovernanceAgent could not be initialized: %s", exc)
        return None


# ==================== STUDENT USE CASES ====================

def get_start_session_use_case(db_session: AsyncSession) -> StartLearningSessionUseCase:
    """Get start session use case"""
    repository = get_student_repository(db_session)
    return StartLearningSessionUseCase(repository)


def get_send_message_use_case(db_session: AsyncSession) -> SendMessageToTutorUseCase:
    """Get send message use case"""
    repository = get_student_repository(db_session)
    agent = get_socratic_tutor_agent()
    gov_agent = get_governance_agent()
    return SendMessageToTutorUseCase(repository, agent, governance_agent=gov_agent)


def get_session_history_use_case(db_session: AsyncSession) -> GetSessionHistoryUseCase:
    """Get session history use case"""
    repository = get_student_repository(db_session)
    return GetSessionHistoryUseCase(repository)


def get_submit_code_use_case(db_session: AsyncSession) -> SubmitCodeForReviewUseCase:
    """Get submit code use case"""
    repository = get_student_repository(db_session)
    # Sandbox execution backend: simple subprocess (default) or Docker-based
    sandbox_backend = os.getenv("SANDBOX_BACKEND", "subprocess").lower()

    sandbox: SimpleSandboxService
    if sandbox_backend == "docker":
        try:
            sandbox = DockerSandboxService()
            logger.info("Using DockerSandboxService for code execution")
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("DockerSandboxService unavailable (%s), falling back to SimpleSandboxService", exc)
            sandbox = SimpleSandboxService()
    else:
        sandbox = SimpleSandboxService()

    auditor = get_code_auditor_agent()
    teacher_repo = get_teacher_repository(db_session)
    return SubmitCodeForReviewUseCase(
        student_repository=repository,
        teacher_repository=teacher_repo,
        auditor_agent=auditor, 
        sandbox_service=sandbox
    )


# ==================== TEACHER USE CASES ====================

def get_create_activity_use_case(db_session: AsyncSession) -> CreateActivityUseCase:
    """Get create activity use case"""
    repository = get_teacher_repository(db_session)
    return CreateActivityUseCase(repository)


def get_generate_exercise_use_case(db_session: AsyncSession) -> GenerateExerciseUseCase:
    """Get generate exercise use case"""
    repository = get_teacher_repository(db_session)
    # Real RAG + LLM generator with safe fallback inside the use case
    rag_service = ChromaRAGService()
    generator = ExerciseGeneratorAgent()
    return GenerateExerciseUseCase(repository, rag_service, generator)


def get_publish_activity_use_case(db_session: AsyncSession) -> PublishActivityUseCase:
    """Get publish activity use case"""
    repository = get_teacher_repository(db_session)
    return PublishActivityUseCase(repository)


def get_activity_exercises_use_case(db_session: AsyncSession) -> GetActivityExercisesUseCase:
    """Get activity exercises use case"""
    repository = get_teacher_repository(db_session)
    return GetActivityExercisesUseCase(repository)


# ==================== AUTH USE CASES ====================


def get_login_use_case(db_session: AsyncSession) -> LoginUseCase:
    """Get login use case"""
    repo = get_user_repository(db_session)
    return LoginUseCase(repo)


def get_register_user_use_case(db_session: AsyncSession) -> RegisterUserUseCase:
    """Get register user use case"""
    repo = get_user_repository(db_session)
    return RegisterUserUseCase(repo)


def get_get_user_by_id_use_case(db_session: AsyncSession) -> GetUserByIdUseCase:
    """Get use case to fetch user by id"""
    repo = get_user_repository(db_session)
    return GetUserByIdUseCase(repo)
