"""
Script para agregar ejercicios a actividades y estudiantes con trazabilidad.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from backend.src_v3.infrastructure.persistence.database import get_db_session
from datetime import datetime, timezone
import uuid


async def seed_exercises_and_students():
    """Agrega ejercicios a actividades existentes y crea estudiantes con trazabilidad."""
    
    async for db in get_db_session():
        try:
            # 1. Obtener todas las actividades
            result = await db.execute(text("""
                SELECT activity_id, title FROM activities LIMIT 6
            """))
            activities = result.fetchall()
            
            if not activities:
                print("No hay actividades en la base de datos")
                return
            
            print(f"Encontradas {len(activities)} actividades")
            
            # 2. Crear estudiantes si no existen
            students_data = [
                {
                    'id': str(uuid.uuid4()),
                    'email': 'estudiante1@test.com',
                    'username': 'maria.garcia',
                    'full_name': 'María García',
                    'password': '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYdR8L6k.6i'  # 123456
                },
                {
                    'id': str(uuid.uuid4()),
                    'email': 'estudiante2@test.com',
                    'username': 'juan.perez',
                    'full_name': 'Juan Pérez',
                    'password': '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYdR8L6k.6i'
                },
                {
                    'id': str(uuid.uuid4()),
                    'email': 'estudiante3@test.com',
                    'username': 'ana.martinez',
                    'full_name': 'Ana Martínez',
                    'password': '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYdR8L6k.6i'
                },
                {
                    'id': str(uuid.uuid4()),
                    'email': 'estudiante4@test.com',
                    'username': 'carlos.lopez',
                    'full_name': 'Carlos López',
                    'password': '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYdR8L6k.6i'
                },
                {
                    'id': str(uuid.uuid4()),
                    'email': 'estudiante5@test.com',
                    'username': 'laura.rodriguez',
                    'full_name': 'Laura Rodríguez',
                    'password': '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYdR8L6k.6i'
                }
            ]
            
            student_ids = []
            for student in students_data:
                # Verificar si ya existe
                check = await db.execute(text("""
                    SELECT id FROM users WHERE email = :email
                """), {'email': student['email']})
                existing = check.first()
                
                if existing:
                    student_ids.append(existing[0])
                    print(f"+ Estudiante ya existe: {student['email']}")
                else:
                    await db.execute(text("""
                        INSERT INTO users (id, email, username, full_name, hashed_password, roles, is_active)
                        VALUES (:id, :email, :username, :full_name, :password, '["student"]'::jsonb, true)
                    """), {
                        'id': student['id'],
                        'email': student['email'],
                        'username': student['username'],
                        'full_name': student['full_name'],
                        'password': student['password']
                    })
                    
                    student_ids.append(student['id'])
                    print(f"+ Estudiante creado: {student['email']}")
            
            await db.commit()
            print(f"\nTotal de estudiantes: {len(student_ids)}")
            
            # 3. Crear ejercicios para cada actividad
            exercises_templates = [
                {
                    'title': 'Ejercicio Basico',
                    'description': 'Implementa una función que resuelva el problema planteado.',
                    'difficulty': 'EASY',
                    'points': 10
                },
                {
                    'title': 'Ejercicio Intermedio',
                    'description': 'Resuelve un problema de mediana complejidad aplicando los conceptos.',
                    'difficulty': 'MEDIUM',
                    'points': 15
                },
                {
                    'title': 'Ejercicio Avanzado',
                    'description': 'Desafío avanzado que requiere pensamiento crítico.',
                    'difficulty': 'HARD',
                    'points': 20
                }
            ]
            
            total_exercises = 0
            total_submissions = 0
            
            for activity_id, activity_title in activities:
                print(f"\nProcesando actividad: {activity_title}")
                
                # Crear ejercicios
                for i, template in enumerate(exercises_templates):
                    exercise_id = str(uuid.uuid4())
                    
                    await db.execute(text("""
                        INSERT INTO exercises (
                            exercise_id, activity_id, title, description, 
                            difficulty, points, order_index
                        ) VALUES (
                            :exercise_id, :activity_id, :title, :description,
                            :difficulty, :points, :order_index
                        )
                    """), {
                        'exercise_id': exercise_id,
                        'activity_id': activity_id,
                        'title': f"{template['title']} - {activity_title}",
                        'description': template['description'],
                        'difficulty': template['difficulty'],
                        'points': template['points'],
                        'order_index': i
                    })
                    
                    total_exercises += 1
                    print(f"  + Ejercicio creado: {template['title']}")
                    
                    # Crear entregas (submissions) para cada estudiante
                    for student_id in student_ids:
                        submission_id = str(uuid.uuid4())
                        
                        # Variar estados y puntajes
                        import random
                        status_options = ['pending', 'submitted', 'graded', 'graded']  # Más probabilidad de graded
                        status = random.choice(status_options)
                        
                        score = None
                        feedback = None
                        submitted_at = None
                        graded_at = None
                        
                        if status in ['submitted', 'graded']:
                            submitted_at = datetime.now(timezone.utc)
                            
                        if status == 'graded':
                            score = random.randint(5, template['points'])
                            feedback = f"Buen trabajo. Puntaje: {score}/{template['points']}"
                            graded_at = datetime.now(timezone.utc)
                        
                        await db.execute(text("""
                            INSERT INTO submissions (
                                submission_id, exercise_id, student_id, 
                                code, status, score, feedback,
                                submitted_at, graded_at, attempt_number
                            ) VALUES (
                                :submission_id, :exercise_id, :student_id,
                                :code, :status, :score, :feedback,
                                :submitted_at, :graded_at, :attempt_number
                            )
                        """), {
                            'submission_id': submission_id,
                            'exercise_id': exercise_id,
                            'student_id': student_id,
                            'code': f"# Código del estudiante\nprint('Solución al {template['title']}')",
                            'status': status,
                            'score': score,
                            'feedback': feedback,
                            'submitted_at': submitted_at,
                            'graded_at': graded_at,
                            'attempt_number': 1
                        })
                        
                        total_submissions += 1
            
            await db.commit()
            
            print(f"\n{'='*60}")
            print(f"RESUMEN:")
            print(f"   - Estudiantes: {len(student_ids)}")
            print(f"   - Actividades procesadas: {len(activities)}")
            print(f"   - Ejercicios creados: {total_exercises}")
            print(f"   - Entregas (submissions) creadas: {total_submissions}")
            print(f"{'='*60}")
            
            # Mostrar estadisticas por estudiante
            print("\nESTADISTICAS POR ESTUDIANTE:")
            for student_id in student_ids:
                stats = await db.execute(text("""
                    SELECT 
                        u.full_name,
                        COUNT(s.submission_id) as total_submissions,
                        COUNT(CASE WHEN s.status = 'graded' THEN 1 END) as graded,
                        AVG(CASE WHEN s.score IS NOT NULL THEN s.score END) as avg_score
                    FROM users u
                    LEFT JOIN submissions s ON u.id = s.student_id
                    WHERE u.id = :student_id
                    GROUP BY u.full_name
                """), {'student_id': student_id})
                
                stat = stats.first()
                if stat:
                    print(f"   {stat[0]}: {stat[2]} calificadas de {stat[1]} entregas | Promedio: {stat[3]:.1f if stat[3] else 0}")
            
        except Exception as e:
            await db.rollback()
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            raise


if __name__ == "__main__":
    print("Iniciando carga de ejercicios y estudiantes...\n")
    asyncio.run(seed_exercises_and_students())
    print("\nProceso completado!")
