"""
Exercise SQLAlchemy Model
"""
from sqlalchemy import Column, String, Text, Integer, Boolean, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy import DateTime
from ..database import Base


class ExerciseModel(Base):
    """Exercise persistence model."""
    __tablename__ = "exercises_v2"  # Fixed: Use exercises_v2 table that actually exists
    
    # Primary Key (no 'id' column, only exercise_id)
    exercise_id = Column(String(36), primary_key=True)
    activity_id = Column(String(36), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    difficulty = Column(String(50), nullable=True)
    exercise_type = Column(String(50), nullable=False)
    language = Column(String(50), nullable=False, default="python")
    
    # Test cases
    test_cases = Column(JSONB, nullable=True)
    
    # Solution and template code
    solution = Column(Text, nullable=True)  # Reference solution for teacher
    reference_solution = Column(Text, nullable=True)  # Solución de referencia detallada para IA
    template_code = Column(Text, nullable=True)  # Starter code for students
    
    # Grading configuration for AI
    grading_config = Column(JSONB, nullable=True, default=dict)  # Config para evaluación IA
    
    # Metadata
    order_index = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # No need for __table_args__ since activity_id already has index=True
