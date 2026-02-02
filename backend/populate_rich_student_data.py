import asyncio
import os
import sys
import uuid
import datetime
import random
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Add payload to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src_v3"))

# DB Config
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres")

async def populate_rich_student_data():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        print("Creating rich student data for verification...")

        # 1. Create Teacher
        teacher_id = str(uuid.uuid4())
        await db.execute(text("""
            INSERT INTO users (id, email, username, full_name, role, created_at)
            VALUES (:id, :email, :username, :full_name, 'teacher', NOW())
            ON CONFLICT (email) DO NOTHING
        """), {
            "id": teacher_id,
            "email": "teacher_verify@test.com",
            "username": "teacher_verify",
            "full_name": "Profesor Verificación"
        })
        
        # 2. Create Course
        course_id = str(uuid.uuid4())
        await db.execute(text("""
            INSERT INTO courses (course_id, title, description, teacher_id, created_at)
            VALUES (:id, 'Python Avanzado 2025', 'Curso de prueba de analíticas', :teacher_id, NOW())
        """), {"id": course_id, "teacher_id": teacher_id})

        # 3. Create Activity
        activity_id = str(uuid.uuid4())
        await db.execute(text("""
            INSERT INTO activities (activity_id, course_id, title, description, status, teacher_id, created_at)
            VALUES (:id, :course_id, 'Análisis de Datos con Pandas', 'Actividad práctica completa', 'ACTIVE', :teacher_id, NOW())
        """), {"id": activity_id, "course_id": course_id, "teacher_id": teacher_id})

        # 4. Create Exercises
        ex1_id = str(uuid.uuid4())
        ex2_id = str(uuid.uuid4())
        
        await db.execute(text("""
            INSERT INTO exercises_v2 (exercise_id, activity_id, title, description, difficulty, points, order_index)
            VALUES 
            (:ex1, :act_id, 'Ejercicio 1: Cargar CSV', 'Carga el archivo data.csv en un DataFrame', 'easy', 40, 1),
            (:ex2, :act_id, 'Ejercicio 2: Filtrar Datos', 'Filtra las filas donde edad > 30', 'medium', 60, 2)
        """), {"ex1": ex1_id, "ex2": ex2_id, "act_id": activity_id})

        # 5. Create Student
        student_id = str(uuid.uuid4())
        await db.execute(text("""
            INSERT INTO users (id, email, username, full_name, role, created_at)
            VALUES (:id, :email, :username, :full_name, 'student', NOW())
        """), {
            "id": student_id,
            "email": "alumno_test_analytics@test.com",
            "username": "alumno_analytics",
            "full_name": "Alumno Test Analytics"
        })

        # 6. Create Session
        session_id = str(uuid.uuid4())
        await db.execute(text("""
            INSERT INTO sessions_v2 (session_id, user_id, activity_id, status, start_time, end_time, session_metrics, cognitive_status)
            VALUES (:id, :uid, :act_id, 'completed', NOW() - INTERVAL '1 hour', NOW(), :metrics, :cog)
        """), {
            "id": session_id,
            "uid": student_id,
            "act_id": activity_id,
            "metrics": '{"duration_minutes": 45, "total_interactions": 12, "final_grade": 75}',
            "cog": '{"cognitive_phase": "reflection", "frustration_level": 0.2, "understanding_level": 0.8, "hint_count": 3}'
        })

        # 7. Insert Cognitive Traces (Chat + Governance)
        # 7a. User asks for help (Low risk)
        await db.execute(text("""
            INSERT INTO cognitive_traces_v2 (trace_id, session_id, interaction_type, interactional_data, timestamp, ai_involvement)
            VALUES (:id, :sid, 'student_question', '{"content": "No entiendo cómo usar read_csv, me ayudas?"}', NOW() - INTERVAL '50 minutes', 0.2)
        """), {"id": str(uuid.uuid4()), "sid": session_id})

        # 7b. Tutor responds
        await db.execute(text("""
            INSERT INTO cognitive_traces_v2 (trace_id, session_id, interaction_type, interactional_data, timestamp, ai_involvement)
            VALUES (:id, :sid, 'tutor_response', '{"content": "Claro, usa pandas.read_csv(\"ruta\")"}', NOW() - INTERVAL '49 minutes', 0.2)
        """), {"id": str(uuid.uuid4()), "sid": session_id})

        # 7c. User shows frustration (High risk moment)
        await db.execute(text("""
            INSERT INTO cognitive_traces_v2 (trace_id, session_id, interaction_type, interactional_data, timestamp, ai_involvement)
            VALUES (:id, :sid, 'student_question', '{"content": "Esto es una mierda, no funciona nada. Dame la respuesta ya."}', NOW() - INTERVAL '30 minutes', 0.8)
        """), {"id": str(uuid.uuid4()), "sid": session_id})

        # 7d. Governance Log (Risk Alert)
        await db.execute(text("""
            INSERT INTO cognitive_traces_v2 (trace_id, session_id, interaction_type, interactional_data, timestamp)
            VALUES (:id, :sid, 'governance_log', '{"risk_level": "ALTO", "evidence": ["Lenguaje ofensivo", "Solicitud directa de solución"], "ai_dependency_score": 0.9, "recommendation": "Intervention required: Frustration detected."}', NOW() - INTERVAL '29 minutes')
        """), {"id": str(uuid.uuid4()), "sid": session_id})

        # 8. Exercise Attempts
        # 8a. Failed attempt at Ex 1
        await db.execute(text("""
            INSERT INTO exercise_attempts_v2 (attempt_id, user_id, exercise_id, session_id, status, submitted_code, ai_feedback, grade, submitted_at)
            VALUES (:id, :uid, :eid, :sid, 'failed', 'import pandas as pd\ndf = open("data.csv")', 'No uses open(), usa pd.read_csv().', 20, NOW() - INTERVAL '40 minutes')
        """), {
            "id": str(uuid.uuid4()),
            "uid": student_id,
            "eid": ex1_id,
            "sid": session_id
        })

        # 8b. Successful attempt at Ex 1
        await db.execute(text("""
            INSERT INTO exercise_attempts_v2 (attempt_id, user_id, exercise_id, session_id, status, submitted_code, ai_feedback, grade, submitted_at)
            VALUES (:id, :uid, :eid, :sid, 'passed', 'import pandas as pd\ndf = pd.read_csv("data.csv")', 'Excelente trabajo. Has cargado el CSV correctamente.', 100, NOW() - INTERVAL '35 minutes')
        """), {
            "id": str(uuid.uuid4()),
            "uid": student_id,
            "eid": ex1_id,
            "sid": session_id
        })

        # 8c. Struggling attempt at Ex 2
        await db.execute(text("""
            INSERT INTO exercise_attempts_v2 (attempt_id, user_id, exercise_id, session_id, status, submitted_code, ai_feedback, grade, submitted_at)
            VALUES (:id, :uid, :eid, :sid, 'failed', 'df[df > 30]', 'Casi. Debes filtrar por la columna edad specifically: df[df["edad"] > 30]', 50, NOW() - INTERVAL '10 minutes')
        """), {
            "id": str(uuid.uuid4()),
            "uid": student_id,
            "eid": ex2_id,
            "sid": session_id
        })

        # 9. Final Submission
        await db.execute(text("""
            INSERT INTO submissions (submission_id, activity_id, student_id, final_grade, ai_feedback, status, submitted_at)
            VALUES (:id, :act, :stu, 75, 'El alumno mostró comprensión del primer ejercicio pero luchó con el filtrado. Se detectó frustración media.', 'graded', NOW())
        """), {
            "id": str(uuid.uuid4()),
            "act": activity_id,
            "stu": student_id
        })

        await db.commit()
        print(f"Data populated successfully!")
        print(f"Teacher Email: teacher_verify@test.com")
        print(f"Student Name: Alumno Test Analytics")
        print(f"Activity ID: {activity_id}")
        
        # Verify Traceability
        print("\nVerifying traceability endpoint logic...")
        row = await db.execute(text("SELECT interactional_data FROM cognitive_traces_v2 WHERE interaction_type = 'governance_log' ORDER BY timestamp DESC LIMIT 1"))
        data = row.fetchone()
        if data:
            print("Governance log found:", data[0])
        else:
            print("❌ No governance log found!")

if __name__ == "__main__":
    asyncio.run(populate_rich_student_data())
