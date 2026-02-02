"""
Student Risk Profile - Domain Entity

Represents a student's learning analytics and risk profile.
Pure business logic without infrastructure dependencies.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class StudentStatus(str, Enum):
    """Student learning status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class RiskLevel(str, Enum):
    """Risk level classification"""
    LOW = "low"        # 0-40
    MEDIUM = "medium"  # 41-60
    HIGH = "high"      # 61-100


@dataclass(frozen=True)
class StudentRiskProfile:
    """
    Student Risk Profile - Domain Entity
    
    Encapsulates student analytics metrics and risk assessment.
    Immutable to ensure data integrity.
    """
    student_id: str
    student_name: str
    email: str
    status: StudentStatus
    risk_score: float  # 0-100
    time_spent_minutes: int
    exercises_completed: int
    total_exercises: int
    last_activity: datetime
    average_attempts: float
    ai_dependency_score: float  # 0-100
    
    def __post_init__(self):
        """Validate domain invariants"""
        if not self.student_id:
            raise ValueError("student_id cannot be empty")
        
        if not (0 <= self.risk_score <= 100):
            raise ValueError("risk_score must be between 0 and 100")
        
        if self.time_spent_minutes < 0:
            raise ValueError("time_spent_minutes cannot be negative")
        
        if self.exercises_completed < 0:
            raise ValueError("exercises_completed cannot be negative")
        
        if self.total_exercises < 0:
            raise ValueError("total_exercises cannot be negative")
        
        if not (0 <= self.ai_dependency_score <= 100):
            raise ValueError("ai_dependency_score must be between 0 and 100")
    
    @property
    def completion_rate(self) -> float:
        """Calculate completion rate as percentage"""
        if self.total_exercises == 0:
            return 0.0
        return (self.exercises_completed / self.total_exercises) * 100
    
    @property
    def risk_level(self) -> RiskLevel:
        """Classify risk level based on risk score"""
        if self.risk_score <= 40:
            return RiskLevel.LOW
        elif self.risk_score <= 60:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.HIGH
    
    @property
    def is_at_risk(self) -> bool:
        """Check if student is at high risk"""
        return self.risk_level == RiskLevel.HIGH
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            "student_id": self.student_id,
            "student_name": self.student_name,
            "email": self.email,
            "status": self.status.value,
            "risk_score": round(self.risk_score, 2),
            "risk_level": self.risk_level.value,
            "time_spent_minutes": self.time_spent_minutes,
            "exercises_completed": self.exercises_completed,
            "total_exercises": self.total_exercises,
            "completion_rate": round(self.completion_rate, 2),
            "last_activity": self.last_activity.isoformat(),
            "average_attempts": round(self.average_attempts, 2),
            "ai_dependency_score": round(self.ai_dependency_score, 2),
            "is_at_risk": self.is_at_risk
        }
