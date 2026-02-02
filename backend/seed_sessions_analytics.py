"""
Seed script to populate database with synthetic session data
for testing the Activity Analytics view.

Creates 3 students with sessions for "Bucles: Introducción a For y While" activity.
Uses sessions_v2 table which already exists in the database.
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, Column, String, Text, Integer, Boolean, DateTime, Float, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
import enum

# Database URL - using Docker postgres service
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@postgres:5432/ai_native"

Base = declarative_base()


class UserModel(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    roles = Column(JSONB, default=list, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class ActivityStatus(str, enum.Enum):
    """Activity status enum"""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class DifficultyLevel(str, enum.Enum):
    """Difficulty level enum"""
    INICIAL = "INICIAL"
    INTERMEDIO = "INTERMEDIO"
    AVANZADO = "AVANZADO"


class ActivityModel(Base):
    __tablename__ = "activities"
    
    activity_id = Column(String(36), primary_key=True)
    title = Column(String(300), nullable=False)
    subject = Column(String(200), nullable=True)
    unit_id = Column(String(50), nullable=True)
    instructions = Column(Text, nullable=False)
    status = Column(SQLEnum(ActivityStatus), nullable=True)
    difficulty_level = Column(SQLEnum(DifficultyLevel), nullable=True)
    course_id = Column(String(36), nullable=True)
    teacher_id = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SessionStatus(str, enum.Enum):
    """Session status enum"""
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class SessionMode(str, enum.Enum):
    """Session mode enum"""
    SOCRATIC = "socratic"
    SIMULATOR = "simulator"
    TUTOR = "tutor"


class SessionModelV2(Base):
    __tablename__ = "sessions_v2"
    
    session_id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=False)
    activity_id = Column(String(36), nullable=False)
    course_id = Column(String(36), nullable=True)
    status = Column(SQLEnum(SessionStatus), default=SessionStatus.ACTIVE)
    mode = Column(SQLEnum(SessionMode), default=SessionMode.SOCRATIC)
    learning_objective = Column(Text, nullable=True)
    cognitive_status = Column(JSONB, nullable=True)
    session_metrics = Column(JSONB, nullable=True)
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


async def main():
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        print("🚀 Starting seed script for session analytics...")

        # Step 1: Find or create the target activity
        print("\n📚 Step 1: Finding/Creating 'Bucles' activity...")
        activity_title = "Bucles: Introducción a For y While"
        
        result = await session.execute(
            select(ActivityModel).where(ActivityModel.title == activity_title)
        )
        activity = result.scalar_one_or_none()

        if not activity:
            # Create activity if it doesn't exist
            print(f"   ⚠️  Activity '{activity_title}' not found. Creating it...")
            activity = ActivityModel(
                activity_id=str(uuid.uuid4()),
                title=activity_title,
                subject="Estructuras de Control: Bucles",
                unit_id="Unit_1",
                instructions="Aprender los conceptos básicos de bucles for y while en Python.",
                status=ActivityStatus.ACTIVE,
                difficulty_level=DifficultyLevel.INTERMEDIO,
                course_id=None,
                teacher_id=None,
                created_at=datetime.now()
            )
            session.add(activity)
            await session.flush()
            print(f"   ✅ Activity created: {activity.activity_id}")
        else:
            print(f"   ✅ Activity found: {activity.activity_id}")

        activity_id = activity.activity_id

        # Step 2: Ensure students exist
        print("\n👨‍🎓 Step 2: Creating/Finding students...")
        students_data = [
            {
                "email": "julian@example.com",
                "username": "julian",
                "full_name": "Julián Álvarez",
                "grade": 95,
                "feedback": "Excelente trabajo. Dominas completamente los conceptos de bucles for y while. Tu código es limpio y eficiente."
            },
            {
                "email": "pity@example.com",
                "username": "pity",
                "full_name": "Pity Martínez",
                "grade": 60,
                "feedback": "Buen progreso, pero necesitas practicar más el uso de rangos en los bucles for. Revisa los ejemplos de la clase."
            },
            {
                "email": "benedetto@example.com",
                "username": "benedetto",
                "full_name": "Darío Benedetto",
                "grade": 20,
                "feedback": "⚠️ ALERTA: Requiere atención urgente. No logra entender los conceptos básicos. Se recomienda sesión de recuperación."
            },
        ]

        students = []
        for student_data in students_data:
            result = await session.execute(
                select(UserModel).where(UserModel.email == student_data["email"])
            )
            student = result.scalar_one_or_none()

            if not student:
                student = UserModel(
                    id=str(uuid.uuid4()),
                    email=student_data["email"],
                    username=student_data["username"],
                    hashed_password=f"hashed_password_{student_data['username']}",
                    full_name=student_data["full_name"],
                    roles=["student"],
                    is_active=True,
                    created_at=datetime.now()
                )
                session.add(student)
                await session.flush()
                print(f"   ✅ Student created: {student.full_name} ({student.id})")
            else:
                print(f"   ✅ Student found: {student.full_name} ({student.id})")

            students.append((student, student_data))

        # Step 3: Creating sessions
        print("\n📝 Step 3: Creating sessions...")
        for student, student_data in students:
            # Check if session already exists
            result = await session.execute(
                select(SessionModelV2).where(
                    SessionModelV2.user_id == student.id,
                    SessionModelV2.activity_id == activity_id
                )
            )
            existing_session = result.scalar_one_or_none()

            if existing_session:
                print(f"   ⏭️  Session already exists for {student.full_name}")
                continue

            # Create new session
            session_id = str(uuid.uuid4())
            start_time = datetime.now() - timedelta(hours=2)
            end_time = datetime.now() - timedelta(hours=1)

            new_session = SessionModelV2(
                session_id=session_id,
                user_id=student.id,
                activity_id=activity_id,
                course_id=None,
                status=SessionStatus.COMPLETED,
                mode=SessionMode.SOCRATIC,
                learning_objective="Practicar bucles for y while en Python",
                cognitive_status={
                    "feedback": student_data["feedback"],
                    "last_feedback": student_data["feedback"],
                    "understanding_level": "high" if student_data["grade"] >= 80 else "medium" if student_data["grade"] >= 60 else "low"
                },
                session_metrics={
                    "final_grade": student_data["grade"],
                    "score": student_data["grade"],
                    "exercises_completed": 10 if student_data["grade"] >= 80 else 6 if student_data["grade"] >= 60 else 2,
                    "hints_used": 1 if student_data["grade"] >= 80 else 5 if student_data["grade"] >= 60 else 12,
                    "time_spent_minutes": 45 if student_data["grade"] >= 80 else 60 if student_data["grade"] >= 60 else 90
                },
                start_time=start_time,
                end_time=end_time,
                created_at=start_time
            )
            session.add(new_session)
            print(f"   ✅ Session created for {student.full_name} (Grade: {student_data['grade']})")

        # Step 4: Commit all changes
        print("\n💾 Step 4: Committing changes to database...")
        await session.commit()
        print("   ✅ All changes committed successfully!")

        # Step 5: Verify the data
        print("\n🔍 Step 5: Verifying data...")
        result = await session.execute(
            select(SessionModelV2).where(SessionModelV2.activity_id == activity_id)
        )
        sessions = result.scalars().all()
        print(f"   ✅ Found {len(sessions)} sessions for activity '{activity_title}'")

        print("\n" + "="*60)
        print("✨ SEED SCRIPT COMPLETED SUCCESSFULLY! ✨")
        print("="*60)
        print(f"\n📊 Summary:")
        print(f"   - Activity ID: {activity_id}")
        print(f"   - Activity Title: {activity_title}")
        print(f"   - Students: {len(students)}")
        print(f"   - Sessions Created: {len(sessions)}")
        print(f"\n🔗 Test the endpoint:")
        print(f"   GET http://localhost:8000/api/v3/analytics/activities/{activity_id}/submissions_analytics")
        print("\n")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
