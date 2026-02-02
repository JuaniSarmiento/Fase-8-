"""
Complete set of improved SQLAlchemy models for Fase 8.

All models with:
- Normalized structure (FKs to Subjects/Courses instead of strings)
- UUIDs as primary keys
- Proper relationships with back_populates
- Soft delete (deleted_at)
- Enums for status/types
- Comprehensive indexes (simple + composite + GIN)
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Index, ForeignKey, CheckConstraint, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..database import Base


# ==================== ENUMS ====================

class SessionStatus(enum.Enum):
    """Session status enum"""
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    ABANDONED = "abandoned"


class SessionMode(enum.Enum):
    """Session mode enum"""
    TUTOR = "tutor"
    SIMULATOR = "simulator"
    EVALUATOR = "evaluator"
    GOVERNANCE = "governance"


class ExerciseDifficulty(enum.Enum):
    """Exercise difficulty enum"""
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"


class ProgrammingLanguage(enum.Enum):
    """Programming language enum"""
    PYTHON = "python"
    JAVA = "java"
    JAVASCRIPT = "javascript"


class TraceLevel(enum.Enum):
    """Trace level enum"""
    N1_SUPERFICIAL = "n1_superficial"
    N2_TECNICO = "n2_tecnico"
    N3_INTERACCIONAL = "n3_interaccional"
    N4_COGNITIVO = "n4_cognitivo"


class InteractionType(enum.Enum):
    """Interaction type enum"""
    STUDENT_PROMPT = "student_prompt"
    AI_RESPONSE = "ai_response"
    CODE_COMMIT = "code_commit"
    TUTOR_INTERVENTION = "tutor_intervention"
    TEACHER_FEEDBACK = "teacher_feedback"
    STRATEGY_CHANGE = "strategy_change"
    HYPOTHESIS_FORMULATION = "hypothesis_formulation"
    SELF_CORRECTION = "self_correction"
    AI_CRITIQUE = "ai_critique"


class RiskLevel(enum.Enum):
    """Risk level enum"""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskDimension(enum.Enum):
    """Risk dimension enum"""
    AI_DEPENDENCY = "ai_dependency"
    COGNITIVE = "cognitive"
    ETHICAL = "ethical"
    PERFORMANCE = "performance"


# ==================== IMPROVED SESSION MODEL ====================

class SessionModelV2(Base):
    """Improved Session model with normalized structure"""
    __tablename__ = "sessions"
    
    id = Column(String(36), primary_key=True)
    
    # References with FKs
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    student_id = Column(String(100), nullable=False, index=True)
    activity_id = Column(String(36), ForeignKey("activities.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id = Column(String(36), ForeignKey("courses.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Session type
    mode = Column(SQLEnum(SessionMode), default=SessionMode.TUTOR, nullable=False)
    simulator_type = Column(String(50), nullable=True)
    
    # Timing
    start_time = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    status = Column(SQLEnum(SessionStatus), default=SessionStatus.ACTIVE, nullable=False)
    
    # N4 Traceability metadata
    learning_objective = Column(JSONB, default=dict)
    cognitive_status = Column(JSONB, default=dict)
    session_metrics = Column(JSONB, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("UserModel", back_populates="sessions")
    activity = relationship("ActivityModel", foreign_keys=[activity_id])
    course = relationship("CourseModel", foreign_keys=[course_id])
    traces = relationship("CognitiveTraceModelV2", back_populates="session", cascade="all, delete-orphan")
    risks = relationship("RiskModelV2", back_populates="session", cascade="all, delete-orphan")
    attempts = relationship("ExerciseAttemptModelV2", back_populates="session", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_sessions_user', 'user_id'),
        Index('idx_sessions_student', 'student_id'),
        Index('idx_sessions_activity', 'activity_id'),
        Index('idx_sessions_course', 'course_id'),
        Index('idx_sessions_status', 'status'),
        Index('idx_sessions_mode', 'mode'),
        Index('idx_sessions_user_activity', 'user_id', 'activity_id'),
        Index('idx_sessions_course_status', 'course_id', 'status'),
        Index('idx_sessions_created_desc', 'created_at'),
    )


# ==================== IMPROVED EXERCISE MODEL ====================

class ExerciseModelV2(Base):
    """Improved Exercise model with normalized structure"""
    __tablename__ = "exercises"
    
    id = Column(String(36), primary_key=True)
    
    # Reference to normalized subject
    subject_id = Column(String(36), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Basic info
    title = Column(String(255), nullable=False)
    description = Column(String, nullable=True)
    difficulty = Column(SQLEnum(ExerciseDifficulty), nullable=False)
    language = Column(SQLEnum(ProgrammingLanguage), nullable=False)
    unit_number = Column(Integer, nullable=True)
    
    # Content
    mission_markdown = Column(String, nullable=False)
    story_markdown = Column(String, nullable=True)
    starter_code = Column(String, nullable=False)
    solution_code = Column(String, nullable=True)
    constraints = Column(JSONB, default=list)
    
    # Metadata
    tags = Column(JSONB, default=list)
    learning_objectives = Column(JSONB, default=list)
    cognitive_level = Column(String(50), nullable=True)
    time_estimate_minutes = Column(Integer, nullable=True)
    max_score = Column(Integer, default=100, nullable=False)
    
    # Status
    version = Column(Integer, default=1, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    subject = relationship("SubjectModel", back_populates="exercises")
    attempts = relationship("ExerciseAttemptModelV2", back_populates="exercise", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_exercises_subject', 'subject_id'),
        Index('idx_exercises_difficulty', 'difficulty'),
        Index('idx_exercises_language', 'language'),
        Index('idx_exercises_unit', 'unit_number'),
        Index('idx_exercises_active', 'is_active'),
        Index('idx_exercises_deleted', 'deleted_at'),
        Index('idx_exercises_tags_gin', 'tags', postgresql_using='gin'),
    )


# ==================== IMPROVED EXERCISE ATTEMPT MODEL ====================

class ExerciseAttemptModelV2(Base):
    """Improved Exercise Attempt model with FKs"""
    __tablename__ = "exercise_attempts"
    
    id = Column(String(36), primary_key=True)
    
    # References with FKs
    exercise_id = Column(String(36), ForeignKey("exercises.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Attempt data
    attempt_number = Column(Integer, nullable=False, default=1)
    code_submitted = Column(String, nullable=False)
    
    # Results
    passed = Column(Boolean, default=False, nullable=False)
    score = Column(Integer, nullable=True)
    execution_output = Column(JSONB, default=dict)
    test_results = Column(JSONB, default=list)
    hints_used = Column(JSONB, default=list)
    
    # Feedback
    feedback = Column(String, nullable=True)
    time_taken_seconds = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    exercise = relationship("ExerciseModelV2", back_populates="attempts")
    session = relationship("SessionModelV2", back_populates="attempts")
    
    __table_args__ = (
        Index('idx_attempts_exercise', 'exercise_id'),
        Index('idx_attempts_user', 'user_id'),
        Index('idx_attempts_session', 'session_id'),
        Index('idx_attempts_passed', 'passed'),
        Index('idx_attempts_user_exercise', 'user_id', 'exercise_id'),
        Index('idx_attempts_created', 'created_at'),
    )


# ==================== IMPROVED COGNITIVE TRACE MODEL ====================

class CognitiveTraceModelV2(Base):
    """Improved Cognitive Trace model (N4)"""
    __tablename__ = "cognitive_traces"
    
    id = Column(String(36), primary_key=True)
    
    # References
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(String(100), nullable=False, index=True)
    activity_id = Column(String(36), ForeignKey("activities.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_trace_id = Column(String(36), ForeignKey("cognitive_traces.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Trace metadata
    agent_id = Column(String(100), nullable=True)
    trace_level = Column(SQLEnum(TraceLevel), default=TraceLevel.N4_COGNITIVO, nullable=False)
    interaction_type = Column(SQLEnum(InteractionType), nullable=False)
    
    # Content
    content = Column(String, nullable=False)
    context = Column(JSONB, default=dict)
    metadata = Column(JSONB, default=dict)
    
    # Cognitive analysis
    cognitive_state = Column(String(50), nullable=True)
    cognitive_intent = Column(String(255), nullable=True)
    decision_justification = Column(String, nullable=True)
    alternatives_considered = Column(JSONB, default=list)
    strategy_type = Column(String(100), nullable=True)
    ai_involvement = Column(Float, nullable=True)
    
    # 6 Dimensions of N4 Traceability
    semantic_understanding = Column(JSONB, default=dict)
    algorithmic_evolution = Column(JSONB, default=dict)
    cognitive_reasoning = Column(JSONB, default=dict)
    interactional_data = Column(JSONB, default=dict)
    ethical_risk_data = Column(JSONB, default=dict)
    process_data = Column(JSONB, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    session = relationship("SessionModelV2", back_populates="traces")
    activity = relationship("ActivityModel", foreign_keys=[activity_id])
    parent_trace = relationship("CognitiveTraceModelV2", remote_side=[id], backref="child_traces")
    
    __table_args__ = (
        Index('idx_traces_session', 'session_id'),
        Index('idx_traces_student', 'student_id'),
        Index('idx_traces_activity', 'activity_id'),
        Index('idx_traces_parent', 'parent_trace_id'),
        Index('idx_traces_level', 'trace_level'),
        Index('idx_traces_session_created', 'session_id', 'created_at'),
        Index('idx_traces_semantic_gin', 'semantic_understanding', postgresql_using='gin'),
        Index('idx_traces_algorithmic_gin', 'algorithmic_evolution', postgresql_using='gin'),
        Index('idx_traces_cognitive_gin', 'cognitive_reasoning', postgresql_using='gin'),
        CheckConstraint("ai_involvement IS NULL OR (ai_involvement >= 0 AND ai_involvement <= 1)", name='ck_traces_ai_range'),
    )


# ==================== IMPROVED RISK MODEL ====================

class RiskModelV2(Base):
    """Improved Risk model with normalized structure"""
    __tablename__ = "risks"
    
    id = Column(String(36), primary_key=True)
    
    # References
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(String(100), nullable=False, index=True)
    activity_id = Column(String(36), ForeignKey("activities.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Classification
    risk_type = Column(String(100), nullable=False)
    risk_level = Column(SQLEnum(RiskLevel), nullable=False)
    dimension = Column(SQLEnum(RiskDimension), nullable=False)
    
    # Description
    description = Column(String, nullable=False)
    impact = Column(String, nullable=True)
    evidence = Column(JSONB, default=list)
    trace_ids = Column(JSONB, default=list)
    
    # Analysis
    root_cause = Column(String, nullable=True)
    impact_assessment = Column(String, nullable=True)
    recommendations = Column(JSONB, default=list)
    pedagogical_intervention = Column(String, nullable=True)
    
    # Status
    resolved = Column(Boolean, default=False, nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_notes = Column(String, nullable=True)
    detected_by = Column(String(50), default="AR-IA", nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    session = relationship("SessionModelV2", back_populates="risks")
    activity = relationship("ActivityModel", foreign_keys=[activity_id])
    
    __table_args__ = (
        Index('idx_risks_session', 'session_id'),
        Index('idx_risks_student', 'student_id'),
        Index('idx_risks_activity', 'activity_id'),
        Index('idx_risks_level', 'risk_level'),
        Index('idx_risks_dimension', 'dimension'),
        Index('idx_risks_resolved', 'resolved'),
        Index('idx_risks_student_resolved', 'student_id', 'resolved'),
        Index('idx_risks_resolved_at', 'resolved_at'),
    )
