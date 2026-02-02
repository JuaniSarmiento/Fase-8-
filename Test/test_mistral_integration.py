"""Test de integración Mistral + RAG + LangGraph para Fase 8.

Originalmente pensado como script ejecutable, pero también se
ejecuta bajo pytest. Añadimos un fixture ``session_id`` para que
las pruebas que lo reciben como argumento funcionen correctamente.

Verifica:
1. Creación de sesión
2. Chat con Mistral
3. RAG context retrieval
4. LangGraph state transitions

Si el backend de Fase 8 no está corriendo en http://localhost:8000,
estas pruebas se marcan como skip para evitar timeouts largos.
"""
import json

import pytest
import requests

BASE_URL = "http://localhost:8000/api/v3"


@pytest.fixture(scope="module")
def backend_available() -> bool:
    """Verifica que el backend externo esté disponible o salta tests."""
    health_url = "http://localhost:8000/health"
    try:
        resp = requests.get(health_url, timeout=2.0)
    except Exception:
        pytest.skip("Fase 8 backend no está corriendo en http://localhost:8000; se omiten tests de Mistral")

    if resp.status_code != 200:
        pytest.skip("/health del backend Fase 8 no devolvió 200; se omiten tests de Mistral")

    return True


def test_create_session(backend_available: bool):
    """Test: Crear sesión de estudio"""
    payload = {
        "student_id": "2",  # String, not int
        "activity_id": "1",  # String, not int
        "context_data": {
            "topic": "variables en Python",
            "difficulty": "beginner"
        }
    }
    
    response = requests.post(f"{BASE_URL}/student/sessions", json=payload)
    print(f"\n✅ CREATE SESSION: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 201
    session_data = response.json()
    assert "session_id" in session_data
    
    return session_data["session_id"]


@pytest.fixture(scope="module")
def session_id(backend_available: bool) -> str:
    """Fixture que crea una sesión de estudio y devuelve su ID.

    Debe pasar explícitamente el fixture backend_available al helper
    test_create_session para evitar errores de tipo en pytest.
    """
    return test_create_session(backend_available)


def test_chat_with_mistral(session_id: str, backend_available: bool):
    """Test: Chat con Mistral LLM"""
    payload = {
        "message": "¿Qué es una variable en Python?",
        "cognitive_phase": "exploration"
    }
    
    response = requests.post(
        f"{BASE_URL}/student/sessions/{session_id}/chat",
        json=payload
    )
    
    print(f"\n✅ CHAT WITH MISTRAL: {response.status_code}")
    if response.status_code == 200:
        chat_data = response.json()
        print(f"Tutor Response: {chat_data.get('tutor_message', '')[:200]}...")
        print(f"Cognitive Phase: {chat_data.get('cognitive_phase')}")
        print(f"Model Used: {chat_data.get('model', 'unknown')}")
        print(f"RAG Used: {chat_data.get('rag_used', False)}")
    else:
        print(f"❌ Error: {response.text}")
    
    assert response.status_code == 200
    return response.json()


def test_get_session(session_id: str, backend_available: bool):
    """Test: Obtener sesión con historial"""
    # API v3 history endpoint
    response = requests.get(f"{BASE_URL}/student/sessions/{session_id}/history")
    
    print(f"\n✅ GET SESSION: {response.status_code}")
    session_data = response.json()
    print(f"Messages: {session_data.get('message_count')}")
    print(f"Session ID: {session_data.get('session_id')}")
    
    assert response.status_code == 200
    return session_data


def main():
    """Ejecutar test suite"""
    print("=" * 60)
    print("🚀 FASE 8 - TEST MISTRAL + RAG + LANGGRAPH")
    print("=" * 60)
    
    try:
        # 1. Crear sesión
        session_id = test_create_session()
        
        # 2. Chat con Mistral
        chat_response = test_chat_with_mistral(session_id)
        
        # 3. Verificar sesión actualizada
        session_data = test_get_session(session_id)
        
        print("\n" + "=" * 60)
        print("✅ TODOS LOS TESTS PASARON")
        print("=" * 60)
        print(f"\n📊 Resumen:")
        print(f"  - Session ID: {session_id}")
        print(f"  - Modelo: {chat_response.get('model', 'Mistral')}")
        print(f"  - Mensajes: {session_data.get('message_count')}")
        print(f"  - Fase cognitiva: {chat_response.get('cognitive_phase')}")
        
    except AssertionError as e:
        print(f"\n❌ TEST FALLÓ: {e}")
        raise
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        raise


if __name__ == "__main__":
    main()
