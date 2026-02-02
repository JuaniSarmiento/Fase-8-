"""
GradingService - Business Logic for Hybrid Grading (AI + Human)

Handles the complete grading lifecycle:
1. Auto-grading based on test execution
2. Teacher manual override
3. Audit logging of grade changes
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
import logging
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

# Import models
from backend.src_v3.infrastructure.persistence.sqlalchemy.models.submission_model import (
    SubmissionModel,
    GradeAuditModel,
    SubmissionStatus
)

logger = logging.getLogger(__name__)


class GradingService:
    """
    Service for managing student submission grading
    
    Business Rules:
    - Auto-grade = (passed_tests / total_tests) * 10
    - Manual override creates audit record
    - Final grade is always the most recent (auto or manual)
    """
    
    def __init__(self, db_session: AsyncSession):
        """
        Initialize grading service
        
        Args:
            db_session: SQLAlchemy async session
        """
        self.db = db_session
    
    def calculate_auto_grade(
        self,
        test_results: Dict[str, Any],
        execution_error: Optional[str] = None
    ) -> float:
        """
        Calculate automatic grade based on test execution
        
        Args:
            test_results: Dict with test execution results
                Expected format: {
                    "total_tests": 5,
                    "passed_tests": 3,
                    "failed_tests": 2,
                    "test_details": [...]
                }
            execution_error: If code failed to execute
        
        Returns:
            Grade from 0.0 to 10.0
        
        Examples:
            >>> service.calculate_auto_grade({"total_tests": 5, "passed_tests": 5})
            10.0
            >>> service.calculate_auto_grade({"total_tests": 5, "passed_tests": 3})
            6.0
            >>> service.calculate_auto_grade({}, execution_error="SyntaxError")
            0.0
        """
        # If code didn't execute, grade is 0
        if execution_error:
            logger.info("Code has execution error, grade = 0.0")
            return 0.0
        
        # Extract test counts
        total_tests = test_results.get("total_tests", 0)
        passed_tests = test_results.get("passed_tests", 0)
        
        if total_tests == 0:
            logger.warning("No tests found, defaulting grade to 0.0")
            return 0.0
        
        # Calculate percentage and convert to 0-10 scale
        percentage = passed_tests / total_tests
        grade = round(percentage * 10.0, 2)
        
        logger.info(
            f"Auto-grade calculated: {passed_tests}/{total_tests} tests passed = {grade}/10"
        )
        
        return grade
    
    async def apply_manual_grade(
        self,
        submission_id: str,
        teacher_id: str,
        manual_grade: float,
        teacher_feedback: Optional[str] = None,
        override_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Apply manual grade override by teacher
        
        This method:
        1. Validates the manual grade (0-10 range)
        2. Updates the submission record
        3. Creates an audit log entry
        4. Returns the updated submission data
        
        Args:
            submission_id: UUID of the submission
            teacher_id: UUID of the teacher making the change
            manual_grade: New grade (0.0 to 10.0)
            teacher_feedback: Optional textual feedback
            override_reason: Optional reason for override
        
        Returns:
            Dict with updated submission data
        
        Raises:
            ValueError: If grade is out of range or submission not found
        """
        # Validate grade range
        if not (0.0 <= manual_grade <= 10.0):
            raise ValueError(f"Grade must be between 0 and 10, got {manual_grade}")
        
        logger.info(
            f"Applying manual grade for submission {submission_id}",
            extra={
                "submission_id": submission_id,
                "teacher_id": teacher_id,
                "manual_grade": manual_grade
            }
        )
        
        try:
            # Get submission from database
            result = await self.db.execute(
                select(SubmissionModel).where(SubmissionModel.submission_id == submission_id)
            )
            submission = result.scalar_one_or_none()
            
            if not submission:
                raise ValueError(f"Submission {submission_id} not found")
            
            # Store previous grade for audit trail
            previous_grade = submission.final_grade
            was_auto_grade = not submission.is_manual_grade
            
            # Update submission with manual grade
            submission.final_grade = manual_grade
            submission.is_manual_grade = True
            submission.teacher_feedback = teacher_feedback
            submission.graded_by = teacher_id
            submission.graded_at = datetime.utcnow()
            submission.status = SubmissionStatus.GRADED
            
            # Create audit log entry
            audit = GradeAuditModel(
                audit_id=f"audit_{submission_id}_{datetime.utcnow().timestamp()}",
                submission_id=submission_id,
                instructor_id=teacher_id,
                previous_grade=previous_grade,
                new_grade=manual_grade,
                was_auto_grade=was_auto_grade,
                override_reason=override_reason,
                timestamp=datetime.utcnow()
            )
            self.db.add(audit)
            
            # Commit transaction
            await self.db.commit()
            await self.db.refresh(submission)
            
            logger.info(
                f"Manual grade applied successfully for submission {submission_id}",
                extra={"previous_grade": previous_grade, "new_grade": manual_grade}
            )
            
            return {
                "submission_id": str(submission.submission_id),
                "grade": submission.final_grade,
                "is_manual_grade": submission.is_manual_grade,
                "teacher_feedback": submission.teacher_feedback,
                "graded_by": str(submission.graded_by),
                "graded_at": submission.graded_at.isoformat(),
                "audit_created": True,
                "previous_grade": previous_grade
            }
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to apply manual grade: {e}", exc_info=True)
            raise RuntimeError(f"Failed to apply manual grade: {str(e)}")
    
    async def get_submission_with_grading_history(
        self,
        submission_id: str
    ) -> Dict[str, Any]:
        """
        Get submission with complete grading history
        
        Args:
            submission_id: UUID of the submission
        
        Returns:
            Dict with submission and audit trail
        """
        try:
            # Fetch submission with audit records
            result = await self.db.execute(
                select(SubmissionModel)
                .options(selectinload(SubmissionModel.grade_audits))
                .where(SubmissionModel.submission_id == submission_id)
            )
            submission = result.scalar_one_or_none()
            
            if not submission:
                raise ValueError(f"Submission {submission_id} not found")
            
            # Build grading history from audit trail
            grading_history = [
                {
                    "audit_id": audit.audit_id,
                    "instructor_id": audit.instructor_id,
                    "previous_grade": audit.previous_grade,
                    "new_grade": audit.new_grade,
                    "was_auto_grade": audit.was_auto_grade,
                    "override_reason": audit.override_reason,
                    "timestamp": audit.timestamp.isoformat()
                }
                for audit in sorted(submission.grade_audits, key=lambda a: a.timestamp, reverse=True)
            ]
            
            return {
                "submission_id": submission.submission_id,
                "student_id": submission.student_id,
                "activity_id": submission.activity_id,
                "current_grade": submission.final_grade,
                "auto_grade": submission.auto_grade,
                "is_manual_grade": submission.is_manual_grade,
                "teacher_feedback": submission.teacher_feedback,
                "ai_feedback": submission.ai_feedback,
                "status": submission.status.value,
                "grading_history": grading_history,
                "created_at": submission.created_at.isoformat(),
                "updated_at": submission.updated_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get grading history: {e}", exc_info=True)
            raise RuntimeError(f"Failed to get grading history: {str(e)}")
    
    def generate_ai_feedback(
        self,
        code: str,
        test_results: Dict[str, Any],
        execution_error: Optional[str] = None
    ) -> str:
        """
        Generate AI-powered feedback for the submission
        
        This can be enhanced to call Mistral AI for detailed feedback,
        but for now provides rule-based feedback.
        
        Args:
            code: The submitted code
            test_results: Test execution results
            execution_error: Execution error if any
        
        Returns:
            Feedback string
        """
        if execution_error:
            return f"❌ Tu código tiene un error de ejecución:\n\n{execution_error}\n\nRevisa la sintaxis y vuelve a intentar."
        
        total = test_results.get("total_tests", 0)
        passed = test_results.get("passed_tests", 0)
        failed = test_results.get("failed_tests", 0)
        
        if passed == total:
            return f"🎉 ¡Excelente! Tu código pasó todos los {total} test cases. Solución correcta."
        
        elif passed > 0:
            return f"⚠️ Tu código pasó {passed} de {total} test cases.\n\nRevisa los casos que fallaron e intenta mejorar tu solución."
        
        else:
            return f"❌ Tu código no pasó ningún test case.\n\nVerifica que tu solución cumpla con los requisitos del enunciado."
    
    async def create_or_update_submission(
        self,
        student_id: str,
        activity_id: str,
        code_snapshot: str,
        test_results: Dict[str, Any],
        execution_error: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create or update a submission with auto-grading
        
        This method:
        1. Calculates auto-grade from test results
        2. Generates AI feedback
        3. Creates new submission or updates existing one
        4. Returns submission data
        
        Args:
            student_id: UUID of the student
            activity_id: UUID of the activity
            code_snapshot: The submitted code
            test_results: Test execution results
            execution_error: Optional execution error
        
        Returns:
            Dict with submission data
        """
        try:
            # Calculate auto-grade
            auto_grade = self.calculate_auto_grade(test_results, execution_error)
            ai_feedback = self.generate_ai_feedback(code_snapshot, test_results, execution_error)
            
            # Check if submission already exists
            result = await self.db.execute(
                select(SubmissionModel).where(
                    SubmissionModel.student_id == student_id,
                    SubmissionModel.activity_id == activity_id
                )
            )
            submission = result.scalar_one_or_none()
            
            if submission:
                # Update existing submission
                submission.code_snapshot = code_snapshot
                submission.auto_grade = auto_grade
                submission.final_grade = auto_grade  # Use auto unless manually overridden
                submission.ai_feedback = ai_feedback
                submission.test_results = test_results
                submission.execution_error = execution_error
                submission.status = SubmissionStatus.SUBMITTED
                submission.submitted_at = datetime.utcnow()
                
                logger.info(f"Updated submission {submission.submission_id} with auto-grade {auto_grade}")
            else:
                # Create new submission
                submission_id = f"sub_{student_id}_{activity_id}_{datetime.utcnow().timestamp()}"
                submission = SubmissionModel(
                    submission_id=submission_id,
                    student_id=student_id,
                    activity_id=activity_id,
                    code_snapshot=code_snapshot,
                    status=SubmissionStatus.SUBMITTED,
                    auto_grade=auto_grade,
                    final_grade=auto_grade,
                    is_manual_grade=False,
                    ai_feedback=ai_feedback,
                    test_results=test_results,
                    execution_error=execution_error,
                    submitted_at=datetime.utcnow()
                )
                self.db.add(submission)
                
                logger.info(f"Created new submission {submission_id} with auto-grade {auto_grade}")
            
            await self.db.commit()
            await self.db.refresh(submission)
            
            return {
                "submission_id": submission.submission_id,
                "student_id": submission.student_id,
                "activity_id": submission.activity_id,
                "auto_grade": submission.auto_grade,
                "final_grade": submission.final_grade,
                "is_manual_grade": submission.is_manual_grade,
                "ai_feedback": submission.ai_feedback,
                "status": submission.status.value,
                "submitted_at": submission.submitted_at.isoformat() if submission.submitted_at else None
            }
            
        except Exception as e:
            logger.error(f"Failed to create/update submission: {e}", exc_info=True)
            await self.db.rollback()
            raise RuntimeError(f"Failed to create/update submission: {str(e)}")
    
    async def bulk_grade_submissions(
        self,
        activity_id: str,
        grading_criteria: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Grade all submissions for an activity (batch processing)
        
        Useful for re-grading after test case updates.
        
        Args:
            activity_id: UUID of the activity
            grading_criteria: Optional custom grading rules
        
        Returns:
            Dict with grading results
        """
        logger.info(f"Starting bulk grading for activity {activity_id}")
        
        try:
            # TODO: Implement with real DB models
            # This would:
            # 1. Fetch all submissions for activity
            # 2. Re-run test cases
            # 3. Recalculate auto-grades
            # 4. Update records
            
            logger.warning("Bulk grading not yet implemented")
            
            return {
                "activity_id": activity_id,
                "submissions_processed": 0,
                "submissions_updated": 0,
                "note": "MOCK RESPONSE - Implement when DB models ready"
            }
            
        except Exception as e:
            logger.error(f"Bulk grading failed: {e}", exc_info=True)
            raise RuntimeError(f"Bulk grading failed: {str(e)}")


# ==================== HELPER FUNCTIONS ====================

def validate_test_results(test_results: Dict[str, Any]) -> bool:
    """
    Validate that test results have the expected structure
    
    Args:
        test_results: Dict to validate
    
    Returns:
        True if valid, False otherwise
    """
    required_keys = {"total_tests", "passed_tests", "failed_tests"}
    return all(key in test_results for key in required_keys)


def calculate_pass_threshold(total_tests: int, threshold: float = 0.6) -> int:
    """
    Calculate minimum tests to pass for a given threshold
    
    Args:
        total_tests: Total number of tests
        threshold: Pass percentage (default 60%)
    
    Returns:
        Minimum tests needed to pass
    
    Examples:
        >>> calculate_pass_threshold(5, 0.6)
        3
        >>> calculate_pass_threshold(10, 0.7)
        7
    """
    import math
    return math.ceil(total_tests * threshold)
