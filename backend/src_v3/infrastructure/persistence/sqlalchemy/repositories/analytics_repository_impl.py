"""
Analytics Repository Implementation - SQLAlchemy

Implements the AnalyticsRepository port using SQLAlchemy.
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy import select, func, and_, desc
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src_v3.core.ports.repositories.analytics_repository import AnalyticsRepository
from backend.src_v3.core.domain.entities.course_analytics import CourseAnalytics
from backend.src_v3.core.domain.entities.student_risk_profile import (
    StudentRiskProfile,
    StudentStatus,
)
from backend.src_v3.core.domain.exceptions import EntityNotFoundException

from ..models.user_model import UserModel
from ..models.session_model import SessionModel
from ..models.exercise_attempt_model import ExerciseAttemptModel
from ..models.risk_model import RiskModel


class AnalyticsRepositoryImpl(AnalyticsRepository):
    """
    SQLAlchemy implementation of AnalyticsRepository.
    
    Translates between ORM models and domain entities.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_course_analytics(self, course_id: str) -> Optional[CourseAnalytics]:
        """
        Retrieve aggregated analytics for a course.
        
        Implements the same logic as V2 but returns domain entities.
        """
        # Get all students in the course. In environments where the legacy
        # 'sessions' table does not exist yet, we treat this as "no data"
        # instead of raising a 500 error.
        stmt = (
            select(SessionModel.student_id)
            .where(SessionModel.course_id == course_id)
            .distinct()
        )
        try:
            result = await self.session.execute(stmt)
        except ProgrammingError as exc:
            if 'relation "sessions" does not exist' in str(exc):
                return CourseAnalytics(
                    course_id=course_id,
                    total_students=0,
                    average_risk=0.0,
                    students_at_risk=0,
                    completion_rate=0.0,
                    students=[],
                )
            raise

        student_ids = [row[0] for row in result.fetchall()]
        
        if not student_ids:
            # Return empty analytics
            return CourseAnalytics(
                course_id=course_id,
                total_students=0,
                average_risk=0.0,
                students_at_risk=0,
                completion_rate=0.0,
                students=[]
            )
        
        # Build student profiles
        student_profiles: List[StudentRiskProfile] = []
        total_risk = 0.0
        students_at_risk_count = 0
        total_completion = 0.0
        
        # Default total exercises (should be calculated from activities)
        total_exercises = 10
        
        for student_id in student_ids:
            profile = await self._build_student_profile(
                student_id, 
                course_id, 
                total_exercises
            )
            if profile:
                student_profiles.append(profile)
                total_risk += profile.risk_score
                total_completion += profile.completion_rate
                if profile.is_at_risk:
                    students_at_risk_count += 1
        
        # Calculate aggregated metrics
        total_students = len(student_profiles)
        average_risk = total_risk / total_students if total_students > 0 else 0.0
        completion_rate_avg = total_completion / total_students if total_students > 0 else 0.0
        
        return CourseAnalytics(
            course_id=course_id,
            total_students=total_students,
            average_risk=round(average_risk, 2),
            students_at_risk=students_at_risk_count,
            completion_rate=round(completion_rate_avg, 2),
            students=student_profiles
        )
    
    async def get_student_risk_profile(
        self, 
        student_id: str, 
        course_id: Optional[str] = None
    ) -> Optional[StudentRiskProfile]:
        """
        Retrieve risk profile for a specific student.
        """
        return await self._build_student_profile(student_id, course_id, 10)
    
    async def _build_student_profile(
        self, 
        student_id: str, 
        course_id: Optional[str],
        total_exercises: int
    ) -> Optional[StudentRiskProfile]:
        """
        Build a StudentRiskProfile from database data.
        
        This is the mapper logic (ORM -> Domain Entity).
        """
        # Get user info
        stmt = select(UserModel).where(UserModel.student_id == student_id)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            student_name = f"Student {student_id}"
            email = f"{student_id}@example.com"
        else:
            student_name = user.full_name or user.username
            email = user.email
        
        # Calculate completed exercises
        stmt_completed = (
            select(func.count(ExerciseAttemptModel.id))
            .where(
                and_(
                    ExerciseAttemptModel.student_id == student_id,
                    ExerciseAttemptModel.status == "success"
                )
            )
        )
        result_completed = await self.session.execute(stmt_completed)
        completed_exercises = result_completed.scalar() or 0
        
        # Calculate time spent (sum of session durations)
        if course_id:
            stmt_time = (
                select(
                    func.sum(
                        func.extract('epoch', SessionModel.end_time - SessionModel.start_time) / 60
                    )
                )
                .where(
                    and_(
                        SessionModel.student_id == student_id,
                        SessionModel.course_id == course_id,
                        SessionModel.end_time.isnot(None)
                    )
                )
            )
        else:
            stmt_time = (
                select(
                    func.sum(
                        func.extract('epoch', SessionModel.end_time - SessionModel.start_time) / 60
                    )
                )
                .where(
                    and_(
                        SessionModel.student_id == student_id,
                        SessionModel.end_time.isnot(None)
                    )
                )
            )
        
        result_time = await self.session.execute(stmt_time)
        time_spent = int(result_time.scalar() or 0)
        
        # Calculate average attempts (simplified - count total attempts / exercises)
        stmt_attempts = (
            select(func.count(ExerciseAttemptModel.id))
            .where(ExerciseAttemptModel.student_id == student_id)
        )
        result_attempts = await self.session.execute(stmt_attempts)
        total_attempts = result_attempts.scalar() or 0
        avg_attempts = total_attempts / completed_exercises if completed_exercises > 0 else 1.0
        
        # Get AI dependency from latest risk assessment
        stmt_risk = (
            select(RiskModel)
            .where(RiskModel.student_id == student_id)
            .order_by(desc(RiskModel.created_at))
        )
        result_risk = await self.session.execute(stmt_risk)
        latest_risk = result_risk.scalar_one_or_none()
        
        if latest_risk and latest_risk.risk_factors:
            ai_dependency = latest_risk.risk_factors.get("ai_dependency_score", 0.0)
        else:
            ai_dependency = 0.0
        
        # Get last activity
        if course_id:
            stmt_last = (
                select(SessionModel)
                .where(
                    and_(
                        SessionModel.student_id == student_id,
                        SessionModel.course_id == course_id
                    )
                )
                .order_by(desc(SessionModel.start_time))
            )
        else:
            stmt_last = (
                select(SessionModel)
                .where(SessionModel.student_id == student_id)
                .order_by(desc(SessionModel.start_time))
            )
        
        result_last = await self.session.execute(stmt_last)
        last_session = result_last.scalar_one_or_none()
        
        if last_session:
            last_activity = last_session.start_time
        else:
            last_activity = datetime.utcnow()
        
        # Determine status
        completion_rate = completed_exercises / total_exercises if total_exercises > 0 else 0
        if completion_rate >= 1.0:
            status = StudentStatus.COMPLETED
        elif completion_rate > 0:
            status = StudentStatus.IN_PROGRESS
        else:
            status = StudentStatus.NOT_STARTED
        
        # Calculate risk score using Value Object
        from backend.src_v3.core.domain.value_objects.risk_score import RiskScore

        risk_score_vo = RiskScore.calculate(
            ai_dependency=ai_dependency,
            avg_attempts=avg_attempts,
            completion_rate=completion_rate,
            time_spent_minutes=time_spent
        )
        risk_score = float(risk_score_vo)
        
        # Create domain entity
        return StudentRiskProfile(
            student_id=student_id,
            student_name=student_name,
            email=email,
            status=status,
            risk_score=round(risk_score, 2),
            time_spent_minutes=time_spent,
            exercises_completed=completed_exercises,
            total_exercises=total_exercises,
            last_activity=last_activity,
            average_attempts=round(avg_attempts, 2),
            ai_dependency_score=round(ai_dependency * 100, 2)
        )
    
    def _calculate_risk_score(
        self,
        ai_dependency: float,
        avg_attempts: float,
        completion_rate: float,
        time_spent: int
    ) -> float:
        """
        Calculate risk score (0-100).
        
        Same formula as V2 for consistency.
        """
        # AI dependency (40%)
        ai_risk = ai_dependency * 100 * 0.4
        
        # Average attempts (30%)
        attempt_risk = min((avg_attempts - 1) / 4, 1.0) * 100 * 0.3
        
        # Completion rate (20%)
        completion_risk = (1 - completion_rate) * 100 * 0.2
        
        # Time spent (10%)
        time_risk = max(0, (60 - time_spent) / 60) * 100 * 0.1
        
        return min(ai_risk + attempt_risk + completion_risk + time_risk, 100)
