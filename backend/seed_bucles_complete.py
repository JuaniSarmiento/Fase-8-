"""
Complete seed script to populate Bucles activities with real students and grades.
Creates 15 students per activity with varied performance levels.
All data is stored in PostgreSQL database (sessions_v2 table).
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uuid
import random
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, Column, String, Text, Boolean, DateTime, Enum as SQLEnum
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
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class DifficultyLevel(str, enum.Enum):
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
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class SessionMode(str, enum.Enum):
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


# Student names pool (realistic Argentine names)
STUDENT_NAMES = [
    "Juan Martínez", "María García", "Carlos López", "Ana Rodríguez", "Luis González",
    "Laura Fernández", "Diego Pérez", "Sofía Sánchez", "Mateo Romero", "Valentina Torres",
    "Santiago Flores", "Camila Díaz", "Nicolás Alvarez", "Isabella Ruiz", "Benjamín Castro",
    "Martina Silva", "Lucas Moreno", "Emma Herrera", "Thiago Vega", "Mía Mendoza",
    "Felipe Ortiz", "Catalina Medina", "Tomás Ríos", "Lucía Vargas", "Joaquín Ramírez",
    "Antonella Gutiérrez", "Emilio Cruz", "Victoria Jiménez", "Gabriel Muñoz", "Regina Navarro"
]


def generate_grade_and_feedback(performance_level: str) -> tuple:
    """Generate realistic grade and feedback based on performance level"""
    
    if performance_level == "excellent":
        grade = random.randint(90, 100)
        feedbacks = [
            f"¡Excelente trabajo! Dominas completamente los conceptos de bucles. Nota: {grade}/100",
            f"Sobresaliente. Tu código es limpio, eficiente y bien estructurado. Nota: {grade}/100",
            f"Perfecto entendimiento de bucles for y while. Sigue así! Nota: {grade}/100",
            f"Trabajo impecable. Demuestras un alto nivel de comprensión. Nota: {grade}/100"
        ]
        exercises_completed = random.randint(9, 10)
        hints_used = random.randint(0, 2)
        time_spent = random.randint(30, 50)
        
    elif performance_level == "good":
        grade = random.randint(70, 89)
        feedbacks = [
            f"Buen trabajo. Entiendes los conceptos básicos, sigue practicando. Nota: {grade}/100",
            f"Muy bien. Algunas áreas de mejora en la optimización de código. Nota: {grade}/100",
            f"Sólido desempeño. Practica más los casos edge. Nota: {grade}/100",
            f"Bien hecho. Continúa así y mejora en la eficiencia del código. Nota: {grade}/100"
        ]
        exercises_completed = random.randint(7, 9)
        hints_used = random.randint(2, 5)
        time_spent = random.randint(50, 70)
        
    elif performance_level == "passing":
        grade = random.randint(60, 69)
        feedbacks = [
            f"Aprobado. Necesitas reforzar algunos conceptos de iteración. Nota: {grade}/100",
            f"Cumple con lo mínimo. Revisa los ejemplos de la clase. Nota: {grade}/100",
            f"Aprobado justo. Practica más con bucles anidados. Nota: {grade}/100",
            f"Suficiente pero mejorable. Repasa el uso de break y continue. Nota: {grade}/100"
        ]
        exercises_completed = random.randint(6, 7)
        hints_used = random.randint(5, 8)
        time_spent = random.randint(60, 90)
        
    else:  # at_risk
        grade = random.randint(15, 59)
        feedbacks = [
            f"⚠️ ALERTA: Requiere atención urgente. No logra entender los conceptos básicos de bucles. Se recomienda tutoría. Nota: {grade}/100",
            f"⚠️ RIESGO ACADÉMICO: Muchas dificultades con iteraciones. Necesita apoyo adicional. Nota: {grade}/100",
            f"⚠️ EN RIESGO: No comprende la sintaxis básica. Sesión de recuperación requerida. Nota: {grade}/100",
            f"⚠️ ALERTA ROJA: Nivel muy bajo. Se necesita intervención inmediata. Nota: {grade}/100"
        ]
        exercises_completed = random.randint(1, 4)
        hints_used = random.randint(10, 20)
        time_spent = random.randint(80, 120)
    
    feedback = random.choice(feedbacks)
    understanding = "high" if grade >= 80 else "medium" if grade >= 60 else "low"
    
    return grade, feedback, exercises_completed, hints_used, time_spent, understanding


async def main():
    engine = create_async_engine(DATABASE_URL, echo=False)  # echo=False para menos logs
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        print("🚀 Starting complete seed script for Bucles activities...")
        print("=" * 70)

        # Step 1: Get activities
        print("\n📚 Step 1: Finding Bucles activities...")
        result = await session.execute(
            select(ActivityModel).where(
                ActivityModel.title.like('%Bucle%')
            ).order_by(ActivityModel.title)
        )
        activities = result.scalars().all()
        
        if len(activities) == 0:
            print("   ❌ No se encontraron actividades 'Bucles' o 'Bucles 2'")
            return
        
        for act in activities:
            print(f"   ✅ Found: {act.title} (ID: {act.activity_id})")

        # Step 2: Create 15 students with varied performance
        print("\n👥 Step 2: Creating 15 diverse students...")
        
        # Performance distribution (realistic class distribution)
        performance_distribution = (
            ["excellent"] * 3 +      # 3 excellent students (20%)
            ["good"] * 6 +           # 6 good students (40%)
            ["passing"] * 4 +        # 4 passing students (27%)
            ["at_risk"] * 2          # 2 at-risk students (13%)
        )
        random.shuffle(performance_distribution)
        
        students = []
        for i, name in enumerate(STUDENT_NAMES[:15]):
            username = name.lower().replace(" ", "").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
            email = f"{username}@estudiantes.com"
            
            # Check if student exists
            result = await session.execute(
                select(UserModel).where(UserModel.email == email)
            )
            student = result.scalar_one_or_none()
            
            if not student:
                student = UserModel(
                    id=str(uuid.uuid4()),
                    email=email,
                    username=username,
                    hashed_password=f"hashed_{username}",
                    full_name=name,
                    roles=["student"],
                    is_active=True,
                    created_at=datetime.now()
                )
                session.add(student)
                await session.flush()
                print(f"   ✅ Created: {name}")
            else:
                print(f"   ⏭️  Exists: {name}")
            
            students.append({
                "model": student,
                "performance": performance_distribution[i]
            })

        # Step 3: Create sessions for each activity
        print("\n📝 Step 3: Creating sessions for each activity...")
        
        total_sessions_created = 0
        
        for activity in activities:
            print(f"\n   🎯 Activity: {activity.title}")
            print(f"   ID: {activity.activity_id}")
            
            for student_data in students:
                student = student_data["model"]
                performance = student_data["performance"]
                
                # Check if session already exists
                result = await session.execute(
                    select(SessionModelV2).where(
                        SessionModelV2.user_id == student.id,
                        SessionModelV2.activity_id == activity.activity_id
                    )
                )
                existing_session = result.scalar_one_or_none()
                
                if existing_session:
                    continue
                
                # Generate realistic data
                grade, feedback, exercises, hints, time, understanding = generate_grade_and_feedback(performance)
                
                # Random timestamps within last 7 days
                days_ago = random.randint(1, 7)
                start_time = datetime.now() - timedelta(days=days_ago, hours=random.randint(1, 5))
                end_time = start_time + timedelta(minutes=time)
                
                # Create session
                new_session = SessionModelV2(
                    session_id=str(uuid.uuid4()),
                    user_id=student.id,
                    activity_id=activity.activity_id,
                    course_id=None,
                    status=SessionStatus.COMPLETED,
                    mode=SessionMode.SOCRATIC,
                    learning_objective=f"Practicar bucles - {activity.title}",
                    cognitive_status={
                        "feedback": feedback,
                        "last_feedback": feedback,
                        "understanding_level": understanding,
                        "concepts_mastered": ["for", "while"] if grade >= 70 else ["for"] if grade >= 60 else [],
                        "concepts_struggling": ["break", "continue"] if grade < 60 else []
                    },
                    session_metrics={
                        "final_grade": grade,
                        "score": grade,
                        "exercises_completed": exercises,
                        "total_exercises": 10,
                        "hints_used": hints,
                        "time_spent_minutes": time,
                        "attempts": 1 if grade >= 80 else 2 if grade >= 60 else random.randint(3, 5)
                    },
                    start_time=start_time,
                    end_time=end_time,
                    created_at=start_time
                )
                session.add(new_session)
                total_sessions_created += 1
            
            await session.flush()
            print(f"   ✅ Created sessions for {len(students)} students")

        # Step 4: Commit all changes
        print("\n💾 Step 4: Committing all changes to database...")
        await session.commit()
        print("   ✅ All changes committed successfully!")

        # Step 5: Verify and show statistics
        print("\n🔍 Step 5: Verification and Statistics")
        print("=" * 70)
        
        for activity in activities:
            result = await session.execute(
                select(SessionModelV2).where(
                    SessionModelV2.activity_id == activity.activity_id
                )
            )
            sessions = result.scalars().all()
            
            if sessions:
                grades = [s.session_metrics.get("final_grade", 0) for s in sessions if s.session_metrics]
                avg_grade = sum(grades) / len(grades) if grades else 0
                at_risk = sum(1 for g in grades if g < 60)
                excellent = sum(1 for g in grades if g >= 80)
                
                print(f"\n📊 {activity.title}")
                print(f"   Activity ID: {activity.activity_id}")
                print(f"   Total Sessions: {len(sessions)}")
                print(f"   Average Grade: {avg_grade:.1f}/100")
                print(f"   🟢 Excellent (≥80): {excellent}")
                print(f"   🔴 At Risk (<60): {at_risk}")
                print(f"\n   🔗 Test URL:")
                print(f"   http://localhost:8000/api/v3/analytics/activities/{activity.activity_id}/submissions_analytics")

        print("\n" + "=" * 70)
        print("✨ SEED SCRIPT COMPLETED SUCCESSFULLY! ✨")
        print("=" * 70)
        print(f"\n📈 Summary:")
        print(f"   - Activities processed: {len(activities)}")
        print(f"   - Students created/used: {len(students)}")
        print(f"   - Total sessions created: {total_sessions_created}")
        print(f"\n🎯 Next Steps:")
        print(f"   1. Navigate to: http://localhost:3000/teacher/activities/<activity_id>")
        print(f"   2. Click on 'Analytics' tab")
        print(f"   3. See real data from PostgreSQL database!")
        print("\n")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
