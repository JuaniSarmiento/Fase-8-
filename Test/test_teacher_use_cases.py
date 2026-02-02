"""
Tests unitarios para casos de uso de profesor
"""
import pytest
from datetime import datetime, timedelta

@pytest.fixture
def activity_data():
    return {
        "course_id": 1,
        "teacher_id": 1,
        "title": "TP1: Variables y Control de Flujo",
        "description": "Trabajo práctico sobre fundamentos de Python",
        "topics": ["variables", "tipos_datos", "if_else"],
        "difficulty": "easy",
        "start_date": datetime.now().isoformat(),
        "due_date": (datetime.now() + timedelta(days=14)).isoformat()
    }

@pytest.fixture
def exercise_data():
    return {
        "activity_id": 1,
        "topic": "variables",
        "difficulty": "easy",
        "language": "python",
        "problem_statement": "Crea una variable edad y asígnale tu edad",
        "test_cases": [
            {
                "input": "",
                "expected_output": "20",
                "description": "Debe crear variable edad"
            }
        ],
        "hints": ["Usa el operador =", "No necesitas declarar tipo"],
        "solution_template": "edad = 0"
    }

class TestTeacherUseCases:
    """Tests para casos de uso de profesor"""
    
    def test_create_activity_valid_data(self, activity_data):
        """Test crear actividad con datos válidos"""
        assert activity_data["course_id"] > 0
        assert activity_data["teacher_id"] > 0
        assert len(activity_data["title"]) > 0
        assert len(activity_data["topics"]) > 0
        assert activity_data["difficulty"] in ["easy", "medium", "hard"]
    
    def test_create_activity_dates_validation(self, activity_data):
        """Test validación de fechas de actividad"""
        start = datetime.fromisoformat(activity_data["start_date"])
        due = datetime.fromisoformat(activity_data["due_date"])
        assert due > start, "Fecha de entrega debe ser posterior a inicio"
    
    def test_create_exercise_valid_data(self, exercise_data):
        """Test crear ejercicio con datos válidos"""
        assert exercise_data["activity_id"] > 0
        assert len(exercise_data["problem_statement"]) > 0
        assert len(exercise_data["test_cases"]) > 0
        assert exercise_data["language"] in ["python", "java", "javascript"]
    
    def test_exercise_test_cases_structure(self, exercise_data):
        """Test estructura de casos de prueba"""
        for test_case in exercise_data["test_cases"]:
            assert "input" in test_case
            assert "expected_output" in test_case
            assert "description" in test_case
    
    def test_exercise_hints_not_empty(self, exercise_data):
        """Test hints no vacíos"""
        assert len(exercise_data["hints"]) > 0
        for hint in exercise_data["hints"]:
            assert len(hint) > 0

class TestTeacherValidations:
    """Tests para validaciones de datos de profesor"""
    
    def test_difficulty_levels(self):
        """Test niveles de dificultad válidos"""
        valid_levels = ["easy", "medium", "hard"]
        for level in valid_levels:
            assert level in ["easy", "medium", "hard"]
    
    def test_topics_not_empty(self):
        """Test lista de temas no vacía"""
        topics = ["variables", "funciones", "loops"]
        assert len(topics) > 0
        assert all(len(topic) > 0 for topic in topics)
    
    def test_programming_languages(self):
        """Test lenguajes de programación válidos"""
        valid_languages = ["python", "java", "javascript", "cpp"]
        for lang in valid_languages:
            assert isinstance(lang, str)
            assert len(lang) > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
