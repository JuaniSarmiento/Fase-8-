"""Governance use cases: expose GSR / risk semaphore."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Any

from backend.src_v3.infrastructure.persistence.repositories.governance_repository import (
    GovernanceRepository,
    GovernanceRecord,
)


@dataclass
class GetSessionGovernanceCommand:
    session_id: str


@dataclass
class GetStudentGovernanceCommand:
    student_id: str


def _level_from_score(score: float) -> str:
    """Map numeric risk score (0-100) to level string."""

    if score <= 40.0:
        return "low"
    if score <= 60.0:
        return "medium"
    return "high"


class GetSessionGovernanceUseCase:
    """Return latest governance/risk info for a session."""

    def __init__(self, repo: GovernanceRepository) -> None:
        self.repo = repo

    async def execute(self, command: GetSessionGovernanceCommand) -> Dict[str, Any]:
        if not command.session_id:
            raise ValueError("session_id is required")

        record: Optional[GovernanceRecord] = await self.repo.get_latest_for_session(
            command.session_id
        )

        if not record:
            return {
                "has_risk": False,
                "session_id": command.session_id,
            }

        ai_dep = record.ai_dependency_score
        return {
            "has_risk": True,
            "id": record.id,
            "student_id": record.student_id,
            "session_id": record.session_id,
            "risk_score": record.risk_score,
            "risk_level": _level_from_score(record.risk_score),
            "ai_dependency_score": ai_dep,
            "ai_dependency_level": _level_from_score(ai_dep),
            "risk_factors": record.risk_factors,
            "created_at": record.created_at.isoformat() if record.created_at else None,
        }


class GetStudentGovernanceUseCase:
    """Return latest governance/risk info for a student (all sessions)."""

    def __init__(self, repo: GovernanceRepository) -> None:
        self.repo = repo

    async def execute(self, command: GetStudentGovernanceCommand) -> Dict[str, Any]:
        if not command.student_id:
            raise ValueError("student_id is required")

        record: Optional[GovernanceRecord] = await self.repo.get_latest_for_student(
            command.student_id
        )

        if not record:
            return {
                "has_risk": False,
                "student_id": command.student_id,
            }

        ai_dep = record.ai_dependency_score
        return {
            "has_risk": True,
            "id": record.id,
            "student_id": record.student_id,
            "session_id": record.session_id,
            "risk_score": record.risk_score,
            "risk_level": _level_from_score(record.risk_score),
            "ai_dependency_score": ai_dep,
            "ai_dependency_level": _level_from_score(ai_dep),
            "risk_factors": record.risk_factors,
            "created_at": record.created_at.isoformat() if record.created_at else None,
        }
