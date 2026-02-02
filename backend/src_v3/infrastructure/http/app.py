"""
FastAPI Application Factory

Creates and configures the FastAPI app with all routers and middleware.
"""
import logging

# Setup enhanced logging FIRST
from ..logging_config import setup_logging
setup_logging()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager

from ..persistence.sqlalchemy.database import async_engine
from ..persistence.database import AsyncSessionLocal
from ..persistence.sqlalchemy.models.user_model import UserModel
from ..persistence.sqlalchemy.models.session_model import SessionModel
from ..persistence.sqlalchemy.models.exercise_attempt_model import ExerciseAttemptModel
from ..persistence.sqlalchemy.models.risk_model import RiskModel
from ..persistence.sqlalchemy.models.exercise_model import ExerciseModel
# Import ActivityModel from simple_models (the correct one) via __init__
from ..persistence.sqlalchemy.models import ActivityModel, CourseModel
from ..persistence.sqlalchemy.models.cognitive_trace_model import CognitiveTraceModel
from ..config.settings import settings
from .api.middleware.error_handler import (
    domain_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    generic_exception_handler
)
from backend.src_v3.core.domain.exceptions import DomainException

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting AI-Native MVP V3 (Clean Architecture)")
    logger.info("Initializing database connection...")
    
    # Note: Tables should be created via Alembic migrations
    # This is just for development
    # from ..persistence.sqlalchemy.database import Base
    # async with async_engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    await async_engine.dispose()


def create_app() -> FastAPI:
    """
    Application factory.
    
    Creates and configures FastAPI app with:
    - CORS middleware
    - Error handlers
    - API routers
    - Health check endpoints
    
    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title=settings.APP_NAME,
        description="Clean Architecture + DDD Implementation",
        version=settings.APP_VERSION,
        docs_url="/api/v3/docs",
        redoc_url="/api/v3/redoc",
        openapi_url="/api/v3/openapi.json",
        lifespan=lifespan,
        debug=settings.DEBUG
    )
    
    # ==================== CORS Configuration ====================
    # SECURITY: Only allow specific origins and methods
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],  # Explicit methods only
        allow_headers=["*"],
    )
    
    # ==================== Exception Handlers ====================
    app.add_exception_handler(DomainException, domain_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
    
    # ==================== Routers ====================
    from .api.v3.routers.analytics_router import router as analytics_router
    from .api.v3.routers.system_router import router as system_router
    from .api.v3.routers.student_router import router as student_router
    from .api.v3.routers.teacher_router import router as teacher_router
    from .api.v3.routers.auth_router import router as auth_router
    from .api.v3.routers.catalog_router import router as catalog_router
    from .api.v3.routers.governance_router import router as governance_router
    from .api.v3.routers.admin_router import router as admin_router
    from .api.v3.routers.enrollments_router import router as enrollments_router
    from .api.v3.routers.notifications_router import router as notifications_router
    
    app.include_router(analytics_router, prefix="/api/v3")
    app.include_router(system_router, prefix="/api/v3")
    app.include_router(student_router, prefix="/api/v3")
    app.include_router(teacher_router, prefix="/api/v3")
    app.include_router(auth_router, prefix="/api/v3")
    app.include_router(catalog_router, prefix="/api/v3")
    app.include_router(governance_router, prefix="/api/v3")
    app.include_router(admin_router, prefix="/api/v3")
    app.include_router(enrollments_router, prefix="/api/v3")
    app.include_router(notifications_router, prefix="/api/v3")
    
    # ==================== Health Check ====================
    @app.get("/health")
    async def health_check():
        """
        Health check endpoint for monitoring.
        """
        try:
            from sqlalchemy import text
            from backend.src_v3.infrastructure.persistence.database import AsyncSessionLocal as SessionLocal
            
            async with SessionLocal() as session:
                await session.execute(text("SELECT 1"))
                db_status = "ok"
        except Exception as e:
            db_status = f"error: {str(e)[:50]}"
        
        status = "healthy" if db_status == "ok" else "degraded"
        
        return {
            "status": status,
            "version": settings.APP_VERSION,
            "architecture": "Clean Architecture + DDD",
            "checks": {
                "database": db_status
            }
        }
    
    @app.get("/")
    async def root():
        """
        Root endpoint.
        """
        return {
            "message": f"{settings.APP_NAME} - Clean Architecture",
            "version": settings.APP_VERSION,
            "docs": "/api/v3/docs",
            "health": "/health",
            "endpoints": {
                "analytics": "/api/v3/analytics",
                "system": "/api/v3/system"
            }
        }
    
    logger.info("Application created successfully")
    return app
