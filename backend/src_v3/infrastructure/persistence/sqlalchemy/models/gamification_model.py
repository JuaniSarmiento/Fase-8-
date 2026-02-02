"""
User Gamification Model - XP, levels, streaks

Tracks gamification metrics for each user.
"""
from sqlalchemy import Column, String, Integer, Date, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from ..simple_models import Base


class UserGamificationModel(Base):
    """
    User gamification model - Tracks XP, levels, and streaks.
    
    Stores gamification data for engagement and motivation.
    """
    __tablename__ = "user_gamification"
    
    # Primary Key (one-to-one with UserProfile)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True)
    
    # Gamification metrics
    xp = Column(Integer, default=0, nullable=False)  # Experience points
    level = Column(Integer, default=1, nullable=False)  # Current level
    streak_days = Column(Integer, default=0, nullable=False)  # Consecutive active days
    
    # Streak tracking
    last_activity_date = Column(Date, nullable=True)
    longest_streak = Column(Integer, default=0, nullable=False)
    
    # Achievements and badges
    achievements = Column(JSONB, default=list)  # List of achievement IDs
    badges = Column(JSONB, default=list)  # List of badge IDs
    
    # Statistics
    total_exercises_completed = Column(Integer, default=0, nullable=False)
    total_activities_completed = Column(Integer, default=0, nullable=False)
    total_hints_used = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    # Note: No direct relationship with UserProfileModel - join via user_id if needed
    
    # Indexes
    __table_args__ = (
        Index('idx_gamification_user', 'user_id'),
        Index('idx_gamification_level', 'level'),
        Index('idx_gamification_xp', 'xp'),
    )
