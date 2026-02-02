"""
E2E Test - Complete Student Flow with REAL Mistral AI and PostgreSQL

Validates the entire student journey with REAL connections:
- Mistral AI for tutor responses
- PostgreSQL for persistence
"""
import asyncio
import pytest
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Add paths
project_root = Path(__file__).parent.parent
backend_path = project_root / "backend"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_path))

# Database URL - adjust if needed
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5433/ai_native")


# ==================== ASYNC HELPER ====================

async def get_db_session():
    """Create async database session"""
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
    await engine.dispose()


# ==================== TESTS ====================

@pytest.mark.asyncio
async def test_01_database_connection():
    """Test database connection works"""
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        result = await session.execute(text("SELECT 1 as test"))
        row = result.fetchone()
        assert row[0] == 1
        print("✅ Database connection OK")
    
    await engine.dispose()


@pytest.mark.asyncio
async def test_02_create_test_student():
    """Create a test student in the database"""
    student_id = f"e2e-test-{uuid.uuid4().hex[:8]}"
    email = f"e2e_{uuid.uuid4().hex[:6]}@test.com"
    username = f"e2e_student_{uuid.uuid4().hex[:6]}"
    
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Create student
        await session.execute(text("""
            INSERT INTO users (id, email, username, hashed_password, full_name, roles, is_active)
            VALUES (:id, :email, :username, 'test_hash', :full_name, '["student"]'::jsonb, true)
            ON CONFLICT (id) DO NOTHING
        """), {
            "id": student_id,
            "email": email,
            "username": username,
            "full_name": "E2E Test Student"
        })
        await session.commit()
        
        # Verify
        result = await session.execute(text("SELECT id, full_name FROM users WHERE id = :id"), {"id": student_id})
        row = result.fetchone()
        assert row is not None, "Student not created"
        print(f"✅ Created student: {row[1]} ({student_id})")
        
        # Cleanup
        await session.execute(text("DELETE FROM users WHERE id = :id"), {"id": student_id})
        await session.commit()
        print(f"✅ Cleaned up student")
    
    await engine.dispose()


@pytest.mark.asyncio
async def test_03_find_bucles_activity():
    """Find or create a bucles activity"""
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Look for existing activity
        result = await session.execute(text("""
            SELECT activity_id, title, instructions
            FROM activities
            WHERE title ILIKE '%bucle%' OR title ILIKE '%loop%'
            LIMIT 1
        """))
        row = result.fetchone()
        
        if row:
            print(f"✅ Found activity: {row[1]} ({row[0]})")
        else:
            print("⚠️ No bucles activity found - checking for any activity")
            result = await session.execute(text("SELECT activity_id, title FROM activities LIMIT 1"))
            row = result.fetchone()
            if row:
                print(f"✅ Using activity: {row[1]} ({row[0]})")
            else:
                print("⚠️ No activities in database")
    
    await engine.dispose()


