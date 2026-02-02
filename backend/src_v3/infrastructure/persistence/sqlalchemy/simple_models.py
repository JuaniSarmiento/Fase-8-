"""
Modelos mínimos para Fase 8 - Clean Architecture
"""
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, Float, ForeignKey, Index, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base, relationship
import enum

Base = declarative_base()


# ==================== ENUMS ====================

class ActivityStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"

class DifficultyLevel(str, enum.Enum):
    FACIL = "facil"
    INTERMEDIO = "intermedio"
    DIFICIL = "dificil"

class SessionStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"

class SessionMode(str, enum.Enum):
    SOCRATIC = "socratic"
    DIRECT = "direct"
    EVALUATION = "evaluation"

class TraceLevel(str, enum.Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

class InteractionType(str, enum.Enum):
    STUDENT_QUESTION = "student_question"
    TUTOR_RESPONSE = "tutor_response"
    CODE_SUBMISSION = "code_submission"
    CODE_REVIEW = "code_review"

class ExerciseDifficulty(str, enum.Enum):
    FACIL = "facil"
    INTERMEDIO = "intermedio"
    DIFICIL = "dificil"

class ProgrammingLanguage(str, enum.Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    JAVA = "java"


# ==================== MODELS ====================

class UserModel(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    roles = Column(JSONB, default=list, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class SubjectModel(Base):
    __tablename__ = "subjects"
    
    subject_id = Column(String(36), primary_key=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    credits = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class CourseModel(Base):
    __tablename__ = "courses"
    
    course_id = Column(String(36), primary_key=True)
    subject_id = Column(String(36), ForeignKey("subjects.subject_id", ondelete="CASCADE"))
    year = Column(Integer, nullable=False)
    semester = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class CommissionModel(Base):
    __tablename__ = "commissions"
    
    commission_id = Column(String(36), primary_key=True)
    course_id = Column(String(36), ForeignKey("courses.course_id", ondelete="CASCADE"))
    teacher_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(100), nullable=False)
    schedule = Column(JSONB, nullable=True)
    capacity = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class UserProfileModel(Base):
    __tablename__ = "user_profiles"
    
    profile_id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    student_id = Column(String(50), unique=True, nullable=True, index=True)
    course_id = Column(String(36), ForeignKey("courses.course_id", ondelete="SET NULL"), nullable=True)
    commission_id = Column(String(36), ForeignKey("commissions.commission_id", ondelete="SET NULL"), nullable=True)
    enrollment_date = Column(DateTime(timezone=True), nullable=True)
    graduation_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ActivityModel(Base):
    __tablename__ = "activities"
    
    activity_id = Column(String(36), primary_key=True)
    title = Column(String(300), nullable=False)
    subject = Column(String(200), nullable=False)
    unit_id = Column(String(50), nullable=False, index=True)
    teacher_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    course_id = Column(String(36), ForeignKey("courses.course_id", ondelete="CASCADE"), nullable=True)
    module_id = Column(String(36), nullable=True, index=True)  # ✅ Added for module support
    order_index = Column(Integer, default=0, nullable=False)  # ✅ Added for sorting in modules
    instructions = Column(Text, nullable=False)
    # Usamos String en lugar de Enum para evitar problemas de validación estricta de SQLAlchemy
    status = Column(String(50), default="draft", index=True)
    difficulty_level = Column(String(50), nullable=True)
    policies = Column(JSONB, nullable=True)
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class SessionModelV2(Base):
    __tablename__ = "sessions_v2"
    
    session_id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"))
    activity_id = Column(String(36), ForeignKey("activities.activity_id", ondelete="CASCADE"))
    course_id = Column(String(36), ForeignKey("courses.course_id", ondelete="SET NULL"), nullable=True)
    status = Column(String(50), default="active", index=True)
    mode = Column(String(50), default="socratic")
    learning_objective = Column(Text, nullable=True)
    cognitive_status = Column(JSONB, nullable=True)
    session_metrics = Column(JSONB, nullable=True)
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ExerciseModelV2(Base):
    __tablename__ = "exercises_v2"
    
    exercise_id = Column(String(36), primary_key=True)
    activity_id = Column(String(36), nullable=True, index=True)  # Link to parent activity
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    subject_id = Column(String(36), ForeignKey("subjects.subject_id", ondelete="CASCADE"))
    unit_number = Column(Integer, nullable=False, index=True)
    difficulty = Column(String(50), nullable=False)
    language = Column(String(50), default="python")
    mission_markdown = Column(Text, nullable=False)
    starter_code = Column(Text, nullable=True)
    solution_code = Column(Text, nullable=True)
    test_cases = Column(JSONB, nullable=True)
    tags = Column(JSONB, nullable=True)
    estimated_time_minutes = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class ExerciseAttemptModelV2(Base):
    __tablename__ = "exercise_attempts_v2"
    
    attempt_id = Column(String(36), primary_key=True)
    exercise_id = Column(String(36), ForeignKey("exercises_v2.exercise_id", ondelete="CASCADE"))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"))
    session_id = Column(String(36), ForeignKey("sessions_v2.session_id", ondelete="CASCADE"))
    code_submitted = Column(Text, nullable=False)
    passed = Column(Boolean, default=False)
    grade = Column(Integer, nullable=True)  # Nota del ejercicio (0-100)
    ai_feedback = Column(Text, nullable=True)  # Feedback detallado de la IA
    execution_output = Column(JSONB, nullable=True)
    test_results = Column(JSONB, nullable=True)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())


class CognitiveTraceModelV2(Base):
    __tablename__ = "cognitive_traces_v2"
    
    trace_id = Column(String(36), primary_key=True)
    session_id = Column(String(36), ForeignKey("sessions_v2.session_id", ondelete="CASCADE"))
    activity_id = Column(String(36), ForeignKey("activities.activity_id", ondelete="CASCADE"))
    trace_level = Column(String(50), default="info")
    interaction_type = Column(String(50), nullable=False)
    semantic_understanding = Column(JSONB, nullable=True)
    algorithmic_evolution = Column(JSONB, nullable=True)
    cognitive_reasoning = Column(JSONB, nullable=True)
    interactional_data = Column(JSONB, nullable=True)
    ethical_risk_data = Column(JSONB, nullable=True)
    process_data = Column(JSONB, nullable=True)
    ai_involvement = Column(Float, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())


class RiskModelV2(Base):
    __tablename__ = "risks_v2"
    
    risk_id = Column(String(36), primary_key=True)
    session_id = Column(String(36), ForeignKey("sessions_v2.session_id", ondelete="CASCADE"))
    activity_id = Column(String(36), ForeignKey("activities.activity_id", ondelete="CASCADE"))
    risk_level = Column(String(20), nullable=False)
    risk_dimension = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    recommendations = Column(JSONB, nullable=True)
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
