"""
Database Configuration and Session Management

Async SQLAlchemy setup for PostgreSQL.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator

import os

# Database URL (from env or default to postgres:postgres@localhost:5433)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5433/ai_native"
)

# Engine
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Log SQL queries
    future=True,
    pool_size=10,
    max_overflow=20,
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base for models (already imported in models)
Base = declarative_base()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI to get database session.
    
    Usage in routers:
        async def endpoint(db: AsyncSession = Depends(get_db_session)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db_health() -> str:
    """
    Check database health status.
    
    Returns:
        "ok" if database is healthy, "error" otherwise
    """
    try:
        from sqlalchemy import text
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            return "ok"
    except Exception as e:
        return "error"


async def init_db():
    """
    Initialize database tables.
    
    Creates all tables defined in models.
    """
    from backend.src_v3.infrastructure.persistence.sqlalchemy.simple_models import (
        Base,
        UserModel,
        SubjectModel,
        CourseModel,
        CommissionModel,
        UserProfileModel,
        ActivityModel,
        SessionModelV2,
        ExerciseModelV2,
        ExerciseAttemptModelV2,
        CognitiveTraceModelV2,
        RiskModelV2,
    )
    
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ Database tables created successfully")


async def drop_all_tables():
    """
    Drop all tables (use with caution!).
    
    For development/testing only.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    print("🗑️ All tables dropped")


if __name__ == "__main__":
    import asyncio
    
    async def main():
        print("Creating database tables...")
        await init_db()
    
    asyncio.run(main())
