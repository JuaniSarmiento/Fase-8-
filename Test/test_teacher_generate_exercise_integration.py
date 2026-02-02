"""Integration test for teacher activity + exercise generation (Fase 8).

Assumes the Fase 8 backend is running on http://localhost:8000 via docker-compose.
"""

import httpx
import pytest

BASE_URL = "http://localhost:8000/api/v3"


@pytest.fixture(scope="module")
def backend_available() -> None:
    """Skip this integration test quickly if external backend is down."""
    try:
        resp = httpx.get("http://localhost:8000/health", timeout=2.0)
    except Exception:
        pytest.skip("External backend for teacher generate exercise test is not available on /health")

    if resp.status_code != 200:
        pytest.skip("External backend for teacher generate exercise test is not healthy (non-200 /health)")


def test_create_activity_and_generate_exercise(backend_available: None) -> None:
    """Full flow: create activity then generate an exercise for it."""
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        # 1) Create activity
        create_payload = {
            "title": "TP Auto - Generación de Ejercicio",
            "course_id": "1",
            "teacher_id": "1",
            "instructions": "Diseñar un ejercicio simple sobre variables.",
            "policy": "BALANCED",
            "max_ai_help_level": "MEDIO",
        }
        create_resp = client.post("/teacher/activities", json=create_payload)
        assert create_resp.status_code == 201, create_resp.text
        activity = create_resp.json()
        activity_id = activity["activity_id"]

        # 2) Generate exercise for that activity
        gen_payload = {
            "topic": "variables en Python",
            "difficulty": "FACIL",
            "unit_number": 1,
            "language": "python",
            "concepts": ["variables", "tipos de datos"],
            "estimated_time_minutes": 20,
        }
        gen_resp = client.post(f"/teacher/activities/{activity_id}/exercises", json=gen_payload)
        assert gen_resp.status_code == 201, gen_resp.text
        data = gen_resp.json()

        # Basic shape checks
        assert data["title"].startswith("Ejercicio")
        assert data["language"] == "python"
        assert data["difficulty"] == "FACIL"
        assert data["visible_test_count"] >= 1
        assert data["hidden_test_count"] >= 1
        assert len(data["test_cases"]) >= 2
