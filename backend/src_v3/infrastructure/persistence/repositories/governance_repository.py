"""Governance repository: risk/governance data access.

Uses RiskModel ("risks" table) as source of governance assessments
for sessions and students.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Any

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import ProgrammingError

from backend.src_v3.infrastructure.persistence.sqlalchemy.models.risk_model import RiskModel


@dataclass
class GovernanceRecord:
    """Simple data structure for governance/risk assessment."""

    id: str
    student_id: str
    session_id: Optional[str]
    risk_score: float
    risk_factors: Dict[str, Any]
    created_at: Any

    @property
    def ai_dependency_score(self) -> float:
        """Return AI dependency score as 0-100 percentage if available."""

        raw = self.risk_factors.get("ai_dependency_score", 0.0) if self.risk_factors else 0.0
        try:
            val = float(raw)
        except (TypeError, ValueError):
            return 0.0

        # If stored in 0-1 range, convert to 0-100
        if 0.0 <= val <= 1.0:
            return val * 100.0
        return max(0.0, min(val, 100.0))


class GovernanceRepository:
    """Repository wrapping access to RiskModel for governance use cases."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_latest_for_session(self, session_id: str) -> Optional[GovernanceRecord]:
        stmt = (
            select(RiskModel)
            .where(RiskModel.session_id == session_id)
            .order_by(desc(RiskModel.created_at))
            .limit(1)
        )
        try:
            result = await self.session.execute(stmt)
        except ProgrammingError as exc:
            # In environments where the legacy 'risks' table does not exist yet,
            # we treat this as "no governance data" instead of failing with 500.
            if 'relation "risks" does not exist' in str(exc):
                return None
            raise

        model: Optional[RiskModel] = result.scalar_one_or_none()
        if not model:
            return None

        return GovernanceRecord(
            id=model.id,
            student_id=model.student_id,
            session_id=model.session_id,
            risk_score=float(model.risk_score),
            risk_factors=model.risk_factors or {},
            created_at=model.created_at,
        )

    async def get_latest_for_student(self, student_id: str) -> Optional[GovernanceRecord]:
        stmt = (
            select(RiskModel)
            .where(RiskModel.student_id == student_id)
            .order_by(desc(RiskModel.created_at))
            .limit(1)
        )
        try:
            result = await self.session.execute(stmt)
        except ProgrammingError as exc:
            if 'relation "risks" does not exist' in str(exc):
                return None
            raise

        model: Optional[RiskModel] = result.scalar_one_or_none()
        if not model:
            return None

        return GovernanceRecord(
            id=model.id,
            student_id=model.student_id,
            session_id=model.session_id,
            risk_score=float(model.risk_score),
            risk_factors=model.risk_factors or {},
            created_at=model.created_at,
        )
