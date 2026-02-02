"""
Session SQLAlchemy Model - Persistence Layer Only
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from ..database import Base


class SessionModel(Base):
    """
    Session persistence model (ORM).
    
    Maps to 'sessions' table.
    """
    __tablename__ = "sessions"
    
    # Primary Key
    id = Column(String(36), primary_key=True)
    
    # Foreign Keys
    student_id = Column(String(100), nullable=False, index=True)
    activity_id = Column(String(100), nullable=False, index=True)
    course_id = Column(String(100), nullable=True, index=True)
    user_id = Column(String(36), ForeignKey('users.id', ondelete="SET NULL"), nullable=True, index=True)
    
    # Session metadata
    mode = Column(String(50), nullable=False, default="tutor")
    simulator_type = Column(String(50), nullable=True, index=True)
    
    # Timing
    start_time = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    
    # State
    state = Column(JSONB, default=dict, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_session_student_id', 'student_id'),
        Index('idx_session_course_id', 'course_id'),
        Index('idx_session_activity_id', 'activity_id'),
    )
