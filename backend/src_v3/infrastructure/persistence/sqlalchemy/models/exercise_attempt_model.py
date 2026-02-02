"""
Exercise Attempt SQLAlchemy Model - Persistence Layer Only
"""
from sqlalchemy import Column, String, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from ..database import Base


class ExerciseAttemptModel(Base):
    """
    Exercise Attempt persistence model (ORM).
    
    Maps to 'exercise_attempts' table.
    """
    __tablename__ = "exercise_attempts"
    
    # Primary Key
    id = Column(String(36), primary_key=True)
    
    # Foreign Keys (logical, not enforced)
    student_id = Column(String(100), nullable=False, index=True)
    exercise_id = Column(String(36), nullable=False, index=True)
    session_id = Column(String(36), nullable=True, index=True)
    
    # Attempt data
    code = Column(Text, nullable=False)
    language = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)  # success, error, partial
    error_message = Column(Text, nullable=True)
    test_results = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_exercise_attempt_student_id', 'student_id'),
        Index('idx_exercise_attempt_exercise_id', 'exercise_id'),
    )
