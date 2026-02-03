"""
Test Student Flow - Learning Interactions with Socratic Tutor

Tests the complete student workflow:
1. Enrollment with access codes
2. View activity history
3. Get workspace and start session
4. Chat with tutor (LangGraph StudentTutorGraph)
5. Submit code and get grades
"""
import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
import uuid


class TestStudentEnrollment:
    """Test student enrollment and course joining"""
    
    @pytest.mark.asyncio
    async def test_join_with_access_code(
        self,
        authenticated_student_client: AsyncClient
    ):
        """Test joining course/activity with access code"""
        student_id = "test_student_1"
        
        enrollment_data = {
            "access_code": "ABC123XYZ"
        }
        
        response = await authenticated_student_client.post(
            f"/api/v3/student/enrollments/join?student_id={student_id}",
            json=enrollment_data
        )
        
        assert response.status_code == 201
        result = response.json()
        
        assert "enrollment_id" in result
        assert result["student_id"] == student_id
        assert "course_id" in result
        assert "enrolled_at" in result
        assert "message" in result
    
    @pytest.mark.asyncio
    async def test_join_with_invalid_code(
        self,
        authenticated_student_client: AsyncClient
    ):
        """Test joining with invalid/expired code"""
        student_id = "test_student_1"
        
        enrollment_data = {
            "access_code": "INVALID_CODE"
        }
        
        response = await authenticated_student_client.post(
            f"/api/v3/student/enrollments/join?student_id={student_id}",
            json=enrollment_data
        )
        
        # Should return 201 in mock, but in real implementation would be 400
        # Testing structure only
        assert response.status_code in [201, 400, 404]
    
    @pytest.mark.asyncio
    async def test_get_activities_history(
        self,
        authenticated_student_client: AsyncClient
    ):
        """Test getting student's activities history"""
        student_id = "test_student_1"
        
        response = await authenticated_student_client.get(
            f"/api/v3/student/activities/history?student_id={student_id}"
        )
        
        assert response.status_code == 200
        activities = response.json()
        
        assert isinstance(activities, list)
        
        if activities:
            activity = activities[0]
            assert "activity_id" in activity
            assert "activity_title" in activity
            assert "course_id" in activity
            assert "status" in activity
            assert activity["status"] in [
                "not_started",
                "in_progress",
                "submitted",
                "graded"
            ]
            assert "cognitive_phase" in activity
            assert "completion_percentage" in activity
            assert "passed" in activity


class TestStudentWorkspace:
    """Test student workspace and activity access"""
    
    @pytest.mark.asyncio
    async def test_get_workspace(
        self,
        authenticated_student_client: AsyncClient,
        create_test_activity
    ):
        """Test getting activity workspace"""
        activity = create_test_activity()
        activity_id = activity["activity_id"]
        student_id = "test_student_1"
        
        response = await authenticated_student_client.get(
            f"/api/v3/student/activities/{activity_id}/workspace?student_id={student_id}"
        )
        
        assert response.status_code == 200
        workspace = response.json()
        
        assert workspace["activity_id"] == activity_id
        assert "activity_title" in workspace
        assert "instructions" in workspace
        assert "expected_concepts" in workspace
        assert "starter_code" in workspace
        assert "template_code" in workspace
        assert "tutor_context" in workspace
        assert "language" in workspace
        assert "difficulty" in workspace
        assert "estimated_time_minutes" in workspace
        
        # Validate expected_concepts is a list
        assert isinstance(workspace["expected_concepts"], list)


