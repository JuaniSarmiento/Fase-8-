"""
Test Teacher Flow - Exercise Generation with LangGraph

Tests the complete teacher workflow:
1. Upload PDF
2. Generate exercises (LangGraph workflow)
3. Review draft
4. Approve and publish
5. Dashboard and traceability
"""
import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
import uuid


class TestTeacherPDFGeneration:
    """Test PDF-based exercise generation workflow"""
    
    @pytest.mark.asyncio
    @pytest.mark.llm
    async def test_upload_pdf_starts_generation(
        self,
        authenticated_teacher_client: AsyncClient,
        mock_langgraph_teacher_generator
    ):
        """Test uploading PDF and starting generation"""
        # Create mock PDF file
        pdf_content = b"%PDF-1.4 Mock PDF content"
        
        files = {"file": ("test_course.pdf", pdf_content, "application/pdf")}
        data = {
            "teacher_id": "test_teacher_1",
            "course_id": "test_course_1",
            "topic": "Python Functions",
            "difficulty": "mixed",
            "language": "python"
        }
        
        response = await authenticated_teacher_client.post(
            "/api/v3/teacher/generator/upload",
            files=files,
            data=data
        )
        
        assert response.status_code == 201
        result = response.json()
        
        assert "job_id" in result
        assert result["status"] in ["ingestion", "generation"]
        assert "awaiting_approval" in result
        assert result["error"] is None
    
    @pytest.mark.asyncio
    @pytest.mark.llm
    async def test_get_draft_exercises(
        self,
        authenticated_teacher_client: AsyncClient,
        mock_langgraph_teacher_generator
    ):
        """Test retrieving draft exercises"""
        job_id = str(uuid.uuid4())
        
        response = await authenticated_teacher_client.get(
            f"/api/v3/teacher/generator/{job_id}/draft"
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["job_id"] == job_id
        assert result["status"] == "review"
        assert "draft_exercises" in result
        assert len(result["draft_exercises"]) == 10  # Should generate 10 exercises
        assert result["awaiting_approval"] is True
        
        # Validate exercise structure
        exercise = result["draft_exercises"][0]
        assert "title" in exercise
        assert "description" in exercise
        assert "difficulty" in exercise
        assert "starter_code" in exercise
        assert "solution_code" in exercise
        assert "test_cases" in exercise
    
    @pytest.mark.asyncio
    @pytest.mark.llm
    async def test_approve_and_publish_exercises(
        self,
        authenticated_teacher_client: AsyncClient,
        mock_langgraph_teacher_generator
    ):
        """Test approving and publishing exercises"""
        job_id = str(uuid.uuid4())
        
        # Approve specific exercises
        approval_data = {
            "approved_indices": [0, 1, 2, 5, 8]  # Approve 5 out of 10
        }
        
        response = await authenticated_teacher_client.put(
            f"/api/v3/teacher/generator/{job_id}/publish",
            json=approval_data
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["job_id"] == job_id
        assert result["status"] == "published"
        assert result["awaiting_approval"] is False
        assert result["error"] is None
    
    @pytest.mark.asyncio
    @pytest.mark.llm
    async def test_approve_all_exercises(
        self,
        authenticated_teacher_client: AsyncClient,
        mock_langgraph_teacher_generator
    ):
        """Test approving all exercises (null approved_indices)"""
        job_id = str(uuid.uuid4())
        
        # Approve all by not specifying indices
        approval_data = {"approved_indices": None}
        
        response = await authenticated_teacher_client.put(
            f"/api/v3/teacher/generator/{job_id}/publish",
            json=approval_data
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["status"] == "published"


class TestTeacherDashboard:
    """Test teacher dashboard and monitoring"""
    
    @pytest.mark.asyncio
    async def test_get_activity_dashboard(
        self,
        authenticated_teacher_client: AsyncClient,
        create_test_activity
    ):
        """Test getting activity dashboard with student stats"""
        activity = create_test_activity()
        activity_id = activity["activity_id"]
        
        response = await authenticated_teacher_client.get(
            f"/api/v3/teacher/activities/{activity_id}/dashboard"
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["activity_id"] == activity_id
        assert "students" in result
        assert "total_students" in result
        assert "students_started" in result
        assert "students_submitted" in result
        assert "students_passed" in result
        assert "average_grade" in result
        assert "pass_rate" in result
        
        # Validate student status structure
        if result["students"]:
            student = result["students"][0]
            assert "student_id" in student
            assert "status" in student
            assert "submissions_count" in student
            assert "grade" in student
            assert "passed" in student
            assert "cognitive_phase" in student
            assert "frustration_level" in student
            assert "understanding_level" in student
    
    @pytest.mark.asyncio
    async def test_get_student_traceability(
        self,
        authenticated_teacher_client: AsyncClient,
        create_test_activity
    ):
        """Test getting N4 cognitive traceability"""
        activity = create_test_activity()
        activity_id = activity["activity_id"]
        student_id = "test_student_1"
        
        response = await authenticated_teacher_client.get(
            f"/api/v3/teacher/students/{student_id}/activities/{activity_id}/traceability"
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["student_id"] == student_id
        assert result["activity_id"] == activity_id
        assert "cognitive_journey" in result
        assert "interactions" in result
        assert "code_evolution" in result
        assert "frustration_curve" in result
        assert "understanding_curve" in result
        assert "total_hints" in result
        assert "total_time_minutes" in result
        assert "final_phase" in result
        assert "completed" in result
        
        # Validate cognitive journey structure
        if result["cognitive_journey"]:
            phase = result["cognitive_journey"][0]
            assert "phase" in phase
            assert "start_time" in phase
            assert "end_time" in phase
            assert "duration_minutes" in phase
            assert "interactions" in phase
            assert "hints_given" in phase
        
        # Validate interactions structure
        if result["interactions"]:
            interaction = result["interactions"][0]
            assert "timestamp" in interaction
            assert "role" in interaction
            assert "message" in interaction
            assert "cognitive_phase" in interaction


class TestTeacherGrading:
    """Test teacher grading functionality"""
    
    @pytest.mark.asyncio
    async def test_get_submissions(
        self,
        authenticated_teacher_client: AsyncClient,
        create_test_activity
    ):
        """Test getting activity submissions"""
        activity = create_test_activity()
        activity_id = activity["activity_id"]
        
        response = await authenticated_teacher_client.get(
            f"/api/v3/teacher/activities/{activity_id}/submissions"
        )
        
        assert response.status_code == 200
        submissions = response.json()
        
        assert isinstance(submissions, list)
    
    @pytest.mark.asyncio
    async def test_grade_submission(
        self,
        authenticated_teacher_client: AsyncClient
    ):
        """Test grading a submission"""
        submission_id = str(uuid.uuid4())
        
        grade_data = {
            "grade": 8.5,
            "feedback": "Excellent work! Consider edge cases.",
            "override_ai": False
        }
        
        response = await authenticated_teacher_client.post(
            f"/api/v3/teacher/submissions/{submission_id}/grade",
            json=grade_data
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert "submission_id" in result
        assert "grade" in result
    
    @pytest.mark.asyncio
    async def test_grade_all_submissions(
        self,
        authenticated_teacher_client: AsyncClient,
        create_test_activity
    ):
        """Test bulk grading all submissions"""
        activity = create_test_activity()
        activity_id = activity["activity_id"]
        
        response = await authenticated_teacher_client.post(
            f"/api/v3/teacher/activities/{activity_id}/grade-all"
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert "graded_count" in result
    
    @pytest.mark.asyncio
    async def test_get_activity_statistics(
        self,
        authenticated_teacher_client: AsyncClient,
        create_test_activity
    ):
        """Test getting activity statistics"""
        activity = create_test_activity()
        activity_id = activity["activity_id"]
        
        response = await authenticated_teacher_client.get(
            f"/api/v3/teacher/activities/{activity_id}/statistics"
        )
        
        assert response.status_code == 200
        stats = response.json()
        
        assert "total_students" in stats
        assert "total_submissions" in stats
        assert "passed_submissions" in stats
        assert "pass_rate" in stats
        assert "average_grade" in stats


class TestTeacherActivities:
    """Test teacher activity management"""
    
    @pytest.mark.asyncio
    async def test_create_activity(
        self,
        authenticated_teacher_client: AsyncClient
    ):
        """Test creating a new activity"""
        activity_data = {
            "title": "Python Functions Workshop",
            "course_id": "test_course_1",
            "teacher_id": "test_teacher_1",
            "instructions": "Learn about functions",
            "policy": "BALANCED",
            "max_ai_help_level": "MEDIO"
        }
        
        response = await authenticated_teacher_client.post(
            "/api/v3/teacher/activities",
            json=activity_data
        )
        
        assert response.status_code == 201
        result = response.json()
        
        assert "activity_id" in result
        assert result["title"] == activity_data["title"]
        assert result["policy"] == "BALANCED"
    
    @pytest.mark.asyncio
    async def test_list_activities(
        self,
        authenticated_teacher_client: AsyncClient
    ):
        """Test listing teacher's activities"""
        response = await authenticated_teacher_client.get(
            "/api/v3/teacher/activities?teacher_id=test_teacher_1"
        )
        
        assert response.status_code == 200
        activities = response.json()
        
        assert isinstance(activities, list)
    
    @pytest.mark.asyncio
    async def test_publish_activity(
        self,
        authenticated_teacher_client: AsyncClient,
        create_test_activity
    ):
        """Test publishing an activity"""
        activity = create_test_activity()
        activity_id = activity["activity_id"]
        
        response = await authenticated_teacher_client.put(
            f"/api/v3/teacher/activities/{activity_id}/publish"
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["status"] == "published"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
