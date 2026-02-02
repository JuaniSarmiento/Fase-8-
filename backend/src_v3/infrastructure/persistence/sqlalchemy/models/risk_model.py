"""
Risk SQLAlchemy Model - Persistence Layer Only
"""
from sqlalchemy import Column, String, DateTime, Float, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from ..database import Base


class RiskModel(Base):
    """
    Risk persistence model (ORM).
    
    Maps to 'risks' table (or risk_assessments).
    """
    __tablename__ = "risks"
    
    # Primary Key
    id = Column(String(36), primary_key=True)
    
    # Foreign Keys
    student_id = Column(String(100), nullable=False, index=True)
    session_id = Column(String(36), nullable=True, index=True)
    
    # Risk data
    risk_score = Column(Float, nullable=False)
    risk_factors = Column(JSONB, nullable=True)
    recommendations = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_risk_student_id', 'student_id'),
    )
