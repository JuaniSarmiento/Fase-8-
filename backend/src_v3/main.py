"""FastAPI Application - Clean Architecture v3.

Main application setup with dependency injection, metrics and health checks.
"""
import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession

from prometheus_fastapi_instrumentator import Instrumentator

from backend.src_v3.infrastructure.http.api.v3.routers import student_router, teacher_router
from backend.src_v3.infrastructure.http.api.v3.routers import auth_router
from backend.src_v3.infrastructure.http.api.v3.routers import (
    analytics_router,
    system_router,
    governance_router,
    catalog_router,
)
from backend.src_v3.infrastructure.persistence.database import get_db_session
from backend.src_v3.core.rate_limiter import RateLimitMiddleware
from backend.src_v3.core.security_middleware import (
    SecurityHeadersMiddleware,
    SQLInjectionDetector,
    RequestLoggingMiddleware,
    XSSProtectionMiddleware,
)


# ==================== LIFESPAN ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events.
    
    Setup:
    - Database connection
    - LLM clients
    - RAG indexing
    
    Teardown:
    - Close connections
    """
    # Startup
    print("🚀 Starting Fase 8 Backend (Clean Architecture)")
    
    # TODO: Initialize database
    # TODO: Initialize LLM clients
    # TODO: Initialize RAG service
    
    yield
    
    # Shutdown
    print("👋 Shutting down Fase 8 Backend")
    
    # TODO: Close database connections
    # TODO: Close LLM clients


# ==================== APP CREATION ====================

def create_app() -> FastAPI:
    """Create FastAPI application"""
    
    # Get environment
    environment = os.getenv("ENVIRONMENT", "development")
    is_production = environment.lower() == "production"
    
    app = FastAPI(
        title="Fase 8 Backend - Clean Architecture",
        description="AI-Native Learning Platform with Clean Architecture + DDD",
        version="3.0.0",
        lifespan=lifespan,
        # Hide docs in production
        docs_url="/docs" if not is_production else None,
        redoc_url="/redoc" if not is_production else None,
    )
    
    # ==================== SECURITY MIDDLEWARES ====================
    
    # 1. Trusted Host Middleware (prevent host header attacks)
    if is_production:
        allowed_hosts = os.getenv("ALLOWED_HOSTS", "").split(",")
        if allowed_hosts and allowed_hosts[0]:
            app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)
    
    # 2. Security Headers Middleware
    app.add_middleware(SecurityHeadersMiddleware)
    
    # 3. Rate Limiting Middleware
    requests_per_minute = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    requests_per_hour = int(os.getenv("RATE_LIMIT_PER_HOUR", "1000"))
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=requests_per_minute,
        requests_per_hour=requests_per_hour
    )
    
    # 4. SQL Injection Detection
    app.add_middleware(SQLInjectionDetector)
    
    # 5. XSS Protection
    app.add_middleware(XSSProtectionMiddleware)
    
    # 6. Request Logging
    if os.getenv("ENABLE_REQUEST_LOGGING", "true").lower() == "true":
        app.add_middleware(RequestLoggingMiddleware)
    
    # ==================== CORS ====================
    
    # Get allowed origins from environment
    allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001")
    allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",")]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["*"],
        expose_headers=["X-RateLimit-Limit-Minute", "X-RateLimit-Limit-Hour"],
        max_age=3600,  # Cache preflight requests for 1 hour
    )
    
    # Routers
    app.include_router(student_router.router, prefix="/api/v3")
    app.include_router(teacher_router.router, prefix="/api/v3")
    app.include_router(auth_router.router, prefix="/api/v3")
    app.include_router(analytics_router.router, prefix="/api/v3")
    app.include_router(system_router.router, prefix="/api/v3")
    app.include_router(governance_router.router, prefix="/api/v3")
    app.include_router(catalog_router.router, prefix="/api/v3")

    # Prometheus metrics (/metrics)
    Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
    
    @app.get("/health")
    async def health_check(db: AsyncSession = Depends(get_db_session)):
        """Health check endpoint with basic dependency checks.

        Currently verifies:
        - Application is up
        - Database is reachable (simple SELECT 1)
        """
        db_ok = True
        try:
            await db.execute("SELECT 1")
        except Exception:
            db_ok = False

        status = "healthy" if db_ok else "degraded"

        return {
            "status": status,
            "version": "3.0.0",
            "architecture": "Clean Architecture + DDD",
            "checks": {
                "database": "ok" if db_ok else "error",
            },
        }
    
    return app


# ==================== APP INSTANCE ====================

app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend.src_v3.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
