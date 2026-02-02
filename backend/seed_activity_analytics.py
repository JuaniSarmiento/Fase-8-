"""
Seed script to populate database with synthetic submission data
for testing the Activity Detail view.

Creates 3 students with submissions for "Bucles: Introducción a For y While" activity.
Note: This version works without the enrollments table.
"""
import asyncio
import sys
import os

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

# Database URL - using Docker postgres service
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@postgres:5432/ai_native"


# Define models inline to avoid import issues
from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey, Float, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()


class SubmissionStatus(str, enum.Enum):
    """Submission status enum"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    GRADED = "graded"
    REVIEWED = "reviewed"


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


class SubmissionModel(Base):
    __tablename__ = "submissions"
    
    submission_id = Column(String(36), primary_key=True)
    student_id = Column(String(36), nullable=False, index=True)
    activity_id = Column(String(36), nullable=False, index=True)
    code_snapshot = Column(Text, nullable=False)
    status = Column(SQLEnum(SubmissionStatus), default=SubmissionStatus.PENDING, nullable=False)
    auto_grade = Column(Float, nullable=True)
    final_grade = Column(Float, nullable=True)
    is_manual_grade = Column(Boolean, default=False, nullable=False)
    ai_feedback = Column(Text, nullable=True)
    teacher_feedback = Column(Text, nullable=True)
    test_results = Column(JSONB, nullable=True)
    graded_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


async def main():
    """Main seeding function"""
    # Create async engine and session
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        print("🚀 Starting seed script for activity analytics...")

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
                course_id=None,  # Will link to course later
                teacher_id=None,  # Can be updated
                created_at=datetime.utcnow(),
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
                "password": "hashed_password_julian",
            },
            {
                "email": "pity@example.com",
                "username": "pity",
                "full_name": "Pity Martínez",
                "password": "hashed_password_pity",
            },
            {
                "email": "benedetto@example.com",
                "username": "benedetto",
                "full_name": "Darío Benedetto",
                "password": "hashed_password_benedetto",
            },
        ]

        students = []
        for data in students_data:
            result = await session.execute(
                select(UserModel).where(UserModel.email == data["email"])
            )
            student = result.scalar_one_or_none()

            if not student:
                student = UserModel(
                    id=str(uuid.uuid4()),
                    email=data["email"],
                    username=data["username"],
                    full_name=data["full_name"],
                    hashed_password=data["password"],
                    roles=["student"],
                    is_active=True,
                    created_at=datetime.utcnow(),
                )
                session.add(student)
                await session.flush()
                print(f"   ✅ Student created: {student.full_name} ({student.id})")
            else:
                print(f"   ✅ Student found: {student.full_name} ({student.id})")

            students.append(student)

        # Step 4: Create submissions (THE CORE TASK)
        print("\n📝 Step 4: Creating submissions...")
        submissions_data = [
            {
                "student": students[0],  # Julián
                "grade": 95.0,
                "status": SubmissionStatus.GRADED,
                "ai_feedback": "Excellent logic! Your implementation of the for loop is clean and efficient. Good use of range() function.",
                "code": """def sum_numbers(n):
    total = 0
    for i in range(1, n + 1):
        total += i
    return total

# Test
print(sum_numbers(10))  # Should output 55
""",
            },
            {
                "student": students[1],  # Pity
                "grade": 60.0,
                "status": SubmissionStatus.GRADED,
                "ai_feedback": "Logic error in loop condition. Your while loop has an incorrect termination condition, causing it to skip some iterations. Review the boundary conditions.",
                "code": """def count_down(n):
    while n >= 0:  # Should be n > 0
        print(n)
        n -= 1

count_down(5)
""",
            },
            {
                "student": students[2],  # Benedetto
                "grade": 20.0,
                "status": SubmissionStatus.GRADED,
                "ai_feedback": "Syntax error detected: infinite loop detected due to missing increment statement. The loop will never terminate. Add 'i += 1' inside the while loop.",
                "code": """def infinite_loop():
    i = 0
    while i < 10:
        print(i)
        # Missing: i += 1
    return i

infinite_loop()
""",
            },
        ]

        for idx, data in enumerate(submissions_data):
            # Check if submission already exists
            result = await session.execute(
                select(SubmissionModel).where(
                    SubmissionModel.student_id == data["student"].id,
                    SubmissionModel.activity_id == activity_id,
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                print(
                    f"   ⚠️  Submission already exists for {data['student'].full_name}. Skipping."
                )
                continue

            submission = SubmissionModel(
                submission_id=str(uuid.uuid4()),
                student_id=data["student"].id,
                activity_id=activity_id,
                code_snapshot=data["code"],
                status=data["status"],
                auto_grade=data["grade"],
                final_grade=data["grade"],
                is_manual_grade=False,
                ai_feedback=data["ai_feedback"],
                test_results={
                    "total_tests": 5,
                    "passed_tests": int(data["grade"] / 20),  # Simple mapping
                    "execution_time_ms": 120,
                },
                graded_at=datetime.utcnow() - timedelta(hours=idx + 1),
                created_at=datetime.utcnow() - timedelta(hours=idx + 2),
                updated_at=datetime.utcnow() - timedelta(hours=idx + 1),
            )
            session.add(submission)
            print(
                f"   ✅ Submission created for {data['student'].full_name}: Grade={data['grade']}"
            )

        # Step 5: Commit all changes
        print("\n💾 Step 5: Committing changes to database...")
        await session.commit()
        print("   ✅ All changes committed successfully!")

        # Step 6: Verification
        print("\n🔍 Step 6: Verifying data...")
        result = await session.execute(
            select(SubmissionModel).where(SubmissionModel.activity_id == activity_id)
        )
        submissions = result.scalars().all()
        print(f"   ✅ Total submissions for activity: {len(submissions)}")
        for sub in submissions:
            result = await session.execute(
                select(UserModel).where(UserModel.id == sub.student_id)
            )
            student = result.scalar_one()
            print(
                f"      - {student.full_name}: Grade={sub.final_grade}, Status={sub.status.value}"
            )

        print("\n✨ Seeding completed successfully!")
        print(f"   Activity ID: {activity_id}")
        print(f"   Activity Title: {activity_title}")


if __name__ == "__main__":
    asyncio.run(main())
