"""Test script para probar todos los endpoints de la API V3.

Pensado originalmente como script ejecutable, pero también se
ejecuta bajo pytest. Para que las pruebas que aceptan argumentos
como ``session_id`` o ``activity_id`` funcionen correctamente con
pytest, definimos fixtures que reutilizan estas funciones helpers.
"""
import json
from datetime import datetime

import httpx
import pytest

BASE_URL = "http://localhost:8000"


@pytest.fixture(scope="module")
def backend_available() -> bool:
    """Ensure external API backend is reachable, or skip tests.

    These tests were originally designed as a manual script hitting a
    running API. When the backend is not running, we skip to avoid
    long timeouts at every http call.
    """
    try:
        resp = httpx.get(f"{BASE_URL}/health", timeout=2.0)
    except Exception:
        pytest.skip("API backend is not running on http://localhost:8000; skipping API endpoint tests")

    if resp.status_code != 200:
        pytest.skip("API backend /health did not return 200; skipping API endpoint tests")

    return True

def print_response(title: str, response: httpx.Response):
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except:
        print(f"Response: {response.text}")
    print()

def test_health(backend_available: bool):
    """Test health endpoint"""
    response = httpx.get(f"{BASE_URL}/health")
    print_response("Health Check", response)
    return response.status_code == 200

def test_create_student_session(backend_available: bool):
    """Test crear sesión de estudiante"""
    payload = {
        "student_id": "2",
        "activity_id": "1",
        "mode": "SOCRATIC"
    }
    response = httpx.post(f"{BASE_URL}/api/v3/student/sessions", json=payload, timeout=30.0)
    print_response("Crear Sesión de Estudiante", response)
    
    if response.status_code == 201:
        session_data = response.json()
        return session_data.get("session_id")
    return None

def test_chat_interaction(session_id: str, backend_available: bool):
    """Test interacción de chat en sesión"""
    payload = {
        "message": "¿Cómo puedo crear una variable en Python?"
    }
    response = httpx.post(
        f"{BASE_URL}/api/v3/student/sessions/{session_id}/chat",
        json=payload,
        timeout=60.0
    )
    print_response(f"Chat en Sesión {session_id[:8]}...", response)
    return response.status_code == 200

def test_get_session_history(session_id: str, backend_available: bool):
    """Test obtener historial de sesión"""
    response = httpx.get(f"{BASE_URL}/api/v3/student/sessions/{session_id}/history", timeout=30.0)
    print_response(f"Historial de Sesión {session_id[:8]}...", response)
    return response.status_code == 200

def test_submit_exercise(session_id: str, exercise_id: str, backend_available: bool):
    """Test enviar solución de ejercicio"""
    payload = {
        "code": "edad = 20\nnombre = 'Juan'\nprint(f'Hola, me llamo {nombre} y tengo {edad} años')"
    }
    response = httpx.post(
        f"{BASE_URL}/api/v3/student/exercises/{exercise_id}/submit",
        json=payload,
        timeout=30.0
    )
    print_response(f"Enviar Ejercicio {exercise_id[:8]}...", response)
    return response.status_code == 200

def test_create_activity(backend_available: bool):
    """Test crear actividad (profesor)"""
    payload = {
        "course_id": "1",
        "teacher_id": "1",
        "title": "TP Test: Variables y Tipos",
        "description": "Actividad de prueba automática",
        "instructions": "Completar ejercicios sobre variables y tipos de datos",
        "topics": ["variables", "tipos_datos", "print"],
        "difficulty": "EASY",
        "start_date": datetime.now().isoformat(),
        "due_date": "2026-02-15T23:59:59"
    }
    response = httpx.post(f"{BASE_URL}/api/v3/teacher/activities", json=payload, timeout=30.0)
    print_response("Crear Actividad (Profesor)", response)
    
    if response.status_code == 201:
        return response.json().get("activity_id")
    return None

