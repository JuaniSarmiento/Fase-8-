"""
Script para cargar datos de prueba en la base de datos.
"""
import asyncio
import sys
from pathlib import Path
from uuid import uuid4
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.src_v3.infrastructure.persistence.database import AsyncSessionLocal, engine
from backend.src_v3.infrastructure.persistence.sqlalchemy.models import (
    UserModel,
    UserProfileModel,
    SubjectModel,
    CourseModel,
    CommissionModel,
    ActivityModel,
    SessionModelV2,
    ExerciseModelV2,
    CognitiveTraceModelV2,
    ActivityStatus,
    DifficultyLevel,
    SessionStatus,
    SessionMode,
    TraceLevel,
    InteractionType,
    ExerciseDifficulty,
    ProgrammingLanguage,
)
from sqlalchemy import select


async def clear_data(session):
    """Limpiar datos de prueba existentes"""
    print("🗑️  Limpiando datos existentes...")
    
    # Delete in reverse order of dependencies
    await session.execute("DELETE FROM cognitive_traces_v2")
    await session.execute("DELETE FROM exercise_attempts_v2")
    await session.execute("DELETE FROM risks_v2")
    await session.execute("DELETE FROM sessions_v2")
    await session.execute("DELETE FROM exercises_v2")
    await session.execute("DELETE FROM activities")
    await session.execute("DELETE FROM user_profiles")
    await session.execute("DELETE FROM commissions")
    await session.execute("DELETE FROM courses")
    await session.execute("DELETE FROM subjects")
    await session.execute("DELETE FROM users WHERE email LIKE '%test%'")
    
    await session.commit()
    print("✅ Datos limpiados")


