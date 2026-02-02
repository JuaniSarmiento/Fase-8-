"""
Analytics Repository Interface - Port

Defines the contract for analytics data access.
Infrastructure layer will implement this interface.
"""
from abc import ABC, abstractmethod
from typing import Optional
from ...domain.entities.course_analytics import CourseAnalytics
from ...domain.entities.student_risk_profile import StudentRiskProfile


class AnalyticsRepository(ABC):
    """
    Analytics Repository Interface (Port)
    
    Defines operations for retrieving analytics data.
    Follows Repository Pattern and Dependency Inversion Principle.
    """
    
    @abstractmethod
    async def get_course_analytics(self, course_id: str) -> Optional[CourseAnalytics]:
        """
        Retrieve aggregated analytics for a course.
        
        Args:
            course_id: Unique identifier of the course
            
        Returns:
            CourseAnalytics domain entity or None if not found
        """
        pass
    
    @abstractmethod
    async def get_student_risk_profile(
        self, 
        student_id: str, 
        course_id: Optional[str] = None
    ) -> Optional[StudentRiskProfile]:
        """
        Retrieve risk profile for a specific student.
        
        Args:
            student_id: Unique identifier of the student
            course_id: Optional course filter
            
        Returns:
            StudentRiskProfile domain entity or None if not found
        """
        pass
