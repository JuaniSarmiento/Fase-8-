"""Routers package for API v3."""

from . import (
    student_router,
    teacher_router,
    auth_router,
    analytics_router,
    system_router,
    governance_router,
    catalog_router,
    admin_router,
    enrollments_router,
    notifications_router,
)

__all__ = [
    "student_router",
    "teacher_router",
    "auth_router",
    "analytics_router",
    "system_router",
    "governance_router",
    "catalog_router",
    "admin_router",
    "enrollments_router",
    "notifications_router",
]