async def load_test_data():
    """Cargar datos de prueba completos"""
    async with AsyncSessionLocal() as session:
        try:
            # await clear_data(session)
            
            print("📦 Cargando datos de prueba...")
            
            # ==================== SUBJECTS ====================
            print("\n1️⃣ Creando materias...")
            subject1 = SubjectModel(
                subject_id=str(uuid4()),
                code="PROG1",
                name="Programación 1",
                credits=6,
            )
            subject2 = SubjectModel(
                subject_id=str(uuid4()),
                code="ALG1",
                name="Algoritmos 1",
                credits=8,
            )
            session.add_all([subject1, subject2])
            await session.flush()
            print(f"   ✅ {subject1.code}: {subject1.name}")
            print(f"   ✅ {subject2.code}: {subject2.name}")
            
            # ==================== COURSES ====================
            print("\n2️⃣ Creando cursos...")
            course1 = CourseModel(
                course_id=str(uuid4()),
                subject_id=subject1.subject_id,
                year=2024,
                semester=1,
            )
            course2 = CourseModel(
                course_id=str(uuid4()),
                subject_id=subject2.subject_id,
                year=2024,
                semester=1,
            )
            session.add_all([course1, course2])
            await session.flush()
            print(f"   ✅ Curso: {subject1.name} 2024-1")
            print(f"   ✅ Curso: {subject2.name} 2024-1")
            
            # ==================== USERS ====================
            print("\n3️⃣ Creando usuarios...")
            
            # Teacher
            teacher = UserModel(
                user_id=str(uuid4()),
                email="teacher.test@universidad.edu",
                username="Prof. García",
                password_hash="$2b$12$test_hash",
                roles=["teacher", "admin"],
                is_active=True,
            )
            session.add(teacher)
            await session.flush()
            print(f"   👨‍🏫 Teacher: {teacher.username}")
            
            # Students
            students = []
            for i in range(3):
                student = UserModel(
                    user_id=str(uuid4()),
                    email=f"student{i+1}.test@universidad.edu",
                    username=f"Estudiante {i+1}",
                    password_hash="$2b$12$test_hash",
                    roles=["student"],
                    is_active=True,
                )
                students.append(student)
                session.add(student)
            
            await session.flush()
            for s in students:
                print(f"   👨‍🎓 Student: {s.username}")
            
            # ==================== COMMISSIONS ====================
            print("\n4️⃣ Creando comisiones...")
            commission1 = CommissionModel(
                commission_id=str(uuid4()),
                course_id=course1.course_id,
                teacher_id=teacher.user_id,
                name="Comisión A",
                schedule={"lunes": "14:00-16:00", "miércoles": "14:00-16:00"},
                capacity=30,
            )
            session.add(commission1)
            await session.flush()
            print(f"   ✅ {commission1.name} - {subject1.name}")
            
            # ==================== USER PROFILES ====================
            print("\n5️⃣ Creando perfiles académicos...")
            for idx, student in enumerate(students):
                profile = UserProfileModel(
                    profile_id=str(uuid4()),
                    user_id=student.user_id,
                    student_id=f"EST{2024}{idx+1:03d}",
                    course_id=course1.course_id,
                    commission_id=commission1.commission_id,
                    enrollment_date=datetime.utcnow(),
                )
                session.add(profile)
                print(f"   ✅ {profile.student_id} → {subject1.name}")
            
            await session.flush()
            
            # ==================== ACTIVITIES ====================
            print("\n6️⃣ Creando actividades...")
            activity1 = ActivityModel(
                activity_id=str(uuid4()),
                title="Introducción a Bucles",
                subject="Programación 1",
                unit_id="1",
                teacher_id=teacher.user_id,
                course_id=course1.course_id,
                instructions="Practicar el uso de bucles while y for en Python",
                status=ActivityStatus.ACTIVE,
                difficulty_level=DifficultyLevel.FACIL,
                policies={
                    "max_ai_help_level": "MEDIO",
                    "allow_code_snippets": True,
                    "require_test_cases": True,
                },
                start_date=datetime.utcnow(),
            )
            
            activity2 = ActivityModel(
                activity_id=str(uuid4()),
                title="Funciones y Recursión",
                subject="Programación 1",
                unit_id="2",
                teacher_id=teacher.user_id,
                course_id=course1.course_id,
                instructions="Implementar funciones recursivas",
                status=ActivityStatus.ACTIVE,
                difficulty_level=DifficultyLevel.INTERMEDIO,
                policies={
                    "max_ai_help_level": "BAJO",
                    "allow_code_snippets": False,
                    "require_test_cases": True,
                },
                start_date=datetime.utcnow(),
            )
            
            session.add_all([activity1, activity2])
            await session.flush()
            print(f"   ✅ Actividad: {activity1.title}")
            print(f"   ✅ Actividad: {activity2.title}")
            
            # ==================== EXERCISES ====================
            print("\n7️⃣ Creando ejercicios...")
            exercise1 = ExerciseModelV2(
                exercise_id=str(uuid4()),
                title="Suma de números pares",
                description="Sumar todos los números pares de 1 a N",
                subject_id=subject1.subject_id,
                unit_number=1,
                difficulty=ExerciseDifficulty.FACIL,
                language=ProgrammingLanguage.PYTHON,
                mission_markdown="""
## 🎯 Misión

Crea una función que sume todos los números pares desde 1 hasta N.

### Ejemplo:
- Entrada: 10
- Salida: 30 (2 + 4 + 6 + 8 + 10)
""",
                starter_code="def suma_pares(n):\n    # TODO: Implementa aquí\n    pass",
                solution_code="def suma_pares(n):\n    return sum(i for i in range(2, n+1, 2))",
                test_cases=[
                    {
                        "test_number": 1,
                        "input": "10",
                        "expected": "30",
                        "is_hidden": False,
                    },
                    {
                        "test_number": 2,
                        "input": "20",
                        "expected": "110",
                        "is_hidden": True,
                    },
                ],
                tags=["bucles", "suma", "números pares"],
                estimated_time_minutes=15,
            )
            
            exercise2 = ExerciseModelV2(
                exercise_id=str(uuid4()),
                title="Factorial recursivo",
                description="Calcular factorial usando recursión",
                subject_id=subject1.subject_id,
                unit_number=2,
                difficulty=ExerciseDifficulty.INTERMEDIO,
                language=ProgrammingLanguage.PYTHON,
                mission_markdown="""
## 🎯 Misión

Implementa el cálculo del factorial de forma recursiva.

### Ejemplo:
- factorial(5) = 5 * 4 * 3 * 2 * 1 = 120
""",
                starter_code="def factorial(n):\n    # TODO: Implementa recursión\n    pass",
                solution_code="def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n-1)",
                test_cases=[
                    {
                        "test_number": 1,
                        "input": "5",
                        "expected": "120",
                        "is_hidden": False,
                    },
                ],
                tags=["recursión", "factorial", "funciones"],
                estimated_time_minutes=30,
            )
            
            session.add_all([exercise1, exercise2])
            await session.flush()
            print(f"   ✅ Ejercicio: {exercise1.title}")
            print(f"   ✅ Ejercicio: {exercise2.title}")
            
            # ==================== SESSIONS ====================
            print("\n8️⃣ Creando sesiones de aprendizaje...")
            session1 = SessionModelV2(
                session_id=str(uuid4()),
                user_id=students[0].user_id,
                activity_id=activity1.activity_id,
                course_id=course1.course_id,
                status=SessionStatus.ACTIVE,
                mode=SessionMode.SOCRATIC,
                learning_objective="Comprender bucles while",
                cognitive_status={
                    "phase": "EXPLORATION",
                    "autonomy_level": 0.6,
                    "engagement_score": 0.8,
                    "ai_dependency_score": 0.4,
                },
                session_metrics={
                    "total_interactions": 5,
                    "average_response_time": 45.2,
                    "questions_asked": 3,
                },
                start_time=datetime.utcnow(),
            )
            
            session.add(session1)
            await session.flush()
            print(f"   ✅ Sesión: {students[0].username} → {activity1.title}")
            
            # ==================== COGNITIVE TRACES ====================
            print("\n9️⃣ Creando trazas cognitivas...")
            trace1 = CognitiveTraceModelV2(
                trace_id=str(uuid4()),
                session_id=session1.session_id,
                activity_id=activity1.activity_id,
                trace_level=TraceLevel.INFO,
                interaction_type=InteractionType.STUDENT_QUESTION,
                semantic_understanding={
                    "student_message": "¿Cómo funciona el bucle while?",
                    "topic_relevance": 0.95,
                    "clarity_score": 0.8,
                },
                algorithmic_evolution={
                    "code_submitted": False,
                    "syntax_errors": 0,
                },
                cognitive_reasoning={
                    "understanding_level": 0.6,
                    "frustration_level": 0.3,
                    "engagement": 0.8,
                },
                interactional_data={
                    "tutor_response": "Excelente pregunta. ¿Qué crees que hace la condición del while?",
                    "socratic_technique": "counter_question",
                },
                ai_involvement=0.7,
            )
            
            session.add(trace1)
            await session.flush()
            print(f"   ✅ Traza: Pregunta sobre bucles")
            
            # ==================== COMMIT ====================
            await session.commit()
            
            print("\n" + "="*60)
            print("✅ DATOS DE PRUEBA CARGADOS EXITOSAMENTE")
            print("="*60)
            print(f"\n📊 Resumen:")
            print(f"   - Materias: 2")
            print(f"   - Cursos: 2")
            print(f"   - Usuarios: 4 (1 teacher, 3 students)")
            print(f"   - Actividades: 2")
            print(f"   - Ejercicios: 2")
            print(f"   - Sesiones: 1")
            print(f"   - Trazas: 1")
            
            print(f"\n🔑 Credenciales de prueba:")
            print(f"   Teacher: teacher.test@universidad.edu")
            print(f"   Student 1: student1.test@universidad.edu")
            print(f"   Student 2: student2.test@universidad.edu")
            print(f"   Student 3: student3.test@universidad.edu")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            await session.rollback()
            raise


async def main():
    """Main function"""
    print("\n" + "="*60)
    print("🚀 CARGANDO DATOS DE PRUEBA - FASE 8")
    print("="*60 + "\n")
    
    try:
        # Test connection
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
            print("✅ Conexión a la base de datos exitosa\n")
        
        # Load data
        await load_test_data()
        
    except Exception as e:
        print(f"\n❌ Error crítico: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