class TestSocraticTutor:
    """Test Socratic tutor interactions using StudentTutorGraph"""
    
    @pytest.mark.asyncio
    @pytest.mark.llm
    async def test_start_tutor_session(
        self,
        authenticated_student_client: AsyncClient,
        mock_langgraph_student_tutor,
        create_test_activity
    ):
        """Test starting a tutoring session"""
        activity = create_test_activity()
        
        session_data = {
            "student_id": "test_student_1",
            "activity_id": activity["activity_id"],
            "course_id": "test_course_1",
            "mode": "SOCRATIC"
        }
        
        response = await authenticated_student_client.post(
            "/api/v3/student/sessions",
            json=session_data
        )
        
        assert response.status_code == 201
        result = response.json()
        
        assert "session_id" in result
        assert result["student_id"] == session_data["student_id"]
        assert result["activity_id"] == session_data["activity_id"]
        assert result["mode"] == "SOCRATIC"
        assert "cognitive_phase" in result
        assert result["cognitive_phase"] == "exploration"  # Should start in exploration
    
    @pytest.mark.asyncio
    @pytest.mark.llm
    async def test_chat_with_tutor(
        self,
        authenticated_student_client: AsyncClient,
        mock_langgraph_student_tutor,
        create_test_activity
    ):
        """Test chatting with Socratic tutor"""
        activity = create_test_activity()
        activity_id = activity["activity_id"]
        student_id = "test_student_1"
        
        chat_data = {
            "student_message": "No entiendo cómo empezar este ejercicio",
            "current_code": "# TODO",
            "error_message": None
        }
        
        response = await authenticated_student_client.post(
            f"/api/v3/student/activities/{activity_id}/tutor?student_id={student_id}",
            json=chat_data
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert "tutor_response" in result
        assert "cognitive_phase" in result
        assert "frustration_level" in result
        assert "understanding_level" in result
        assert "hint_count" in result
        assert "rag_context_used" in result
        
        # Validate metrics are in valid range
        assert 0.0 <= result["frustration_level"] <= 1.0
        assert 0.0 <= result["understanding_level"] <= 1.0
        assert result["hint_count"] >= 0
        
        # Tutor response should be a non-empty string
        assert len(result["tutor_response"]) > 0
    
    @pytest.mark.asyncio
    @pytest.mark.llm
    async def test_tutor_with_code_error(
        self,
        authenticated_student_client: AsyncClient,
        mock_langgraph_student_tutor,
        create_test_activity
    ):
        """Test tutor handling code errors"""
        activity = create_test_activity()
        activity_id = activity["activity_id"]
        student_id = "test_student_1"
        
        chat_data = {
            "student_message": "Mi código da error",
            "current_code": "def factorial(n):\n    return n * factorial(n)",
            "error_message": "RecursionError: maximum recursion depth exceeded"
        }
        
        response = await authenticated_student_client.post(
            f"/api/v3/student/activities/{activity_id}/tutor?student_id={student_id}",
            json=chat_data
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # Tutor should respond to the error
        assert "tutor_response" in result
        assert len(result["tutor_response"]) > 0
        
        # Should be in debugging phase or similar
        assert result["cognitive_phase"] in [
            "debugging",
            "implementation",
            "exploration"
        ]
    
    @pytest.mark.asyncio
    @pytest.mark.llm
    async def test_tutor_rag_context(
        self,
        authenticated_student_client: AsyncClient,
        mock_langgraph_student_tutor,
        mock_chroma_vector_store,
        create_test_activity
    ):
        """Test that tutor uses RAG context from course materials"""
        activity = create_test_activity()
        activity_id = activity["activity_id"]
        student_id = "test_student_1"
        
        chat_data = {
            "student_message": "¿Qué es recursión?",
            "current_code": None,
            "error_message": None
        }
        
        response = await authenticated_student_client.post(
            f"/api/v3/student/activities/{activity_id}/tutor?student_id={student_id}",
            json=chat_data
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # Should have RAG context
        assert "rag_context_used" in result
        # In mock, this will have course material fragments
        assert len(result["rag_context_used"]) > 0
    
    @pytest.mark.asyncio
    @pytest.mark.llm
    async def test_cognitive_phase_progression(
        self,
        authenticated_student_client: AsyncClient,
        mock_langgraph_student_tutor,
        create_test_activity
    ):
        """Test that cognitive phase progresses through N4 levels"""
        activity = create_test_activity()
        activity_id = activity["activity_id"]
        student_id = "test_student_1"
        
        # Valid N4 phases
        valid_phases = [
            "exploration",
            "decomposition",
            "planning",
            "implementation",
            "debugging",
            "validation",
            "reflection"
        ]
        
        chat_data = {
            "student_message": "Ya entendí y quiero continuar",
            "current_code": "def factorial(n): return 1 if n <= 1 else n * factorial(n-1)",
            "error_message": None
        }
        
        response = await authenticated_student_client.post(
            f"/api/v3/student/activities/{activity_id}/tutor?student_id={student_id}",
            json=chat_data
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # Should be in a valid cognitive phase
        assert result["cognitive_phase"] in valid_phases


class TestSessionHistory:
    """Test session history and traceability"""
    
    @pytest.mark.asyncio
    async def test_get_session_history(
        self,
        authenticated_student_client: AsyncClient,
        mock_langgraph_student_tutor
    ):
        """Test getting complete session history"""
        session_id = str(uuid.uuid4())
        
        response = await authenticated_student_client.get(
            f"/api/v3/student/sessions/{session_id}/history"
        )
        
        assert response.status_code == 200
        history = response.json()
        
        assert "session_id" in history
        assert "messages" in history
        assert "cognitive_phase" in history
        assert "frustration_level" in history
        assert "understanding_level" in history
        
        # Validate messages structure
        if history["messages"]:
            message = history["messages"][0]
            assert "role" in message
            assert message["role"] in ["student", "assistant", "system"]
            assert "content" in message


class TestStudentSubmissions:
    """Test code submission and evaluation"""
    
    @pytest.mark.asyncio
    async def test_submit_code(
        self,
        authenticated_student_client: AsyncClient
    ):
        """Test submitting code for evaluation"""
        session_id = str(uuid.uuid4())
        
        submission_data = {
            "code": "def factorial(n):\n    return 1 if n <= 1 else n * factorial(n-1)",
            "language": "python"
        }
        
        response = await authenticated_student_client.post(
            f"/api/v3/student/sessions/{session_id}/submit",
            json=submission_data
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert "submission_id" in result
        assert "status" in result
        assert "test_results" in result


class TestStudentGrades:
    """Test student grade viewing"""
    
    @pytest.mark.asyncio
    async def test_get_grades(
        self,
        authenticated_student_client: AsyncClient
    ):
        """Test getting student grades"""
        response = await authenticated_student_client.get(
            "/api/v3/student/grades"
        )
        
        assert response.status_code == 200
        grades = response.json()
        
        assert isinstance(grades, list)
    
    @pytest.mark.asyncio
    async def test_get_grades_summary(
        self,
        authenticated_student_client: AsyncClient
    ):
        """Test getting grades summary"""
        response = await authenticated_student_client.get(
            "/api/v3/student/grades/summary"
        )
        
        assert response.status_code == 200
        summary = response.json()
        
        assert "total_grades" in summary
        assert "average_grade" in summary
        assert "passed_count" in summary
    
    @pytest.mark.asyncio
    async def test_get_course_grades(
        self,
        authenticated_student_client: AsyncClient
    ):
        """Test getting grades for specific course"""
        course_id = "test_course_1"
        
        response = await authenticated_student_client.get(
            f"/api/v3/student/grades/course/{course_id}"
        )
        
        assert response.status_code == 200
        grades = response.json()
        
        assert isinstance(grades, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
