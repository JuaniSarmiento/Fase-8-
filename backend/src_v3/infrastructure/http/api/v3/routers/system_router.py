"""
System Health Router

Provides detailed health information about the application.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from pydantic import BaseModel
from typing import List

from backend.src_v3.infrastructure.config.settings import settings
from backend.src_v3.infrastructure.cache.decorators import cached

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/system", tags=["System"])


class UpdateRolesRequest(BaseModel):
    roles: List[str]


async def get_db_session():
    """Provide AsyncSession using shared database configuration."""
    from backend.src_v3.infrastructure.persistence.database import get_db_session as db_session
    async for session in db_session():
        yield session


@router.get("/health/detailed")
async def detailed_health_check(
    request: Request,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Detailed health check with database and Redis connectivity.
    """
    logger.info("🏥 Performing detailed health check...")
    
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
        logger.debug("🔍 Checking database connection...")
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        health_status["components"]["database"] = {
            "status": "healthy",
            "type": "PostgreSQL"
        }
        logger.info("✅ Database: healthy")
    except Exception as e:
        logger.error(f"❌ Database: unhealthy - {e}")
        health_status["status"] = "unhealthy"
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check Redis
    try:
        logger.debug("🔍 Checking Redis connection...")
        from backend.src_v3.infrastructure.cache import get_redis_cache
        redis_cache = await get_redis_cache()
        
        if await redis_cache.is_healthy():
            stats = await redis_cache.get_stats()
            health_status["components"]["redis"] = {
                "status": "healthy",
                "url": settings.REDIS_URL,
                "connected_clients": stats.get("connected_clients"),
                "used_memory": stats.get("used_memory_human"),
                "hit_rate": stats.get("hit_rate")
            }
            logger.info(f"✅ Redis: healthy (hit_rate: {stats.get('hit_rate')})")
        else:
            health_status["status"] = "degraded"
            health_status["components"]["redis"] = {
                "status": "unhealthy",
                "url": settings.REDIS_URL
            }
            logger.warning("⚠️  Redis: unhealthy")
    except Exception as e:
        logger.error(f"❌ Redis: error - {e}")
        health_status["status"] = "degraded"
        health_status["components"]["redis"] = {
            "status": "error",
            "error": str(e),
            "url": settings.REDIS_URL
        }
    
    # Check LLM availability
    health_status["components"]["llm"] = {
        "status": "configured" if settings.OPENAI_API_KEY else "not_configured",
        "provider": "OpenAI" if settings.OPENAI_API_KEY else None
    }
    
    logger.info(f"🏥 Health check complete: {health_status['status']}")
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
@cached(ttl=30)  # Cache for 30 seconds
async def system_stats(
    request: Request,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get basic system statistics (cached for 30 seconds).
    """
    logger.info("📊 Fetching system statistics...")
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
        
        stats = {
            "total_users": user_count,
            "total_sessions": session_count,
            "total_attempts": attempt_count,
            "sessions_today": today_sessions,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"✅ Statistics retrieved: {user_count} users, {session_count} sessions")
        return stats
    except Exception as e:
        logger.error(f"❌ Error fetching statistics: {e}")
        return {
            "error": "Unable to fetch statistics",
            "detail": str(e)
        }


@router.get("/redis/stats")
async def redis_stats(request: Request):
    """
    Get detailed Redis statistics and metrics.
    """
    logger.info("📊 Fetching Redis statistics...")
    try:
        from backend.src_v3.infrastructure.cache import get_redis_cache
        redis_cache = await get_redis_cache()
        
        stats = await redis_cache.get_stats()
        logger.info(f"✅ Redis stats retrieved: {stats.get('hit_rate', 'N/A')} hit rate")
        
        return {
            "status": "success",
            "redis_stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Error fetching Redis stats: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.post("/redis/test")
async def test_redis(request: Request):
    """
    Test Redis connectivity by setting and getting a test value.
    """
    logger.info("🧪 Testing Redis operations...")
    try:
        from backend.src_v3.infrastructure.cache import get_redis_cache
        redis_cache = await get_redis_cache()
        
        test_key = "test:redis:connection"
        test_value = {"timestamp": datetime.utcnow().isoformat(), "test": "success"}
        
        # Set value
        logger.debug(f"💾 Setting test value in Redis: {test_key}")
        set_result = await redis_cache.set(test_key, test_value, ttl=60)
        
        # Get value
        logger.debug(f"🔍 Getting test value from Redis: {test_key}")
        get_result = await redis_cache.get(test_key)
        
        # Delete value
        logger.debug(f"🗑️  Deleting test value from Redis: {test_key}")
        del_result = await redis_cache.delete(test_key)
        
        logger.info("✅ Redis test completed successfully")
        
        return {
            "status": "success",
            "operations": {
                "set": set_result,
                "get": get_result,
                "delete": del_result
            },
            "message": "Redis is working correctly",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Redis test failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Redis test failed",
            "timestamp": datetime.utcnow().isoformat()
        }


@router.put("/users/{user_id}/roles")
async def update_user_roles(
    user_id: str,
    request: UpdateRolesRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Update user roles. Allows self-registration of teachers.
    """
    try:
        # Validate roles
        valid_roles = ['student', 'teacher', 'admin', 'ta', 'observer']
        for role in request.roles:
            if role.lower() not in valid_roles:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid role: {role}. Valid roles are: {', '.join(valid_roles)}"
                )
        
        # Update user roles
        update_query = text("""
            UPDATE users 
            SET roles = :roles, updated_at = NOW()
            WHERE id = :user_id
            RETURNING id, username, email, roles
        """)
        
        result = await db.execute(
            update_query,
            {"user_id": user_id, "roles": request.roles}
        )
        await db.commit()
        
        updated_user = result.fetchone()
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {
            "message": "Roles updated successfully",
            "user_id": updated_user.id,
            "username": updated_user.username,
            "email": updated_user.email,
            "roles": updated_user.roles
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update roles: {str(e)}"
        )
