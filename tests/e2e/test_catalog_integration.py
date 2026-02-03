"""Integration tests for Catalog API v3.

These tests assume the FastAPI app is running on localhost:8000
(via docker compose or uvicorn) and the test data loader has populated
subjects, courses and commissions.
"""
import os

import httpx
import pytest

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")


@pytest.fixture(scope="module")
def backend_available() -> None:
    """Skip catalog integration tests quickly if external backend is down."""
    try:
        resp = httpx.get(f"{BASE_URL}/health", timeout=2.0)
    except Exception:
        pytest.skip("External backend for catalog tests is not available on /health")

    if resp.status_code != 200:
        pytest.skip("External backend for catalog tests is not healthy (non-200 /health)")


def test_list_subjects_smoke(backend_available: None) -> None:
    response = httpx.get(f"{BASE_URL}/api/v3/catalog/subjects", timeout=10.0)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        first = data[0]
        assert "id" in first
        assert "code" in first
        assert "name" in first


def test_list_courses_for_subject_smoke(backend_available: None) -> None:
    subjects_resp = httpx.get(f"{BASE_URL}/api/v3/catalog/subjects", timeout=10.0)
    assert subjects_resp.status_code == 200
    subjects = subjects_resp.json()
    if not subjects:
        return

    subject_id = subjects[0]["id"]
    response = httpx.get(
        f"{BASE_URL}/api/v3/catalog/subjects/{subject_id}/courses",
        timeout=10.0,
    )
    assert response.status_code == 200
    courses = response.json()
    assert isinstance(courses, list)
    if courses:
        course = courses[0]
        assert course["subject_id"] == subject_id


def test_list_commissions_for_course_smoke(backend_available: None) -> None:
    subjects_resp = httpx.get(f"{BASE_URL}/api/v3/catalog/subjects", timeout=10.0)
    assert subjects_resp.status_code == 200
    subjects = subjects_resp.json()
    if not subjects:
        return

    subject_id = subjects[0]["id"]
    courses_resp = httpx.get(
        f"{BASE_URL}/api/v3/catalog/subjects/{subject_id}/courses",
        timeout=10.0,
    )
    assert courses_resp.status_code == 200
    courses = courses_resp.json()
    if not courses:
        return

    course_id = courses[0]["id"]
    response = httpx.get(
        f"{BASE_URL}/api/v3/catalog/courses/{course_id}/commissions",
        timeout=10.0,
    )
    assert response.status_code == 200
    commissions = response.json()
    assert isinstance(commissions, list)
    if commissions:
        cm = commissions[0]
        assert cm["course_id"] == course_id
