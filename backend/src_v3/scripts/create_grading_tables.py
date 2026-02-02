"""
Database Migration: Create Submission and GradeAudit Tables

Run this script to create the necessary tables for the grading system.

Usage:
    python -m backend.src_v3.scripts.create_grading_tables
"""
import asyncio
import logging
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Import models
from backend.src_v3.infrastructure.persistence.sqlalchemy.models.submission_model import (
    SubmissionModel,
    GradeAuditModel
)
from backend.src_v3.infrastructure.persistence.sqlalchemy.models.exercise_model import ExerciseModel
from backend.src_v3.infrastructure.persistence.database import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load DATABASE_URL from environment
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@127.0.0.1:5433/ai_native")
logger.info(f"Using DATABASE_URL: postgresql+asyncpg://postgres:***@...")

# Create engine for migration
engine = create_async_engine(DATABASE_URL, echo=False)


async def create_tables():
    """Create submission, grade_audit, and exercises tables"""
    try:
        logger.info("Creating tables: submissions, grade_audits, exercises...")
        
        async with engine.begin() as conn:
            # Create tables using SQLAlchemy metadata
            await conn.run_sync(Base.metadata.create_all, tables=[
                ExerciseModel.__table__,
                SubmissionModel.__table__,
                GradeAuditModel.__table__
            ])
        
        logger.info("✅ Tables created successfully!")
        
        # Verify tables exist
        async with engine.connect() as conn:
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('submissions', 'grade_audits', 'exercises')
                ORDER BY table_name
            """))
            
            tables = [row[0] for row in result]
            logger.info(f"Verified tables: {tables}")
            
            if len(tables) >= 2:
                logger.info("✅ Migration completed successfully!")
            else:
                logger.warning(f"⚠️ Expected 3 tables, found {len(tables)}")
    
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}", exc_info=True)
        raise


async def drop_tables():
    """Drop submission and grade_audit tables (for rollback)"""
    try:
        logger.warning("⚠️ Dropping submission and grade_audit tables...")
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all, tables=[
                GradeAuditModel.__table__,  # Drop child table first (foreign key)
                SubmissionModel.__table__
            ])
        
        logger.info("✅ Tables dropped successfully!")
    
    except Exception as e:
        logger.error(f"❌ Drop failed: {e}", exc_info=True)
        raise


async def show_table_info():
    """Show table structure"""
    try:
        async with engine.connect() as conn:
            # Show submissions table structure
            result = await conn.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'submissions'
                ORDER BY ordinal_position
            """))
            
            logger.info("\\n=== SUBMISSIONS TABLE ===")
            for row in result:
                logger.info(f"  {row[0]}: {row[1]} {'NULL' if row[2] == 'YES' else 'NOT NULL'}")
            
            # Show grade_audits table structure
            result = await conn.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'grade_audits'
                ORDER BY ordinal_position
            """))
            
            logger.info("\\n=== GRADE_AUDITS TABLE ===")
            for row in result:
                logger.info(f"  {row[0]}: {row[1]} {'NULL' if row[2] == 'YES' else 'NOT NULL'}")
    
    except Exception as e:
        logger.error(f"❌ Failed to show table info: {e}", exc_info=True)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "drop":
        # Drop tables
        asyncio.run(drop_tables())
    elif len(sys.argv) > 1 and sys.argv[1] == "info":
        # Show table info
        asyncio.run(show_table_info())
    else:
        # Create tables (default)
        asyncio.run(create_tables())
        asyncio.run(show_table_info())
