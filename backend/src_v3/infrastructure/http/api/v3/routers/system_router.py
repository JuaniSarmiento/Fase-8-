"""
System Health Router

Provides detailed health information about the application.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from backend.src_v3.infrastructure.config.settings import settings

router = APIRouter(prefix="/system", tags=["System"])


async def get_db_session():
    """Provide AsyncSession using shared database configuration."""
    from backend.src_v3.infrastructure.persistence.database import get_db_session as db_session
    async for session in db_session():
        yield session


@router.get("/health/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db_session)):
    """
    Detailed health check with database connectivity.
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "debug_mode": settings.DEBUG,
        "components": {}
    }
    
    # Check database
    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        health_status["components"]["database"] = {
            "status": "healthy",
            "type": "PostgreSQL"
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check Redis (if configured)
    health_status["components"]["redis"] = {
        "status": "not_configured",
        "url": settings.REDIS_URL
    }
    
    # Check LLM availability
    health_status["components"]["llm"] = {
        "status": "configured" if settings.OPENAI_API_KEY else "not_configured",
        "provider": "OpenAI" if settings.OPENAI_API_KEY else None
    }
    
    return health_status


@router.get("/info")
async def system_info():
    """
    Get system information.
    """
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "architecture": "Clean Architecture + DDD",
        "debug_mode": settings.DEBUG,
        "features": {
            "analytics": True,
            "student_tutor": False,
            "teacher_tools": False,
            "authentication": False
        },
        "configuration": {
            "database": "PostgreSQL",
            "cache": "Redis" if settings.REDIS_URL else None,
            "llm_provider": "OpenAI" if settings.OPENAI_API_KEY else None
        }
    }


@router.get("/stats")
async def system_stats(db: AsyncSession = Depends(get_db_session)):
    """
    Get basic system statistics.
    """
    try:
        # Count users
        result = await db.execute(text("SELECT COUNT(*) FROM users"))
        user_count = result.scalar() or 0

        # Count sessions (v2 schema)
        result = await db.execute(text("SELECT COUNT(*) FROM sessions_v2"))
        session_count = result.scalar() or 0

        # Count exercise attempts (v2 schema)
        result = await db.execute(text("SELECT COUNT(*) FROM exercise_attempts_v2"))
        attempt_count = result.scalar() or 0

        # Count active sessions today (v2 schema)
        result = await db.execute(
            text("SELECT COUNT(*) FROM sessions_v2 WHERE DATE(start_time) = CURRENT_DATE")
        )
        today_sessions = result.scalar() or 0
        
        return {
            "total_users": user_count,
            "total_sessions": session_count,
            "total_attempts": attempt_count,
            "sessions_today": today_sessions,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "error": "Unable to fetch statistics",
            "detail": str(e)
        }
