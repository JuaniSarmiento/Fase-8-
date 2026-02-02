"""
Test completo de creación de actividad con AI
"""
import sys
sys.path.insert(0, '/app')

from backend.src_v3.infrastructure.ai.db_persistence import publish_exercises_to_db
from backend.src_v3.infrastructure.persistence.sqlalchemy.models.activity_model import ActivityModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import asyncio

async def test_activity_creation():
    # Crear sesión de BD
    engine = create_async_engine("postgresql+asyncpg://postgres:postgres@ai_native_postgres:5432/ai_native")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Datos de prueba
        exercises = [
            {
                "title": "Ejercicio 1",
                "description": "Descripción del ejercicio 1",
                "mission_markdown": "# Misión\nResuelve esto",
                "starter_code": "# Tu código aquí",
                "solution_code": "print('Solución')",
                "difficulty": "facil",
                "test_cases": []
            }
        ]
        
        try:
            result = await publish_exercises_to_db(
                db_session=session,
                teacher_id="teacher-001",
                course_id=None,
                approved_exercises=exercises,
                activity_title="Test Activity",
                activity_description="Test Description",
                module_id="701c7617-75ea-4caa-89f9-a541f213e03a"
            )
            
            print(f"✅ SUCCESS! Activity created: {result['activity_id']}")
            print(f"   - Title: {result['activity_title']}")
            print(f"   - Exercises: {result['exercise_count']}")
            
            # Verificar en BD
            from sqlalchemy import select
            stmt = select(ActivityModel).where(ActivityModel.activity_id == result['activity_id'])
            db_activity = await session.execute(stmt)
            activity = db_activity.scalar_one_or_none()
            
            if activity:
                print(f"   - Verified in DB: module_id={activity.module_id}")
            else:
                print("   ⚠️ Activity not found in DB")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_activity_creation())
