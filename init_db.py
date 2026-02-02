"""
Script to initialize database tables

Creates all tables defined in SQLAlchemy models.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.src_v3.infrastructure.persistence.database import init_db


async def main():
    """Initialize database tables."""
    print("🔨 Initializing database...")
    
    try:
        await init_db()
        print("✅ Database initialized successfully!")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