def test_create_exercise(activity_id: str, backend_available: bool):
    """Test crear ejercicio para actividad"""
    payload = {
        "activity_id": activity_id,
        "topic": "variables",
        "difficulty": "EASY",
        "language": "python",
        "problem_statement": "Crea variables para nombre y edad, luego imprímelas",
        "test_cases": [
            {
                "input": "",
                "expected_output": "Juan 20",
                "description": "Debe imprimir nombre y edad"
            }
        ],
        "hints": ["Usa print()", "Las variables no necesitan tipo explícito"],
        "solution_template": "nombre = ''\nedad = 0\nprint(nombre, edad)"
    }
    response = httpx.post(
        f"{BASE_URL}/api/v3/teacher/activities/{activity_id}/exercises",
        json=payload,
        timeout=30.0
    )
    print_response(f"Crear Ejercicio para Actividad {activity_id}", response)
    
    if response.status_code == 201:
        return response.json().get("exercise_id")
    return None

def test_get_student_sessions(student_id: str, backend_available: bool):
    """Test obtener sesiones de estudiante"""
    response = httpx.get(f"{BASE_URL}/api/v3/student/{student_id}/sessions", timeout=30.0)
    print_response(f"Sesiones de Estudiante {student_id}", response)
    return response.status_code == 200

def test_get_activity_analytics(activity_id: str, backend_available: bool):
    """Test obtener analytics de actividad"""
    response = httpx.get(f"{BASE_URL}/api/v3/teacher/activities/{activity_id}/analytics", timeout=30.0)
    print_response(f"Analytics de Actividad {activity_id}", response)
    return response.status_code == 200

def run_all_tests():
    """Ejecutar todos los tests en secuencia"""
    print("\n" + "="*60)
    print("🚀 INICIANDO TESTS DE API V3")
    print("="*60)
    
    results = {}
    
    # 1. Health check
    results['health'] = test_health()
    
    # 2. Crear sesión de estudiante
    session_id = test_create_student_session()
    results['create_session'] = session_id is not None
    
    if session_id:
        # 3. Chat en sesión
        results['chat'] = test_chat_interaction(session_id)
        
        # 4. Historial de sesión
        results['history'] = test_get_session_history(session_id)
    
    # 5. Crear actividad (profesor)
    activity_id = test_create_activity()
    results['create_activity'] = activity_id is not None
    
    if activity_id:
        # 6. Crear ejercicio
        exercise_id = test_create_exercise(activity_id)
        results['create_exercise'] = exercise_id is not None
        
        # 7. Analytics de actividad
        results['activity_analytics'] = test_get_activity_analytics(activity_id)
    
    # 8. Obtener sesiones de estudiante
    results['student_sessions'] = test_get_student_sessions("2")
    
    # Resumen
    print("\n" + "="*60)
    print("📊 RESUMEN DE TESTS")
    print("="*60)
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n{'='*60}")
    print(f"Total: {passed}/{total} tests pasaron")
    print(f"{'='*60}\n")
    
    return passed == total


# ==================== Pytest fixtures ====================

@pytest.fixture(scope="module")
def session_id(backend_available: bool) -> str:
    """Create a student session and expose its id as fixture.

    Depends on backend_available to ensure the external API is up
    before attempting to create the session.
    """
    sid = test_create_student_session(backend_available)
    assert sid is not None, "No se pudo crear la sesión de estudiante"
    return sid


@pytest.fixture(scope="module")
def activity_id(backend_available: bool) -> str:
    """Create a teacher activity and expose its id as fixture."""
    aid = test_create_activity(backend_available)
    assert aid is not None, "No se pudo crear la actividad del profesor"
    return aid


@pytest.fixture(scope="module")
def exercise_id(activity_id: str, backend_available: bool) -> str:
    """Create an exercise for the given activity and expose its id."""
    eid = test_create_exercise(activity_id, backend_available)
    assert eid is not None, "No se pudo crear el ejercicio"
    return eid


@pytest.fixture(scope="module")
def student_id() -> str:
    """Expose a default student id used across tests."""
    return "2"

if __name__ == "__main__":
    try:
        success = run_all_tests()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error ejecutando tests: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
