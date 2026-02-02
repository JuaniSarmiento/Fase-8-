"""
Cognitive Trace SQLAlchemy Model
"""
from sqlalchemy import Column, String, Text, Float, DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from ..database import Base


class CognitiveTraceModel(Base):
    """Cognitive trace persistence model."""
    __tablename__ = "cognitive_traces"
    
    id = Column(String(36), primary_key=True)
    session_id = Column(String(36), nullable=False, index=True)
    student_id = Column(String(100), nullable=False, index=True)
    
    # Trace data
    trace_type = Column(String(50), nullable=False)
    content = Column(Text, nullable=True)
    metadata_json = Column(JSONB, nullable=True)
    
    # Cognitive metrics
    understanding_level = Column(Float, nullable=True)
    difficulty_perception = Column(Float, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        Index('idx_cognitive_trace_session_id', 'session_id'),
        Index('idx_cognitive_trace_student_id', 'student_id'),
    )
