"""
Enrollment Model - Many-to-Many relationship between Users and Courses

Replaces simple course_id in UserProfile with flexible enrollment system.
"""
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from ..simple_models import Base


class EnrollmentRole(enum.Enum):
    """Enrollment role enum"""
    STUDENT = "STUDENT"
    TEACHER = "TEACHER"
    TA = "TA"  # Teaching Assistant
    OBSERVER = "OBSERVER"


class EnrollmentStatus(enum.Enum):
    """Enrollment status enum"""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    COMPLETED = "COMPLETED"
    DROPPED = "DROPPED"


class EnrollmentModel(Base):
    """
    Enrollment model - Many-to-Many relationship between Users and Courses.
    
    Replaces simple course_id FK with flexible enrollment tracking.
    """
    __tablename__ = "enrollments"
    
    # Primary Key (composite could work, but using ID)
    enrollment_id = Column(String(36), primary_key=True)
    
    # Foreign Keys
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id = Column(String(36), ForeignKey("courses.course_id", ondelete="CASCADE"), nullable=False, index=True)
    module_id = Column(String(36), ForeignKey("modules.module_id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Enrollment details
    role = Column(SQLEnum(EnrollmentRole, name='enrollment_role'), default=EnrollmentRole.STUDENT, nullable=False)
    status = Column(SQLEnum(EnrollmentStatus, name='enrollment_status_new'), default=EnrollmentStatus.ACTIVE, nullable=False)
    
    # Dates
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    dropped_at = Column(DateTime(timezone=True), nullable=True)
    
    # Additional metadata (section, cohort, etc.)
    metadata_json = Column(JSONB, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    # user = relationship("UserModel", back_populates="enrollments")
    # course = relationship("CourseModel", back_populates="enrollments")
    # Note: No direct relationship with UserProfileModel - join via user_id
    
    # Indexes
    __table_args__ = (
        Index('idx_enrollments_user', 'user_id'),
        Index('idx_enrollments_course', 'course_id'),
        Index('idx_enrollments_module', 'module_id'),
        Index('idx_enrollments_user_module', 'user_id', 'module_id'),
        Index('idx_enrollments_status', 'status'),
        Index('idx_enrollments_role', 'role'),
    )
