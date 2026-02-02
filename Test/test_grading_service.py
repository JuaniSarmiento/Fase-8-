"""
Test GradingService - Hybrid Grading Logic

Tests the business logic for auto-grading and manual overrides.
"""
import pytest
from backend.src_v3.application.services.grading_service import (
    GradingService,
    validate_test_results,
    calculate_pass_threshold
)


class TestAutoGrading:
    """Test auto-grade calculation"""
    
    def setup_method(self):
        """Setup mock DB session"""
        self.service = GradingService(db_session=None)  # Mock for unit tests
    
    def test_perfect_score(self):
        """All tests passed = grade 10.0"""
        test_results = {
            "total_tests": 5,
            "passed_tests": 5,
            "failed_tests": 0
        }
        
        grade = self.service.calculate_auto_grade(test_results)
        assert grade == 10.0
    
    def test_partial_score(self):
        """3 of 5 tests passed = grade 6.0"""
        test_results = {
            "total_tests": 5,
            "passed_tests": 3,
            "failed_tests": 2
        }
        
        grade = self.service.calculate_auto_grade(test_results)
        assert grade == 6.0
    
    def test_zero_score(self):
        """No tests passed = grade 0.0"""
        test_results = {
            "total_tests": 5,
            "passed_tests": 0,
            "failed_tests": 5
        }
        
        grade = self.service.calculate_auto_grade(test_results)
        assert grade == 0.0
    
    def test_execution_error(self):
        """Code with execution error = grade 0.0"""
        test_results = {"total_tests": 5, "passed_tests": 0}
        
        grade = self.service.calculate_auto_grade(
            test_results,
            execution_error="SyntaxError: invalid syntax"
        )
        assert grade == 0.0
    
    def test_no_tests(self):
        """No tests defined = grade 0.0"""
        test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0
        }
        
        grade = self.service.calculate_auto_grade(test_results)
        assert grade == 0.0
    
    def test_rounding(self):
        """Test grade rounding to 2 decimals"""
        test_results = {
            "total_tests": 3,
            "passed_tests": 2,
            "failed_tests": 1
        }
        
        grade = self.service.calculate_auto_grade(test_results)
        # 2/3 = 0.6666... * 10 = 6.6666... rounded to 6.67
        assert grade == 6.67


class TestManualGrading:
    """Test manual grade override"""
    
    def setup_method(self):
        """Setup mock DB session"""
        self.service = GradingService(db_session=None)
    
    @pytest.mark.asyncio
    async def test_valid_manual_grade(self):
        """Apply valid manual grade"""
        result = await self.service.apply_manual_grade(
            submission_id="sub_123",
            teacher_id="teacher_456",
            manual_grade=8.5,
            teacher_feedback="Buen trabajo"
        )
        
        assert result["submission_id"] == "sub_123"
        assert result["grade"] == 8.5
        assert result["is_manual_grade"] is True
        assert result["graded_by"] == "teacher_456"
        assert result["audit_created"] is True
    
    @pytest.mark.asyncio
    async def test_invalid_grade_too_high(self):
        """Grade > 10 should raise ValueError"""
        with pytest.raises(ValueError, match="must be between 0 and 10"):
            await self.service.apply_manual_grade(
                submission_id="sub_123",
                teacher_id="teacher_456",
                manual_grade=11.0
            )
    
    @pytest.mark.asyncio
    async def test_invalid_grade_negative(self):
        """Negative grade should raise ValueError"""
        with pytest.raises(ValueError, match="must be between 0 and 10"):
            await self.service.apply_manual_grade(
                submission_id="sub_123",
                teacher_id="teacher_456",
                manual_grade=-1.0
            )
    
    @pytest.mark.asyncio
    async def test_manual_override_with_reason(self):
        """Manual grade with override reason"""
        result = await self.service.apply_manual_grade(
            submission_id="sub_123",
            teacher_id="teacher_456",
            manual_grade=9.0,
            teacher_feedback="Excelente código",
            override_reason="Teacher adjusted grade based on effort"
        )
        
        assert result["grade"] == 9.0
        assert result["audit_created"] is True


class TestAIFeedback:
    """Test AI feedback generation"""
    
    def setup_method(self):
        """Setup service"""
        self.service = GradingService(db_session=None)
    
    def test_perfect_submission_feedback(self):
        """All tests passed feedback"""
        test_results = {
            "total_tests": 5,
            "passed_tests": 5,
            "failed_tests": 0
        }
        
        feedback = self.service.generate_ai_feedback(
            code="def factorial(n): return 1 if n==0 else n*factorial(n-1)",
            test_results=test_results
        )
        
        assert "Excelente" in feedback or "excelente" in feedback
        assert "5" in feedback
    
    def test_partial_pass_feedback(self):
        """Some tests passed feedback"""
        test_results = {
            "total_tests": 5,
            "passed_tests": 3,
            "failed_tests": 2
        }
        
        feedback = self.service.generate_ai_feedback(
            code="def factorial(n): return n",
            test_results=test_results
        )
        
        assert "3" in feedback
        assert "5" in feedback
    
    def test_execution_error_feedback(self):
        """Execution error feedback"""
        feedback = self.service.generate_ai_feedback(
            code="def factorial(n):\nreturn n",
            test_results={},
            execution_error="IndentationError: expected an indented block"
        )
        
        assert "error" in feedback.lower()
        assert "IndentationError" in feedback
    
    def test_all_failed_feedback(self):
        """All tests failed feedback"""
        test_results = {
            "total_tests": 5,
            "passed_tests": 0,
            "failed_tests": 5
        }
        
        feedback = self.service.generate_ai_feedback(
            code="def factorial(n): pass",
            test_results=test_results
        )
        
        assert "ningún" in feedback or "ninguno" in feedback


class TestHelperFunctions:
    """Test helper functions"""
    
    def test_validate_test_results_valid(self):
        """Valid test results structure"""
        test_results = {
            "total_tests": 5,
            "passed_tests": 3,
            "failed_tests": 2
        }
        
        assert validate_test_results(test_results) is True
    
    def test_validate_test_results_invalid(self):
        """Invalid test results structure"""
        test_results = {
            "total_tests": 5
            # Missing passed_tests and failed_tests
        }
        
        assert validate_test_results(test_results) is False
    
    def test_calculate_pass_threshold_60_percent(self):
        """60% pass threshold"""
        assert calculate_pass_threshold(5, 0.6) == 3
        assert calculate_pass_threshold(10, 0.6) == 6
    
    def test_calculate_pass_threshold_70_percent(self):
        """70% pass threshold"""
        assert calculate_pass_threshold(5, 0.7) == 4
        assert calculate_pass_threshold(10, 0.7) == 7
    
    def test_calculate_pass_threshold_rounding_up(self):
        """Threshold rounds up (ceiling)"""
        # 3 * 0.6 = 1.8, should round to 2
        assert calculate_pass_threshold(3, 0.6) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
