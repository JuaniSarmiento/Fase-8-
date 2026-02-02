"""
Script para poblar la base de datos con estudiantes, ejercicios v2 y entregas.
"""
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4
import random
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    print("Iniciando seed de estudiantes y ejercicios v2...")
    
    # Datos de estudiantes
    students_data = [
        {
            'id': str(uuid4()),
            'email': 'maria.garcia@student.com',
            'username': 'maria.garcia',
            'full_name': 'Maria Garcia',
            'password': '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYdR8L6k.6i'  # 123456
        },
        {
            'id': str(uuid4()),
            'email': 'juan.perez@student.com',
            'username': 'juan.perez',
            'full_name': 'Juan Perez',
            'password': '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYdR8L6k.6i'
        },
        {
            'id': str(uuid4()),
            'email': 'ana.martinez@student.com',
            'username': 'ana.martinez',
            'full_name': 'Ana Martinez',
            'password': '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYdR8L6k.6i'
        },
        {
            'id': str(uuid4()),
            'email': 'carlos.lopez@student.com',
            'username': 'carlos.lopez',
            'full_name': 'Carlos Lopez',
            'password': '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYdR8L6k.6i'
        },
        {
            'id': str(uuid4()),
            'email': 'laura.rodriguez@student.com',
            'username': 'laura.rodriguez',
            'full_name': 'Laura Rodriguez',
            'password': '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYdR8L6k.6i'
        }
    ]
    
    try:
        # Conectar a la base de datos
        engine = create_async_engine(
            'postgresql+asyncpg://postgres:postgres@localhost:5433/ai_native',
            echo=False
        )
        
        async with engine.begin() as conn:
            print("+ Conexion a base de datos establecida")
            
            # 1. Verificar y crear estudiantes
            print("\n+ Verificando/creando estudiantes...")
            
            # Primero obtener estudiantes existentes por username o email
            existing_result = await conn.execute(text("""
                SELECT id, email, username FROM users WHERE roles @> '["student"]'::jsonb
            """))
            existing_by_email = {}
            existing_by_username = {}
            for row in existing_result.fetchall():
                existing_by_email[row[1]] = row[0]  # email -> id
                existing_by_username[row[2]] = row[0]  # username -> id
            
            student_ids = []
            for student in students_data:
                if student['email'] in existing_by_email:
                    student_ids.append(existing_by_email[student['email']])
                    print(f"  + Estudiante ya existe (email): {student['full_name']}")
                elif student['username'] in existing_by_username:
                    student_ids.append(existing_by_username[student['username']])
                    print(f"  + Estudiante ya existe (username): {student['full_name']}")
                else:
                    # Crear nuevo estudiante
                    await conn.execute(text("""
                        INSERT INTO users (id, email, username, full_name, hashed_password, roles, is_active)
                        VALUES (:id, :email, :username, :full_name, :password, '["student"]'::jsonb, true)
                    """), student)
                    student_ids.append(student['id'])
                    print(f"  + Estudiante creado: {student['full_name']}")
            
            # Actualizar students_data con IDs existentes
            for i, student in enumerate(students_data):
                student['id'] = student_ids[i]
            
            # 2. Obtener actividades existentes
            result = await conn.execute(text("""
                SELECT activity_id, title, subject, unit_id 
                FROM activities 
                WHERE deleted_at IS NULL
                ORDER BY created_at
            """))
            activities = result.fetchall()
            
            if not activities:
                print("No hay actividades en la base de datos")
                return
            
            print(f"\n+ Encontradas {len(activities)} actividades")
            
            # 3. Crear ejercicios vinculados a subjects
            print("\n+ Creando ejercicios para cada actividad...")
            exercise_templates = [
                {
                    'title': 'Ejercicio Basico',
                    'difficulty': 'FACIL',
                    'estimated_time': 15,
                    'mission': 'Implementa una funcion basica que resuelva el problema planteado.',
                    'starter_code': 'def resolver():\n    # Tu codigo aqui\n    pass',
                    'solution_code': 'def resolver():\n    return "Solucion"\n'
                },
                {
                    'title': 'Ejercicio Intermedio',
                    'difficulty': 'INTERMEDIO',
                    'estimated_time': 30,
                    'mission': 'Implementa una solucion mas compleja con manejo de casos especiales.',
                    'starter_code': 'def resolver_intermedio():\n    # Tu codigo aqui\n    pass',
                    'solution_code': 'def resolver_intermedio():\n    return "Solucion intermedia"\n'
                },
                {
                    'title': 'Ejercicio Avanzado',
                    'difficulty': 'DIFICIL',
                    'estimated_time': 45,
                    'mission': 'Implementa una solucion optima considerando eficiencia y edge cases.',
                    'starter_code': 'def resolver_avanzado():\n    # Tu codigo aqui\n    pass',
                    'solution_code': 'def resolver_avanzado():\n    return "Solucion avanzada"\n'
                }
            ]
            
            created_exercises = {}
            
            for activity in activities:
                activity_id = activity[0]
                activity_title = activity[1]
                subject_name = activity[2] or 'Python'
                
                # Get or create subject
                subject_result = await conn.execute(text("""
                    SELECT subject_id FROM subjects WHERE name = :name LIMIT 1
                """), {'name': subject_name})
                subject_row = subject_result.fetchone()
                
                if not subject_row:
                    # Create subject if doesn't exist
                    subject_id = str(uuid4())
                    code = subject_name[:20].upper().replace(' ', '_')
                    await conn.execute(text("""
                        INSERT INTO subjects (subject_id, code, name, credits)
                        VALUES (:subject_id, :code, :name, :credits)
                        ON CONFLICT (code) DO NOTHING
                    """), {
                        'subject_id': subject_id,
                        'code': code,
                        'name': subject_name,
                        'credits': 3
                    })
                    print(f"  + Materia creada: {subject_name} ({code})")
                    # Re-fetch to get the subject_id if there was a conflict
                    subject_result = await conn.execute(text("""
                        SELECT subject_id FROM subjects WHERE code = :code LIMIT 1
                    """), {'code': code})
                    subject_row = subject_result.fetchone()
                    subject_id = subject_row[0]
                else:
                    subject_id = subject_row[0]
                
                print(f"\n  Actividad: {activity_title}")
                created_exercises[activity_id] = []
                
                for idx, template in enumerate(exercise_templates):
                    exercise_id = str(uuid4())
                    
                    await conn.execute(text("""
                        INSERT INTO exercises_v2 (
                            exercise_id, title, description, subject_id, unit_number,
                            difficulty, language, mission_markdown, starter_code, 
                            solution_code, estimated_time_minutes, tags
                        ) VALUES (
                            :exercise_id, :title, :description, :subject_id, :unit_number,
                            :difficulty, :language, :mission_markdown, :starter_code,
                            :solution_code, :estimated_time_minutes, :tags
                        )
                    """), {
                        'exercise_id': exercise_id,
                        'title': f"{template['title']} - {activity_title}",
                        'description': f"Ejercicio {template['difficulty']} para la actividad {activity_title}",
                        'subject_id': subject_id,
                        'unit_number': 1,
                        'difficulty': template['difficulty'],
                        'language': 'PYTHON',
                        'mission_markdown': template['mission'],
                        'starter_code': template['starter_code'],
                        'solution_code': template['solution_code'],
                        'estimated_time_minutes': template['estimated_time'],
                        'tags': '["autogenerado", "seed"]'
                    })
                    
                    created_exercises[activity_id].append(exercise_id)
                    print(f"    + Ejercicio {template['difficulty']}: {exercise_id[:8]}...")
            
            # 4. Crear sesiones y ejercicios intentos (submissions)
            print("\n+ Creando sesiones y entregas de estudiantes...")
            
            for activity in activities:
                activity_id = activity[0]
                activity_title = activity[1]
                
                print(f"\n  Actividad: {activity_title}")
                
                # Cada estudiante tiene una sesion para esta actividad
                for student in students_data:
                    session_id = str(uuid4())
                    
                    # Create session
                    await conn.execute(text("""
                        INSERT INTO sessions_v2 (
                            session_id, user_id, activity_id, status, mode,
                            learning_objective, start_time
                        ) VALUES (
                            :session_id, :user_id, :activity_id, :status, :mode,
                            :learning_objective, :start_time
                        )
                    """), {
                        'session_id': session_id,
                        'user_id': student['id'],
                        'activity_id': activity_id,
                        'status': 'ACTIVE',
                        'mode': 'DIRECT',
                        'learning_objective': f'Completar actividad: {activity_title}',
                        'start_time': datetime.now() - timedelta(days=random.randint(1, 10))
                    })
                    
                    # Create attempts for each exercise
                    for exercise_id in created_exercises.get(activity_id, []):
                        # Random number of attempts (1-3)
                        num_attempts = random.randint(1, 3)
                        
                        for attempt_num in range(num_attempts):
                            attempt_id = str(uuid4())
                            passed = random.choice([True, False, True])  # 66% pass rate
                            
                            code_samples = [
                                f"def resolver():\n    return {random.randint(1, 100)}",
                                f"def resolver():\n    resultado = {random.randint(1, 100)}\n    return resultado",
                                "def resolver():\n    # Intentando resolver\n    return None"
                            ]
                            
                            await conn.execute(text("""
                                INSERT INTO exercise_attempts_v2 (
                                    attempt_id, exercise_id, user_id, session_id,
                                    code_submitted, passed, execution_output, test_results,
                                    submitted_at
                                ) VALUES (
                                    :attempt_id, :exercise_id, :user_id, :session_id,
                                    :code_submitted, :passed, :execution_output, :test_results,
                                    :submitted_at
                                )
                            """), {
                                'attempt_id': attempt_id,
                                'exercise_id': exercise_id,
                                'user_id': student['id'],
                                'session_id': session_id,
                                'code_submitted': random.choice(code_samples),
                                'passed': passed,
                                'execution_output': f'{{"output": "Resultado del intento {attempt_num + 1}"}}',
                                'test_results': f'{{"tests_passed": {1 if passed else 0}, "tests_total": 1}}',
                                'submitted_at': datetime.now() - timedelta(days=random.randint(0, 7))
                            })
                    
                    print(f"    + Sesion creada para {student['full_name']}")
            
            print("\n+ Seed completado exitosamente!")
            
            # Estadisticas
            result = await conn.execute(text("SELECT COUNT(*) FROM users WHERE roles @> '[\"student\"]'::jsonb"))
            student_count = result.scalar()
            
            result = await conn.execute(text("SELECT COUNT(*) FROM exercises_v2"))
            exercise_count = result.scalar()
            
            result = await conn.execute(text("SELECT COUNT(*) FROM exercise_attempts_v2"))
            attempt_count = result.scalar()
            
            result = await conn.execute(text("SELECT COUNT(*) FROM sessions_v2"))
            session_count = result.scalar()
            
            print("\nEstadisticas:")
            print(f"  Estudiantes: {student_count}")
            print(f"  Ejercicios: {exercise_count}")
            print(f"  Sesiones: {session_count}")
            print(f"  Intentos: {attempt_count}")
    
    except Exception as e:
        print(f"\nError durante el seed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
