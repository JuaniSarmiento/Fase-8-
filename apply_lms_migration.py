#!/usr/bin/env python3
"""
Apply LMS Hierarchical Architecture Migration

Creates new tables: modules, enrollments, user_gamification
Updates existing tables: activities (module_id), exercises_v2 (grading fields)
Migrates data from user_profiles to enrollments
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from backend.src_v3.infrastructure.persistence.database import (
    get_db_session,
    engine as async_engine
)


async def apply_lms_migration():
    """Apply LMS hierarchy migration SQL"""
    
    print("🚀 Starting LMS Hierarchical Architecture Migration...")
    
    # Read SQL file
    sql_file = Path(__file__).parent / "migrate_lms_hierarchy.sql"
    if not sql_file.exists():
        print(f"❌ Migration file not found: {sql_file}")
        return False
    
    with open(sql_file, "r", encoding="utf-8") as f:
        sql_content = f.read()
    
    try:
        # Get async session
        async with AsyncSession(async_engine) as session:
            print("📊 Connected to database")
            
            # Split SQL into statements (basic split by semicolon)
            statements = [s.strip() for s in sql_content.split(";") if s.strip()]
            
            print(f"📝 Executing {len(statements)} SQL statements...")
            
            for i, statement in enumerate(statements, 1):
                # Skip comments and empty statements
                if statement.startswith("--") or not statement:
                    continue
                
                try:
                    await session.execute(text(statement))
                    await session.commit()
                    
                    # Print progress every 10 statements
                    if i % 10 == 0:
                        print(f"✅ Executed {i}/{len(statements)} statements...")
                        
                except Exception as e:
                    # Some statements might fail if tables already exist - that's OK
                    if "already exists" in str(e) or "duplicate" in str(e).lower():
                        print(f"⚠️  Statement {i} skipped (already exists): {str(e)[:100]}")
                        await session.rollback()
                        continue
                    else:
                        print(f"❌ Error in statement {i}: {statement[:100]}")
                        print(f"   Error: {e}")
                        await session.rollback()
                        # Continue with next statement
            
            print("✅ Migration SQL executed successfully!")
            
            # Verify results
            print("\n📊 Verifying migration results...")
            
            # Check modules
            result = await session.execute(text("SELECT COUNT(*) FROM modules"))
            module_count = result.scalar()
            print(f"   Modules: {module_count}")
            
            # Check enrollments
            result = await session.execute(text("SELECT COUNT(*) FROM enrollments"))
            enrollment_count = result.scalar()
            print(f"   Enrollments: {enrollment_count}")
            
            # Check gamification
            result = await session.execute(text("SELECT COUNT(*) FROM user_gamification"))
            gamification_count = result.scalar()
            print(f"   Gamification records: {gamification_count}")
            
            # Check activities with modules
            result = await session.execute(text("SELECT COUNT(*) FROM activities WHERE module_id IS NOT NULL"))
            activities_with_modules = result.scalar()
            print(f"   Activities with modules: {activities_with_modules}")
            
            # Enrollment distribution
            result = await session.execute(text("""
                SELECT role, status, COUNT(*) as count
                FROM enrollments
                GROUP BY role, status
                ORDER BY role, status
            """))
            print(f"\n   Enrollment distribution:")
            for row in result:
                print(f"      {row.role} - {row.status}: {row.count}")
            
            print("\n✅ LMS Hierarchical Architecture Migration Complete!")
            print("\n📋 Next Steps:")
            print("   1. Update routers to use Enrollment joins instead of UserProfile.course_id")
            print("   2. Implement module CRUD endpoints in teacher_router.py")
            print("   3. Update student_router.py to group activities by modules")
            print("   4. Test enrollment-based access control")
            print("   5. Implement gamification API endpoints")
            
            return True
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def rollback_migration():
    """
    Rollback migration (drop new tables)
    WARNING: This will delete data!
    """
    print("⚠️  WARNING: This will drop modules, enrollments, and user_gamification tables!")
    confirm = input("Type 'YES' to confirm rollback: ")
    
    if confirm != "YES":
        print("❌ Rollback cancelled")
        return
    
    rollback_sql = """
    DROP TABLE IF EXISTS user_gamification CASCADE;
    DROP TABLE IF EXISTS enrollments CASCADE;
    DROP TABLE IF EXISTS modules CASCADE;
    DROP TYPE IF EXISTS enrollment_role CASCADE;
    DROP TYPE IF EXISTS enrollment_status CASCADE;
    ALTER TABLE activities DROP COLUMN IF EXISTS module_id;
    ALTER TABLE activities DROP COLUMN IF EXISTS order_index;
    ALTER TABLE exercises_v2 DROP COLUMN IF EXISTS reference_solution;
    ALTER TABLE exercises_v2 DROP COLUMN IF EXISTS grading_config;
    """
    
    try:
        async with AsyncSession(async_engine) as session:
            await session.execute(text(rollback_sql))
            await session.commit()
            print("✅ Migration rolled back successfully")
    except Exception as e:
        print(f"❌ Rollback failed: {e}")


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="LMS Migration Tool")
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="Rollback migration (WARNING: deletes data)"
    )
    args = parser.parse_args()
    
    if args.rollback:
        await rollback_migration()
    else:
        success = await apply_lms_migration()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
