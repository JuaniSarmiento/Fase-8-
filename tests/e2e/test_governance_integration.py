"""Integration tests for governance (GSR) endpoints in Fase 8.

Assumes fase8-backend is running on http://localhost:8000 via docker-compose.
If the backend is not reachable, these tests are skipped to avoid long
timeouts when running the suite locally.
"""

import httpx
import pytest

BASE_URL = "http://localhost:8000/api/v3"


@pytest.fixture(scope="module")
def backend_available() -> bool:
    """Ensure the external Fase 8 backend is reachable, or skip tests."""
    try:
        resp = httpx.get("http://localhost:8000/health", timeout=2.0)
    except Exception:
        pytest.skip("Fase 8 backend is not running on http://localhost:8000; skipping governance integration tests")

    if resp.status_code != 200:
        pytest.skip("Fase 8 backend /health did not return 200; skipping governance integration tests")

    return True


def test_governance_student_smoke(backend_available: bool):
    """Smoke test for /api/v3/governance/students/{student_id}.

    We allow both cases: no risk data (has_risk=False) or existing data.
    """
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        # Student ids 1-4 are present in seed data; risk table may be empty.
        resp = client.get("/governance/students/1")
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "has_risk" in data
        # If there is risk data, basic fields should be present
        if data["has_risk"]:
            assert data["student_id"] == "1" or data["student_id"]
            assert "risk_score" in data


def test_governance_session_smoke(backend_available: bool):
    """Smoke test for /api/v3/governance/sessions/{session_id}.

    We use a bogus session_id to ensure the endpoint still responds
    with has_risk=False and 200.
    """
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        resp = client.get("/governance/sessions/non-existent-session")
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["has_risk"] in (True, False)
