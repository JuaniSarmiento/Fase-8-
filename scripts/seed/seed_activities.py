"""
Seed script to add test activities to the database
"""
import asyncio
import uuid
import sys
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Fix encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Database connection
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5433/ai_native"

async def seed_activities():
    """Add test activities to the database"""
    
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            # First, get the teacher user ID
            result = await session.execute(
                text("SELECT id FROM users WHERE email = 'docente@test.com' LIMIT 1")
            )
            teacher_row = result.fetchone()
            
            if not teacher_row:
                print("❌ Teacher user not found! Run seed_users.py first.")
                return
            
            teacher_id = teacher_row[0]
            print(f"✅ Found teacher: {teacher_id}")
            
            # Get or create a test subject and course
            result = await session.execute(
                text("SELECT code FROM subjects LIMIT 1")
            )
            subject_row = result.fetchone()
            
            if subject_row:
                subject_code = subject_row[0]
                print(f"✅ Using existing subject: {subject_code}")
            else:
                # Create a test subject
                subject_code = "PROG101"
                await session.execute(
                    text("""
                        INSERT INTO subjects (code, name, description, credits, semester, is_active)
                        VALUES (:code, :name, :description, :credits, :semester, :is_active)
                    """),
                    {
                        "code": subject_code,
                        "name": "Programación Python",
                        "description": "Curso de introducción a Python",
                        "credits": 6,
                        "semester": 1,
                        "is_active": True
                    }
                )
                print(f"✅ Created subject: {subject_code}")
            
            result = await session.execute(
                text("SELECT course_id FROM courses LIMIT 1")
            )
            course_row = result.fetchone()
            
            if course_row:
                course_id = course_row[0]
                print(f"✅ Using existing course: {course_id}")
            else:
                # Create a test course
                course_id = str(uuid.uuid4())
                await session.execute(
                    text("""
                        INSERT INTO courses (course_id, subject_code, academic_year, academic_period, is_active, created_at)
                        VALUES (:course_id, :subject_code, :academic_year, :academic_period, :is_active, NOW())
                    """),
                    {
                        "course_id": course_id,
                        "subject_code": subject_code,
                        "academic_year": 2026,
                        "academic_period": "1C",
                        "is_active": True
                    }
                )
                print(f"✅ Created course: {course_id}")
            
            # Check if activities already exist
            result = await session.execute(text("SELECT COUNT(*) FROM activities"))
            count = result.scalar()
            
            if count > 0:
                print(f"⚠️  Database already has {count} activities. Skipping seed.")
                return
            
            # Create test activities
            activities = [
                {
                    "activity_id": str(uuid.uuid4()),
                    "title": "Introducción a Variables y Tipos de Datos",
                    "instructions": "En esta actividad aprenderás sobre variables, tipos de datos básicos en Python (int, float, str, bool), y operaciones básicas.",
                    "course_id": course_id,
                    "teacher_id": teacher_id,
                    "status": "published",
                    "difficulty": "FACIL",
                    "estimated_duration_minutes": 45,
                    "max_score": 10.0,
                    "passing_score": 6.0,
                    "is_published": True,
                    "published_at": datetime.now() - timedelta(days=5),
                },
                {
                    "activity_id": str(uuid.uuid4()),
                    "title": "Control de Flujo: If, Else, Elif",
                    "instructions": "Practica estructuras condicionales en Python. Aprende a usar if, else, elif, y operadores de comparación.",
                    "course_id": course_id,
                    "teacher_id": teacher_id,
                    "status": "published",
                    "difficulty": "FACIL",
                    "estimated_duration_minutes": 60,
                    "max_score": 10.0,
                    "passing_score": 6.0,
                    "is_published": True,
                    "published_at": datetime.now() - timedelta(days=3),
                },
                {
                    "activity_id": str(uuid.uuid4()),
                    "title": "Bucles: For y While",
                    "instructions": "Domina los bucles en Python: for loops, while loops, break, continue. Incluye ejercicios con rangos y listas.",
                    "course_id": course_id,
                    "teacher_id": teacher_id,
                    "status": "published",
                    "difficulty": "INTERMEDIO",
                    "estimated_duration_minutes": 90,
                    "max_score": 10.0,
                    "passing_score": 6.0,
                    "is_published": True,
                    "published_at": datetime.now() - timedelta(days=1),
                },
                {
                    "activity_id": str(uuid.uuid4()),
                    "title": "Funciones y Parámetros",
                    "instructions": "Aprende a crear funciones, usar parámetros, valores por defecto, y retornar valores. Practica con scope de variables.",
                    "course_id": course_id,
                    "teacher_id": teacher_id,
                    "status": "draft",
                    "difficulty": "INTERMEDIO",
                    "estimated_duration_minutes": 75,
                    "max_score": 10.0,
                    "passing_score": 6.0,
                    "is_published": False,
                    "published_at": None,
                },
                {
                    "activity_id": str(uuid.uuid4()),
                    "title": "Estructuras de Datos: Listas y Diccionarios",
                    "instructions": "Explora listas, tuplas, conjuntos y diccionarios. Aprende métodos comunes y cuándo usar cada estructura.",
                    "course_id": course_id,
                    "teacher_id": teacher_id,
                    "status": "draft",
                    "difficulty": "INTERMEDIO",
                    "estimated_duration_minutes": 120,
                    "max_score": 10.0,
                    "passing_score": 6.0,
                    "is_published": False,
                    "published_at": None,
                },
                {
                    "activity_id": str(uuid.uuid4()),
                    "title": "Manejo de Excepciones",
                    "instructions": "Aprende a manejar errores con try, except, finally. Practica creando excepciones personalizadas.",
                    "course_id": course_id,
                    "teacher_id": teacher_id,
                    "status": "draft",
                    "difficulty": "DIFICIL",
                    "estimated_duration_minutes": 90,
                    "max_score": 10.0,
                    "passing_score": 7.0,
                    "is_published": False,
                    "published_at": None,
                },
            ]
            
            # Insert activities
            for activity in activities:
                await session.execute(
                    text("""
                        INSERT INTO activities (
                            activity_id, title, instructions, course_id, teacher_id,
                            status, difficulty, estimated_duration_minutes,
                            max_score, passing_score, is_published, published_at,
                            created_at, updated_at
                        ) VALUES (
                            :activity_id, :title, :instructions, :course_id, :teacher_id,
                            :status, :difficulty, :estimated_duration_minutes,
                            :max_score, :passing_score, :is_published, :published_at,
                            NOW(), NOW()
                        )
                    """),
                    activity
                )
                status_icon = "🟢" if activity["status"] == "published" else "⚪"
                print(f"  {status_icon} {activity['title']} ({activity['difficulty']})")
            
            await session.commit()
            
            print(f"\n✅ Successfully created {len(activities)} activities!")
            print(f"   - 3 published (visible to students)")
            print(f"   - 3 drafts (only visible to teacher)")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error: {e}")
            raise
        finally:
            await engine.dispose()

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  SEEDING TEST ACTIVITIES")
    print("="*60 + "\n")
    asyncio.run(seed_activities())
    print("\n" + "="*60)
    print("  ✅ SEED COMPLETE!")
    print("="*60 + "\n")
