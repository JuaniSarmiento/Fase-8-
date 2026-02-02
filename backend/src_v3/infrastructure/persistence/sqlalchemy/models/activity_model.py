"""
Activity SQLAlchemy Model - Improved with normalized structure

Activities are learning tasks created by teachers.
Properly linked to Courses instead of duplicating data.
"""
from sqlalchemy import Column, String, Integer, DateTime, Index, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..database import Base


class ActivityStatus(enum.Enum):
    """Activity status enum"""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class DifficultyLevel(enum.Enum):
    """Difficulty level enum"""
    INICIAL = "INICIAL"
    INTERMEDIO = "INTERMEDIO"
    AVANZADO = "AVANZADO"


class ActivityModel(Base):
    """Activity persistence model (ORM)"""
    __tablename__ = "activities"
    
    # Primary Key (matches DB schema)
    activity_id = Column(String(36), primary_key=True)
    
    # Basic info
    title = Column(String(255), nullable=False)
    description = Column(String, nullable=True)
    instructions = Column(String, nullable=False)
    evaluation_criteria = Column(JSONB, default=list)
    
    # References (normalized - replaces subject_id string)
    # NOTE: ForeignKey constraints removed to avoid circular dependencies at ORM level
    # The constraints exist in the database schema, but we don't declare them here
    course_id = Column(String(36), nullable=True, index=True)
    module_id = Column(String(36), nullable=True, index=True)
    teacher_id = Column(String(36), nullable=True, index=True)
    
    # Order within module
    order_index = Column(Integer, default=0, nullable=False)
    
    # Pedagogical metadata
    policies = Column(JSONB, default=dict, nullable=False)
    difficulty = Column(String(50), nullable=True)  # Changed from Enum to String to match DB
    estimated_duration_minutes = Column(Integer, nullable=True)
    learning_objectives = Column(JSONB, default=list)
    tags = Column(JSONB, default=list)
    
    # Status
    status = Column(String(50), default='draft', nullable=False)  # Changed from Enum to String
    published_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    # course = relationship("CourseModel", foreign_keys=[course_id])  # Disabled to avoid circular import
    # teacher = relationship("UserModel", foreign_keys=[teacher_id], back_populates="activities_created")
    
    # Indexes
    __table_args__ = (
        Index('idx_activities_course', 'course_id'),
        Index('idx_activities_module', 'module_id'),
        Index('idx_activities_teacher', 'teacher_id'),
        Index('idx_activities_status', 'status'),
        Index('idx_activities_deleted', 'deleted_at'),
        Index('idx_activities_module_order', 'module_id', 'order_index'),
    )
