"""
Tests de integración para API endpoints
"""
import pytest
import httpx
from datetime import datetime

BASE_URL = "http://localhost:8000"


@pytest.fixture(scope="session")
def backend_available() -> None:
    """Skip integration tests quickly if external backend is not running."""
    try:
        resp = httpx.get(f"{BASE_URL}/health", timeout=2.0)
    except Exception:
        pytest.skip("External backend for integration tests is not available on /health")

    if resp.status_code != 200:
        pytest.skip("External backend for integration tests is not healthy (non-200 /health)")


@pytest.fixture
def client(backend_available):
    """HTTP client para tests"""
    return httpx.Client(base_url=BASE_URL, timeout=30.0)

class TestHealthEndpoints:
    """Tests para endpoints de salud"""
    
    def test_health_endpoint(self, client):
        """Test endpoint de salud"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        # Fase 8 puede devolver "healthy" o "degraded" según el estado de la DB
        assert data["status"] in {"healthy", "degraded"}
        assert "version" in data

class TestStudentEndpoints:
    """Tests para endpoints de estudiante"""
    
    def test_create_session(self, client):
        """Test crear sesión de estudiante"""
        payload = {
            "student_id": 2,
            "activity_id": 1,
            "mode": "socratic"
        }
        response = client.post("/api/v3/student/sessions", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert "session_id" in data
        return data["session_id"]
    
    def test_chat_in_session(self, client):
        """Test enviar mensaje en sesión"""
        # Primero crear sesión
        session_payload = {
            "student_id": 2,
            "activity_id": 1,
            "mode": "socratic"
        }
        session_response = client.post("/api/v3/student/sessions", json=session_payload)
        session_id = session_response.json()["session_id"]
        
        # Luego enviar mensaje
        chat_payload = {"message": "¿Qué es una variable?"}
        response = client.post(f"/api/v3/student/sessions/{session_id}/chat", json=chat_payload)
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
    
    def test_get_session_history(self, client):
        """Test obtener historial de sesión"""
        # Crear sesión primero
        session_payload = {
            "student_id": 2,
            "activity_id": 1,
            "mode": "direct"
        }
        session_response = client.post("/api/v3/student/sessions", json=session_payload)
        session_id = session_response.json()["session_id"]
        
        # Obtener historial
        response = client.get(f"/api/v3/student/sessions/{session_id}/history")
        assert response.status_code == 200
        data = response.json()
        assert "messages" in data

class TestTeacherEndpoints:
    """Tests para endpoints de profesor"""
    
    def test_create_activity(self, client):
        """Test crear actividad"""
        payload = {
            "course_id": 1,
            "teacher_id": 1,
            "title": "TP Test Automatizado",
            "description": "Actividad de prueba",
            "topics": ["testing", "automation"],
            "difficulty": "medium",
            "start_date": datetime.now().isoformat(),
            "due_date": "2026-02-28T23:59:59"
        }
        response = client.post("/api/v3/teacher/activities", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert "activity_id" in data
    
    def test_create_exercise(self, client):
        """Test crear ejercicio para actividad"""
        # Primero crear actividad
        activity_payload = {
            "course_id": 1,
            "teacher_id": 1,
            "title": "TP para ejercicio",
            "description": "Test",
            "topics": ["test"],
            "difficulty": "easy",
            "start_date": datetime.now().isoformat(),
            "due_date": "2026-02-28T23:59:59"
        }
        activity_response = client.post("/api/v3/teacher/activities", json=activity_payload)
        activity_id = activity_response.json()["activity_id"]
        
        # Luego crear ejercicio
        exercise_payload = {
            "activity_id": activity_id,
            "topic": "variables",
            "difficulty": "easy",
            "language": "python",
            "problem_statement": "Crea una variable x = 5",
            "test_cases": [{"input": "", "expected_output": "5", "description": "Test"}],
            "hints": ["Usa ="],
            "solution_template": "x = 0"
        }
        response = client.post(f"/api/v3/teacher/activities/{activity_id}/exercises", json=exercise_payload)
        assert response.status_code == 201
        data = response.json()
        assert "exercise_id" in data

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
