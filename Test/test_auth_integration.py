"""Integration test for auth endpoints in Fase 8.

This test assumes the Fase 8 backend is running on http://localhost:8000
using docker-compose (service fase8-backend). If not running, the test
is skipped quickly to avoid long timeouts.
"""

import httpx
import pytest


BASE_URL = "http://localhost:8000"


@pytest.fixture(scope="module")
def backend_available() -> bool:
    """Ensure external auth backend is reachable, or skip test."""
    try:
        resp = httpx.get(f"{BASE_URL}/health", timeout=2.0)
    except Exception:
        pytest.skip("Auth backend is not running on http://localhost:8000; skipping auth integration test")

    if resp.status_code != 200:
        pytest.skip("Auth backend /health did not return 200; skipping auth integration test")

    return True


def test_auth_login_and_me_flow(backend_available: bool):
    """End-to-end test for /api/v3/auth/login and /api/v3/auth/me.

    Uses seeded users in the fase8 Postgres DB. We expect that user with
    email martinez@example.com and password password123 exists (id=1, role teacher).
    """

    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        # 1) Login
        login_payload = {
            "email": "martinez@example.com",
            "password": "password123",
        }
        login_response = client.post("/api/v3/auth/login", json=login_payload)

        assert login_response.status_code == 200, login_response.text
        login_data = login_response.json()

        assert "tokens" in login_data
        access_token = login_data["tokens"]["access_token"]
        assert access_token

        # 2) Call /auth/me with Bearer token
        headers = {"Authorization": f"Bearer {access_token}"}
        me_response = client.get("/api/v3/auth/me", headers=headers)

        assert me_response.status_code == 200, me_response.text
        me_data = me_response.json()

        assert me_data["email"] == "martinez@example.com"
        assert me_data["is_active"] is True
        # At least one role (e.g. ["teacher"]) should be present
        assert isinstance(me_data.get("roles"), list)
        assert len(me_data["roles"]) >= 1
