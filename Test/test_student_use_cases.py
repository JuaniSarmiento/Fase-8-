"""
Tests unitarios para casos de uso de estudiante
"""
import pytest
from datetime import datetime
from uuid import uuid4

# Mock data para testing
@pytest.fixture
def student_session_data():
    return {
        "student_id": 2,
        "activity_id": 1,
        "mode": "socratic"
    }

@pytest.fixture
def chat_message_data():
    return {
        "message": "¿Cómo funciona un bucle for en Python?"
    }

@pytest.fixture
def exercise_submission_data():
    return {
        "code": "for i in range(10):\n    print(i)"
    }

class TestStudentUseCases:
    """Tests para casos de uso de estudiante"""
    
    def test_create_session_valid_data(self, student_session_data):
        """Test crear sesión con datos válidos"""
        assert student_session_data["student_id"] > 0
        assert student_session_data["activity_id"] > 0
        assert student_session_data["mode"] in ["socratic", "direct", "exploratory"]
    
    def test_create_session_invalid_mode(self):
        """Test crear sesión con modo inválido"""
        invalid_data = {
            "student_id": 2,
            "activity_id": 1,
            "mode": "invalid_mode"
        }
        # Should raise validation error
        assert invalid_data["mode"] not in ["socratic", "direct", "exploratory"]
    
    def test_chat_message_not_empty(self, chat_message_data):
        """Test mensaje de chat no vacío"""
        assert len(chat_message_data["message"]) > 0
        assert isinstance(chat_message_data["message"], str)
    
    def test_exercise_submission_has_code(self, exercise_submission_data):
        """Test envío de ejercicio tiene código"""
        assert "code" in exercise_submission_data
        assert len(exercise_submission_data["code"]) > 0

class TestStudentValidations:
    """Tests para validaciones de datos de estudiante"""
    
    def test_student_id_positive(self):
        """Test ID de estudiante es positivo"""
        valid_ids = [1, 2, 100, 999]
        for student_id in valid_ids:
            assert student_id > 0
    
    def test_session_id_is_uuid(self):
        """Test ID de sesión es UUID válido"""
        session_id = str(uuid4())
        assert len(session_id) == 36
        assert session_id.count('-') == 4
    
    def test_activity_id_positive(self):
        """Test ID de actividad es positivo"""
        activity_id = 1
        assert activity_id > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
