"""
Demo del flujo completo de evaluación y cómo el profesor accede a los datos.
"""
import subprocess
import json

def run_sql_json(query):
    """Execute SQL query and return JSON output."""
    result = subprocess.run([
        'docker', 'exec', 'ai_native_postgres',
        'psql', '-U', 'postgres', '-d', 'ai_native', '-t', '-c', query
    ], capture_output=True, text=True, encoding='utf-8')
    return result.stdout.strip()

print("="*80)
print("DEMOSTRACIÓN: FLUJO COMPLETO DE EVALUACIÓN")
print("="*80)

# 1. Ver estudiantes
print("\n1️⃣ ESTUDIANTES EN EL SISTEMA:")
print("-" * 80)
students_json = run_sql_json("""
    SELECT json_agg(row_to_json(t))
    FROM (
        SELECT id, username, full_name, role
        FROM users
        WHERE role = 'student'
        LIMIT 5
    ) t;
""")
students = json.loads(students_json) if students_json and students_json != 'null' else []
for student in students:
    print(f"   👤 {student['full_name']} ({student['username']})")
    print(f"      ID: {student['id']}")

# 2. Ver intentos de ejercicios de un estudiante
print("\n\n2️⃣ INTENTOS DE EJERCICIOS - Luna Estudiante:")
print("-" * 80)
attempts_json = run_sql_json("""
    SELECT json_agg(row_to_json(t))
    FROM (
        SELECT 
            e.title,
            e.difficulty::text,
            ea.passed,
            ea.test_results->>'grade' as grade,
            ea.test_results->>'feedback' as feedback,
            ea.submitted_at::text
        FROM exercise_attempts_v2 ea
        INNER JOIN exercises_v2 e ON e.exercise_id = ea.exercise_id
        WHERE ea.user_id = '70ed9d32-7bf5-4ae2-9aa9-d40ffeba4aea'
        ORDER BY ea.submitted_at DESC
        LIMIT 5
    ) t;
""")
attempts = json.loads(attempts_json) if attempts_json and attempts_json != 'null' else []
for attempt in attempts:
    status = "✅ Aprobado" if attempt['passed'] == 't' or attempt['passed'] == True else "❌ Fallido"
    print(f"\n   📝 {attempt['title']} ({attempt['difficulty']})")
    print(f"      Status: {status} | Nota: {attempt['grade']}/100")
    print(f"      Feedback: {attempt['feedback'][:100]}...")
    print(f"      Fecha: {attempt['submitted_at'][:19]}")

# 3. Ver envíos finales de actividades
print("\n\n3️⃣ ENVÍOS FINALES DE ACTIVIDADES:")
print("-" * 80)
submissions_json = run_sql_json("""
    SELECT json_agg(row_to_json(t))
    FROM (
        SELECT 
            a.title,
            s.status::text,
            s.auto_grade,
            s.ai_feedback,
            s.submitted_at::text,
            s.test_results
        FROM submissions s
        INNER JOIN activities a ON a.activity_id = s.activity_id
        WHERE s.student_id = '70ed9d32-7bf5-4ae2-9aa9-d40ffeba4aea'
        ORDER BY s.submitted_at DESC
        LIMIT 3
    ) t;
""")
submissions = json.loads(submissions_json) if submissions_json and submissions_json != 'null' else []
for submission in submissions:
    print(f"\n   🎓 {submission['title']}")
    print(f"      Status: {submission['status']} | Nota: {submission['auto_grade']}/100")
    print(f"      Feedback: {submission['ai_feedback']}")
    print(f"      Fecha: {submission['submitted_at'][:19]}")
    
    # Check for risk analysis
    if submission['test_results']:
        risk = submission['test_results'].get('risk_level', 'N/A')
        completion_rate = submission['test_results'].get('completion_rate', 0)
        print(f"      Riesgo: {risk} | Completitud: {completion_rate}%")

# 4. Ver sesiones activas
print("\n\n4️⃣ SESIONES DE PRÁCTICA:")
print("-" * 80)
sessions_json = run_sql_json("""
    SELECT json_agg(row_to_json(t))
    FROM (
        SELECT 
            a.title,
            s.status::text,
            s.start_time::text,
            s.end_time::text,
            s.session_metrics
        FROM sessions_v2 s
        LEFT JOIN activities a ON a.activity_id = s.activity_id
        WHERE s.user_id = '70ed9d32-7bf5-4ae2-9aa9-d40ffeba4aea'
        ORDER BY s.start_time DESC
        LIMIT 3
    ) t;
""")
sessions = json.loads(sessions_json) if sessions_json and sessions_json != 'null' else []
for session in sessions:
    status_emoji = "🟢" if session['status'] == 'active' else "🔴"
    activity_name = session['title'] if session['title'] else "Sin actividad"
    print(f"\n   {status_emoji} {activity_name}")
    print(f"      Status: {session['status']}")
    print(f"      Inicio: {session['start_time'][:19] if session['start_time'] else 'N/A'}")
    print(f"      Fin: {session['end_time'][:19] if session['end_time'] else 'En progreso'}")

print("\n\n" + "="*80)
print("RESUMEN PARA EL PROFESOR:")
print("="*80)
print("""
📊 El profesor puede ver:

1. exercise_attempts_v2: 
   - Cada intento individual de ejercicio
   - Código enviado, nota, feedback detallado, si pasó o no
   - Timestamp de cuándo se envió

2. submissions:
   - Envío final completo de la actividad
   - Nota global, feedback general
   - Análisis de riesgo (BAJO/MEDIO/ALTO)
   - Tasa de completitud

3. sessions_v2:
   - Sesiones de práctica del estudiante
   - Métricas de la sesión (tiempo, interacciones)
   - Estado cognitivo (opcional)

4. Tutor de IA (chat):
   - No se registran las conversaciones por ahora
   - Solo se procesan en tiempo real con RAG + Mistral
   
✅ TODO está guardado en PostgreSQL y accesible para análisis del profesor.
""")

print("="*80)
