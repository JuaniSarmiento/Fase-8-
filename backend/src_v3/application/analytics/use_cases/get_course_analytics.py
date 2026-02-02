"""
Get Course Analytics Use Case

Business logic for retrieving course analytics.
Coordinates between repository and domain entities.
"""
from dataclasses import dataclass
from typing import Optional

from backend.src_v3.core.ports.repositories.analytics_repository import AnalyticsRepository
from backend.src_v3.core.domain.entities.course_analytics import CourseAnalytics
from backend.src_v3.core.domain.exceptions import EntityNotFoundException


@dataclass
class GetCourseAnalyticsCommand:
    """
    Command for getting course analytics.
    
    Encapsulates input data for the use case.
    """
    course_id: str


class GetCourseAnalyticsUseCase:
    """
    Use Case: Get Course Analytics
    
    Retrieves aggregated analytics for a course.
    Pure business logic without infrastructure dependencies.
    """
    
    def __init__(self, analytics_repository: AnalyticsRepository):
        """
        Initialize use case with dependencies.
        
        Args:
            analytics_repository: Repository for analytics data access
        """
        self.analytics_repository = analytics_repository
    
    async def execute(self, command: GetCourseAnalyticsCommand) -> CourseAnalytics:
        """
        Execute the use case.
        
        Args:
            command: Input command with course_id
            
        Returns:
            CourseAnalytics domain entity
            
        Raises:
            EntityNotFoundException: If course not found
        """
        # Validate input
        if not command.course_id:
            raise ValueError("course_id is required")
        
        # Retrieve analytics from repository
        analytics = await self.analytics_repository.get_course_analytics(
            course_id=command.course_id
        )
        
        # Business rule: Always return analytics even if empty
        # This ensures consistent API behavior
        if analytics is None:
            # Return empty analytics instead of raising exception
            return CourseAnalytics(
                course_id=command.course_id,
                total_students=0,
                average_risk=0.0,
                students_at_risk=0,
                completion_rate=0.0,
                students=[]
            )
        
        return analytics
