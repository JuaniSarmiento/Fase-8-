"""
User Profile Model - Extended academic information.

Separates authentication (UserModel) from academic context (UserProfileModel).
"""
from sqlalchemy import Column, String, Date, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from .base import Base


class UserProfileModel(Base):
    """
    User profile model - Extended academic information.
    
    Stores academic context separated from authentication data.
    """
    __tablename__ = "user_profiles"
    
    # Reference to user
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # Student identification
    student_id = Column(String(100), unique=True, nullable=True, index=True)
    
    # Academic dates (legacy - migrado a Enrollment)
    enrollment_date = Column(Date, nullable=True)
    graduation_date = Column(Date, nullable=True)
    
    # Additional metadata
    metadata_json = Column(JSONB, default=dict)
    
    # Relationships
    user = relationship("UserModel", back_populates="profile", uselist=False)
    enrollments = relationship("EnrollmentModel", back_populates="user_profile")
    gamification = relationship("UserGamificationModel", back_populates="user_profile", uselist=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_user_profiles_user', 'user_id'),
        Index('idx_user_profiles_student', 'student_id'),
    )
