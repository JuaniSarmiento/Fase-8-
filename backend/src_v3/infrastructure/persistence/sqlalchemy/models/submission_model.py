"""
Submission and GradeAudit SQLAlchemy Models

Handles student code submissions and grading audit trail.
"""
from sqlalchemy import Column, String, Text, Float, Boolean, DateTime, ForeignKey, Index, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..database import Base


class SubmissionStatus(str, enum.Enum):
    """Submission status enum"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    GRADED = "graded"
    REVIEWED = "reviewed"


class SubmissionModel(Base):
    """
    Student code submission for an activity.
    
    Tracks both auto-grading (from test execution) and manual grading (teacher override).
    """
    __tablename__ = "submissions"
    
    # Primary Key (no 'id' column, only submission_id)
    submission_id = Column(String(36), primary_key=True)
    
    # Foreign Keys
    student_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    activity_id = Column(String(36), ForeignKey("activities.activity_id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Submission Data
    code_snapshot = Column(Text, nullable=False)
    status = Column(SQLEnum(SubmissionStatus), default=SubmissionStatus.PENDING, nullable=False, index=True)
    
    # Grading Data
    auto_grade = Column(Float, nullable=True)  # Grade from test execution (0-10)
    final_grade = Column(Float, nullable=True)  # Final grade (auto or manual override)
    is_manual_grade = Column(Boolean, default=False, nullable=False)  # True if teacher overrode
    
    # Feedback
    ai_feedback = Column(Text, nullable=True)  # Auto-generated feedback
    teacher_feedback = Column(Text, nullable=True)  # Manual feedback from teacher
    
    # Test Results (stored as JSON)
    test_results = Column(JSONB, nullable=True)  # {"total_tests": 5, "passed_tests": 3, ...}
    execution_error = Column(Text, nullable=True)  # If code failed to execute
    
    # Grading Metadata
    graded_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # Teacher who graded
    graded_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    grade_audits = relationship("GradeAuditModel", back_populates="submission", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_submission_student_activity', 'student_id', 'activity_id'),
        Index('idx_submission_status', 'status'),
    )


class GradeAuditModel(Base):
    """
    Audit trail for grade changes.
    
    Records every time a teacher manually overrides a grade, providing
    full traceability for academic integrity.
    """
    __tablename__ = "grade_audits"
    
    # Primary Key (no 'id' column, only audit_id)
    audit_id = Column(String(36), primary_key=True)
    
    # Foreign Keys
    submission_id = Column(String(36), ForeignKey("submissions.submission_id", ondelete="CASCADE"), nullable=False, index=True)
    instructor_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Grade Change Data
    previous_grade = Column(Float, nullable=True)  # Grade before change
    new_grade = Column(Float, nullable=False)  # Grade after change
    was_auto_grade = Column(Boolean, nullable=False)  # True if previous was auto-grade
    
    # Justification
    override_reason = Column(Text, nullable=True)  # Why the teacher changed the grade
    
    # Metadata
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    submission = relationship("SubmissionModel", back_populates="grade_audits")
    
    __table_args__ = (
        Index('idx_audit_submission', 'submission_id'),
        Index('idx_audit_instructor', 'instructor_id'),
        Index('idx_audit_timestamp', 'timestamp'),
    )
