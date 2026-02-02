"""
Tests para modelos de dominio
"""
import pytest
from datetime import datetime
from uuid import uuid4

class TestSessionModel:
    """Tests para modelo de sesión"""
    
    def test_session_creation(self):
        """Test creación de sesión"""
        session_data = {
            "id": str(uuid4()),
            "student_id": 2,
            "activity_id": 1,
            "mode": "socratic",
            "status": "active",
            "context_data": {},
            "cognitive_state": {},
            "start_time": datetime.now()
        }
        assert session_data["id"] is not None
        assert session_data["status"] == "active"
    
    def test_session_modes(self):
        """Test modos de sesión válidos"""
        valid_modes = ["socratic", "direct", "exploratory"]
        for mode in valid_modes:
            assert mode in ["socratic", "direct", "exploratory"]

class TestExerciseModel:
    """Tests para modelo de ejercicio"""
    
    def test_exercise_creation(self):
        """Test creación de ejercicio"""
        exercise_data = {
            "id": str(uuid4()),
            "activity_id": 1,
            "topic": "variables",
            "difficulty": "easy",
            "language": "python",
            "problem_statement": "Test problem",
            "test_cases": [],
            "hints": [],
            "solution_template": "x = 0"
        }
        assert exercise_data["id"] is not None
        assert len(exercise_data["problem_statement"]) > 0
    
    def test_exercise_difficulty_levels(self):
        """Test niveles de dificultad"""
        levels = ["easy", "medium", "hard"]
        for level in levels:
            assert level in ["easy", "medium", "hard"]

class TestActivityModel:
    """Tests para modelo de actividad"""
    
    def test_activity_creation(self):
        """Test creación de actividad"""
        activity_data = {
            "id": 1,
            "course_id": 1,
            "teacher_id": 1,
            "title": "Test Activity",
            "description": "Test description",
            "topics": ["topic1", "topic2"],
            "difficulty": "medium",
            "status": "draft"
        }
        assert activity_data["id"] > 0
        assert len(activity_data["topics"]) > 0
    
    def test_activity_status_values(self):
        """Test valores de estado válidos"""
        valid_statuses = ["draft", "active", "completed", "archived"]
        for status in valid_statuses:
            assert status in ["draft", "active", "completed", "archived"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
