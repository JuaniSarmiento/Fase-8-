"""
Module Model - Course content hierarchy

Modules organize activities within a course.
Hierarchy: Course -> Module -> Activity
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from ..simple_models import Base


class ModuleModel(Base):
    """
    Module model - Organizes activities within a course.
    
    Provides hierarchical structure: Course -> Module -> Activity
    """
    __tablename__ = "modules"
    
    # Primary Key
    module_id = Column(String(36), primary_key=True)
    
    # Foreign Key to Course
    course_id = Column(String(36), ForeignKey("courses.course_id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Module info
    title = Column(String(255), nullable=False)
    description = Column(String, nullable=True)
    
    # Ordering within course
    order_index = Column(Integer, default=0, nullable=False)
    
    # Visibility
    is_published = Column(Boolean, default=False, nullable=False)
    
    # Additional metadata
    metadata_json = Column(JSONB, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    # course = relationship("CourseModel", back_populates="modules")
    # activities = relationship("ActivityModel", back_populates="module", order_by="ActivityModel.order_index")
    
    # Indexes
    __table_args__ = (
        Index('idx_modules_course', 'course_id'),
        Index('idx_modules_course_order', 'course_id', 'order_index'),
        Index('idx_modules_published', 'is_published'),
    )
