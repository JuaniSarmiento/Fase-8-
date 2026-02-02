"""Governance / GSR router - API v3.

Provides a lightweight governance/risk semaphore over the stored
RiskModel records ("risks" table).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.src_v3.infrastructure.persistence.database import get_db_session
from backend.src_v3.infrastructure.persistence.repositories.governance_repository import (
    GovernanceRepository,
)
from backend.src_v3.application.governance.use_cases import (
    GetSessionGovernanceUseCase,
    GetSessionGovernanceCommand,
    GetStudentGovernanceUseCase,
    GetStudentGovernanceCommand,
)
from backend.src_v3.infrastructure.ai.agents import GovernanceAgent
from backend.src_v3.infrastructure.dependencies import get_governance_agent


router = APIRouter(prefix="/governance", tags=["Governance / GSR"])


class GovernanceResponse(BaseModel):
    """Simple response model for governance status."""

    has_risk: bool
    student_id: str | None = None
    session_id: str | None = None
    risk_score: float | None = None
    risk_level: str | None = None
    ai_dependency_score: float | None = None
    ai_dependency_level: str | None = None
    risk_factors: Dict[str, Any] | None = None
    created_at: str | None = None
    ai_analysis: Dict[str, Any] | None = None


async def get_governance_repo(db: AsyncSession = Depends(get_db_session)) -> GovernanceRepository:
    """Provide GovernanceRepository using a single AsyncSession instance."""
    return GovernanceRepository(db)


async def get_session_gov_use_case(
    repo: GovernanceRepository = Depends(get_governance_repo),
) -> GetSessionGovernanceUseCase:
    return GetSessionGovernanceUseCase(repo)


async def get_student_gov_use_case(
    repo: GovernanceRepository = Depends(get_governance_repo),
) -> GetStudentGovernanceUseCase:
    return GetStudentGovernanceUseCase(repo)


async def get_optional_governance_agent() -> Optional[GovernanceAgent]:
    """Dependency wrapper for optional GovernanceAgent.

    Returns ``None`` when the agent is disabled or cannot be
    initialized, so endpoints can degrade gracefully.
    """
    return get_governance_agent()


@router.get("/sessions/{session_id}", response_model=GovernanceResponse)
async def get_session_governance(
    session_id: str,
    use_case: GetSessionGovernanceUseCase = Depends(get_session_gov_use_case),
    agent: Optional[GovernanceAgent] = Depends(get_optional_governance_agent),
):
    """Get latest governance / risk status for a session.

    If no risk data exists for the session, returns has_risk=False.
    """
    try:
        result = await use_case.execute(GetSessionGovernanceCommand(session_id=session_id))

        # Optional AI governance analysis (JSON with risk_level/dimension/evidence/recommendation)
        if agent is not None and result.get("has_risk"):
            session_metrics = {
                "risk_score": result.get("risk_score"),
                "ai_dependency_score": result.get("ai_dependency_score"),
            }
            ai_analysis = await agent.analyze_session(session_metrics, recent_messages=[])
            result["ai_analysis"] = ai_analysis

        return GovernanceResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/students/{student_id}", response_model=GovernanceResponse)
async def get_student_governance(
    student_id: str,
    use_case: GetStudentGovernanceUseCase = Depends(get_student_gov_use_case),
    agent: Optional[GovernanceAgent] = Depends(get_optional_governance_agent),
):
    """Get latest governance / risk status for a student.

    If no risk data exists for the student, returns has_risk=False.
    """
    try:
        result = await use_case.execute(GetStudentGovernanceCommand(student_id=student_id))

        if agent is not None and result.get("has_risk"):
            session_metrics = {
                "risk_score": result.get("risk_score"),
                "ai_dependency_score": result.get("ai_dependency_score"),
            }
            ai_analysis = await agent.analyze_session(session_metrics, recent_messages=[])
            result["ai_analysis"] = ai_analysis

        return GovernanceResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


# ==================== GOVERNANCE CONFIGURATION ====================

class GovernanceConfigResponse(BaseModel):
    """Governance system configuration"""
    ai_dependency_threshold: float
    risk_score_critical_threshold: float
    risk_score_warning_threshold: float
    max_consecutive_ai_hints: int
    frustration_intervention_threshold: float
    auto_notify_teacher: bool
    auto_notify_student: bool
    
    class Config:
        from_attributes = True


class UpdateGovernanceConfigRequest(BaseModel):
    """Request to update governance configuration"""
    ai_dependency_threshold: Optional[float] = None
    risk_score_critical_threshold: Optional[float] = None
    risk_score_warning_threshold: Optional[float] = None
    max_consecutive_ai_hints: Optional[int] = None
    frustration_intervention_threshold: Optional[float] = None
    auto_notify_teacher: Optional[bool] = None
    auto_notify_student: Optional[bool] = None


@router.get("/config", response_model=GovernanceConfigResponse)
async def get_governance_config():
    """
    Obtener configuración actual del sistema de gobernanza.
    
    Muestra los umbrales y políticas actuales.
    Requiere autenticación de profesor o admin.
    """
    # TODO: Implementar lectura desde configuración persistente
    # TODO: Verificar autenticación y rol (teacher/admin)
    
    return GovernanceConfigResponse(
        ai_dependency_threshold=0.8,
        risk_score_critical_threshold=0.75,
        risk_score_warning_threshold=0.5,
        max_consecutive_ai_hints=5,
        frustration_intervention_threshold=0.7,
        auto_notify_teacher=True,
        auto_notify_student=False
    )


@router.put("/config", response_model=GovernanceConfigResponse)
async def update_governance_config(request: UpdateGovernanceConfigRequest):
    """
    Actualizar configuración del sistema de gobernanza.
    
    Permite ajustar umbrales de riesgo sin redeployar.
    Requiere autenticación de admin.
    """
    # TODO: Implementar actualización de configuración
    # TODO: Verificar autenticación y rol de admin
    # TODO: Validar rangos de valores (0.0 a 1.0 para thresholds)
    # TODO: Persistir cambios en base de datos o archivo de configuración
    # TODO: Registrar cambio en audit log
    
    return GovernanceConfigResponse(
        ai_dependency_threshold=request.ai_dependency_threshold or 0.8,
        risk_score_critical_threshold=request.risk_score_critical_threshold or 0.75,
        risk_score_warning_threshold=request.risk_score_warning_threshold or 0.5,
        max_consecutive_ai_hints=request.max_consecutive_ai_hints or 5,
        frustration_intervention_threshold=request.frustration_intervention_threshold or 0.7,
        auto_notify_teacher=request.auto_notify_teacher if request.auto_notify_teacher is not None else True,
        auto_notify_student=request.auto_notify_student if request.auto_notify_student is not None else False
    )


# ==================== INCIDENT REPORTING ====================

class ReportIncidentRequest(BaseModel):
    """Request to report a governance incident"""
    incident_type: str  # hallucination, toxic_response, inappropriate_hint, other
    session_id: Optional[str] = None
    message_id: Optional[str] = None
    description: str
    severity: str = "medium"  # low, medium, high, critical
    reported_by_role: str  # student, teacher, system
    ai_response: Optional[str] = None
    context: Optional[dict] = None


class IncidentResponse(BaseModel):
    """Incident report response"""
    incident_id: str
    incident_type: str
    session_id: Optional[str]
    reported_by: str
    reported_by_role: str
    description: str
    severity: str
    status: str  # pending, reviewed, resolved, dismissed
    created_at: str
    reviewed_at: Optional[str] = None
    resolution: Optional[str] = None
    
    class Config:
        from_attributes = True


@router.post("/incidents/report", response_model=IncidentResponse, status_code=201)
async def report_incident(request: ReportIncidentRequest):
    """
    Reportar un incidente de gobernanza.
    
    Permite a estudiantes o profesores reportar:
    - Alucinaciones de la AI (respuestas incorrectas)
    - Respuestas tóxicas o inapropiadas
    - Hints que revelan demasiado la solución
    - Otros problemas éticos o de calidad
    
    Requiere autenticación.
    """
    # TODO: Implementar registro de incidente
    # TODO: Verificar autenticación del usuario
    # TODO: Validar incident_type contra lista permitida
    # TODO: Crear registro en tabla de incidentes
    # TODO: Notificar a administradores si severity >= high
    # TODO: Si hay message_id, marcar el mensaje para revisión
    
    from datetime import datetime
    import uuid
    
    return IncidentResponse(
        incident_id=str(uuid.uuid4()),
        incident_type=request.incident_type,
        session_id=request.session_id,
        reported_by="mock-user-id",
        reported_by_role=request.reported_by_role,
        description=request.description,
        severity=request.severity,
        status="pending",
        created_at=datetime.now().isoformat(),
        reviewed_at=None,
        resolution=None
    )


@router.get("/incidents", response_model=list[IncidentResponse])
async def list_incidents(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    incident_type: Optional[str] = None,
    limit: int = 50
):
    """
    Listar incidentes reportados.
    
    Filtros opcionales por estado, severidad y tipo.
    Requiere autenticación de admin.
    """
    # TODO: Implementar listado desde repositorio
    # TODO: Verificar autenticación y rol de admin
    # TODO: Aplicar filtros
    # TODO: Ordenar por fecha descendente
    
    return []


@router.put("/incidents/{incident_id}/resolve", response_model=IncidentResponse)
async def resolve_incident(incident_id: str, resolution: str):
    """
    Marcar un incidente como resuelto.
    
    Registra la resolución y actualiza el estado.
    Requiere autenticación de admin.
    """
    # TODO: Implementar actualización de incidente
    # TODO: Verificar autenticación y rol de admin
    # TODO: Validar que el incidente exista
    # TODO: Actualizar status, resolution, reviewed_at
    
    from datetime import datetime
    
    return IncidentResponse(
        incident_id=incident_id,
        incident_type="hallucination",
        session_id=None,
        reported_by="mock-user-id",
        reported_by_role="student",
        description="Mock incident",
        severity="medium",
        status="resolved",
        created_at=datetime.now().isoformat(),
        reviewed_at=datetime.now().isoformat(),
        resolution=resolution
    )
