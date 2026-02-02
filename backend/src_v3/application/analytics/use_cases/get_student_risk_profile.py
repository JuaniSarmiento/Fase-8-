"""
Get Student Risk Profile Use Case

Business logic for retrieving student risk profile.
"""
from dataclasses import dataclass
from typing import Optional

from backend.src_v3.core.ports.repositories.analytics_repository import AnalyticsRepository
from backend.src_v3.core.domain.entities.student_risk_profile import StudentRiskProfile
from backend.src_v3.core.domain.exceptions import EntityNotFoundException


@dataclass
class GetStudentRiskProfileCommand:
    """
    Command for getting student risk profile.
    """
    student_id: str
    course_id: Optional[str] = None


class GetStudentRiskProfileUseCase:
    """
    Use Case: Get Student Risk Profile
    
    Retrieves risk profile for a specific student.
    """
    
    def __init__(self, analytics_repository: AnalyticsRepository):
        self.analytics_repository = analytics_repository
    
    async def execute(self, command: GetStudentRiskProfileCommand) -> StudentRiskProfile:
        """
        Execute the use case.
        
        Args:
            command: Input command with student_id and optional course_id
            
        Returns:
            StudentRiskProfile domain entity
            
        Raises:
            EntityNotFoundException: If student not found
        """
        # Validate input
        if not command.student_id:
            raise ValueError("student_id is required")
        
        # Retrieve profile from repository
        profile = await self.analytics_repository.get_student_risk_profile(
            student_id=command.student_id,
            course_id=command.course_id
        )
        
        if profile is None:
            raise EntityNotFoundException("StudentRiskProfile", command.student_id)
        
        return profile
