"""Integration tests for analytics and system endpoints in Fase 8.

Assumes fase8-backend is running on http://localhost:8000 via docker-compose.
If the backend is not reachable, these tests are skipped quickly to
avoid long timeouts during the local test run.
"""

import httpx
import pytest

BASE_URL = "http://localhost:8000"


@pytest.fixture(scope="module")
def backend_available() -> bool:
    """Ensure the external Fase 8 backend is reachable, or skip tests.

    This prevents long ReadTimeouts when the docker-compose stack is
    not running on localhost:8000.
    """
    try:
        resp = httpx.get(f"{BASE_URL}/health", timeout=2.0)
    except Exception:
        pytest.skip("Fase 8 backend is not running on http://localhost:8000; skipping integration tests")

    if resp.status_code != 200:
        pytest.skip("Fase 8 backend /health did not return 200; skipping integration tests")

    return True


def test_system_info_and_stats(backend_available: bool):
    """Smoke test for /api/v3/system/info and /api/v3/system/stats."""
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        info_resp = client.get("/api/v3/system/info")
        assert info_resp.status_code == 200, info_resp.text
        data = info_resp.json()
        assert data["app_name"]
        assert data["architecture"].startswith("Clean Architecture")

        stats_resp = client.get("/api/v3/system/stats")
        assert stats_resp.status_code == 200, stats_resp.text
        stats = stats_resp.json()
        # We just check basic keys exist; counts may be zero on fresh DB
        assert "total_users" in stats
        assert "total_sessions" in stats
        assert "total_attempts" in stats
        assert "sessions_today" in stats


def test_course_analytics_smoke(backend_available: bool):
    """Smoke test for /api/v3/analytics/courses/{course_id}.

    Uses a simple course_id that should exist in the seeded data.
    We use course_id=1 as default for now.
    """
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        # Depending on data, you may need to adjust the course_id
        resp = client.get("/api/v3/analytics/courses/1")
        assert resp.status_code in (200, 404), resp.text
        # If 200, validate basic structure
        if resp.status_code == 200:
            data = resp.json()
            assert "course_id" in data
            assert "total_students" in data
            assert "students" in data