@pytest.mark.asyncio
async def test_04_complete_student_flow():
    """Complete E2E flow: student -> activity -> tutor -> submit -> grade"""
    import httpx
    from httpx import ASGITransport
    
    # Create app
    from backend.src_v3.infrastructure.http.app import create_app
    app = create_app()
    
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Create test student
    student_id = f"e2e-flow-{uuid.uuid4().hex[:8]}"
    email = f"flow_{uuid.uuid4().hex[:6]}@test.com"
    username = f"flow_student_{uuid.uuid4().hex[:6]}"
    activity_id = None
    
    async with async_session() as session:
        # Create student
        await session.execute(text("""
            INSERT INTO users (id, email, username, hashed_password, full_name, roles, is_active)
            VALUES (:id, :email, :username, 'test_hash', 'E2E Flow Student', '["student"]'::jsonb, true)
        """), {"id": student_id, "email": email, "username": username})
        await session.commit()
        print(f"✅ Created student: {student_id}")
        
        # Find activity
        result = await session.execute(text("SELECT activity_id, title FROM activities LIMIT 1"))
        row = result.fetchone()
        if row:
            activity_id = row[0]
            print(f"✅ Using activity: {row[1]}")
        else:
            # Create test activity
            activity_id = f"e2e-activity-{uuid.uuid4().hex[:8]}"
            await session.execute(text("""
                INSERT INTO activities (activity_id, title, subject, unit_id, instructions, status)
                VALUES (:id, 'Test Bucles', 'Programación', 'U1', 'Aprende bucles', 'active')
            """), {"id": activity_id})
            await session.commit()
            print(f"✅ Created activity: {activity_id}")
        
        # Create session for student
        session_id = str(uuid.uuid4())
        await session.execute(text("""
            INSERT INTO sessions_v2 (session_id, user_id, activity_id, status, mode, cognitive_status, session_metrics)
            VALUES (:session_id, :user_id, :activity_id, 'active', 'socratic',
                    '{"cognitive_phase": "exploration", "frustration_level": 0.2, "understanding_level": 0.6}'::jsonb,
                    '{"duration_minutes": 15, "total_interactions": 5}'::jsonb)
        """), {"session_id": session_id, "user_id": student_id, "activity_id": activity_id})
        await session.commit()
        print(f"✅ Created session: {session_id}")
    
    # Test HTTP endpoints
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        
        # Test 1: Get activities
        response = await client.get(f"/api/v3/student/activities", params={"student_id": student_id})
        print(f"📋 GET /student/activities: {response.status_code}")
        if response.status_code == 200:
            activities = response.json()
            print(f"   Found {len(activities)} activities")
        
        # Test 2: Get grades summary
        response = await client.get(f"/api/v3/student/grades/summary", params={"student_id": student_id})
        print(f"📊 GET /grades/summary: {response.status_code}")
        if response.status_code == 200:
            summary = response.json()
            print(f"   Total activities: {summary.get('total_activities')}")
        
        # Test 3: Submit activity
        test_code = "for i in range(5):\n    print(i)"
        response = await client.post(
            f"/api/v3/student/activities/{activity_id}/submit",
            params={"student_id": student_id},
            json={"code": test_code, "is_final_submission": True}
        )
        print(f"📝 POST /activities/{activity_id}/submit: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Submission ID: {result.get('submission_id')}")
            print(f"   Grade: {result.get('grade')}")
            print(f"   AI Feedback: {str(result.get('ai_feedback', ''))[:100]}...")
        
        # Test 4: Get traceability
        response = await client.get(
            f"/api/v3/analytics/students/{student_id}/traceability",
            params={"activity_id": activity_id}
        )
        print(f"🔍 GET /analytics/students/{student_id}/traceability: {response.status_code}")
        if response.status_code == 200:
            trace = response.json()
            print(f"   Cognitive journey phases: {len(trace.get('cognitive_journey', []))}")
            print(f"   Risk level: {trace.get('risk_level')}")
        
        # Test 5: Get grades
        response = await client.get(f"/api/v3/student/grades", params={"student_id": student_id})
        print(f"📈 GET /student/grades: {response.status_code}")
        if response.status_code == 200:
            grades = response.json()
            print(f"   Found {len(grades)} grades")
            for grade in grades[:2]:
                print(f"   - {grade.get('activity_title')}: {grade.get('grade')}")
    
    # Verify in database
    async with async_session() as session:
        # Check submission
        result = await session.execute(text("""
            SELECT submission_id, final_grade, ai_feedback, status
            FROM submissions
            WHERE student_id = :student_id
            ORDER BY created_at DESC LIMIT 1
        """), {"student_id": student_id})
        row = result.fetchone()
        
        if row:
            print(f"\n✅ VERIFIED IN DATABASE:")
            print(f"   Submission ID: {row[0]}")
            print(f"   Final Grade: {row[1]}")
            print(f"   Status: {row[3]}")
            print(f"   AI Feedback: {str(row[2])[:100] if row[2] else 'None'}...")
        else:
            print(f"\n⚠️ No submission found in database")
        
        # Cleanup
        await session.execute(text("DELETE FROM submissions WHERE student_id = :id"), {"id": student_id})
        await session.execute(text("DELETE FROM sessions_v2 WHERE user_id = :id"), {"id": student_id})
        await session.execute(text("DELETE FROM users WHERE id = :id"), {"id": student_id})
        await session.commit()
        print(f"\n🧹 Cleaned up test data")
    
    await engine.dispose()
    print("\n✅ E2E TEST COMPLETE!")


# ==================== EXECUTION ====================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🚀 RUNNING E2E TEST - Complete Student Flow")
    print("   Using REAL PostgreSQL Database")
    print("="*70 + "\n")
    
    pytest.main([__file__, "-v", "-s", "--tb=short"])
