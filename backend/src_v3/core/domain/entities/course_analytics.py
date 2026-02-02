"""
Course Analytics - Domain Entity

Represents aggregated analytics for a course.
"""
from dataclasses import dataclass
from typing import List
from .student_risk_profile import StudentRiskProfile


@dataclass(frozen=True)
class CourseAnalytics:
    """
    Course Analytics - Domain Entity
    
    Aggregates student risk profiles to provide course-level metrics.
    Immutable to ensure data integrity.
    """
    course_id: str
    total_students: int
    average_risk: float
    students_at_risk: int
    completion_rate: float
    students: List[StudentRiskProfile]
    
    def __post_init__(self):
        """Validate domain invariants"""
        if not self.course_id:
            raise ValueError("course_id cannot be empty")
        
        if self.total_students < 0:
            raise ValueError("total_students cannot be negative")
        
        if not (0 <= self.average_risk <= 100):
            raise ValueError("average_risk must be between 0 and 100")
        
        if self.students_at_risk < 0:
            raise ValueError("students_at_risk cannot be negative")
        
        if not (0 <= self.completion_rate <= 100):
            raise ValueError("completion_rate must be between 0 and 100")
        
        if self.total_students != len(self.students):
            raise ValueError("total_students must match students list length")
    
    @property
    def risk_percentage(self) -> float:
        """Calculate percentage of students at risk"""
        if self.total_students == 0:
            return 0.0
        return (self.students_at_risk / self.total_students) * 100
    
    @property
    def has_critical_risks(self) -> bool:
        """Check if course has any students at high risk"""
        return self.students_at_risk > 0
    
    def get_high_risk_students(self) -> List[StudentRiskProfile]:
        """Get list of students with high risk"""
        return [s for s in self.students if s.is_at_risk]
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            "course_id": self.course_id,
            "total_students": self.total_students,
            "average_risk": round(self.average_risk, 2),
            "students_at_risk": self.students_at_risk,
            "risk_percentage": round(self.risk_percentage, 2),
            "completion_rate": round(self.completion_rate, 2),
            "has_critical_risks": self.has_critical_risks,
            "students": [s.to_dict() for s in self.students]
        }
