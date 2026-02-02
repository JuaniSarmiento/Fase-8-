"""
Update Luna's submission to show as completed with correct grade.
"""
import subprocess

def run_sql(query):
    subprocess.run([
        'docker', 'exec', 'ai_native_postgres',
        'psql', '-U', 'postgres', '-d', 'ai_native', '-c', query
    ], capture_output=True, text=True, encoding='utf-8')

# Calculate Luna's actual grade based on exercise attempts
result = subprocess.run([
    'docker', 'exec', 'ai_native_postgres',
    'psql', '-U', 'postgres', '-d', 'ai_native', '-t', '-c',
    """
    WITH latest_attempts AS (
        SELECT DISTINCT ON (ea.exercise_id)
            ea.exercise_id,
            ea.passed,
            (ea.test_results->>'grade')::float as grade
        FROM exercise_attempts_v2 ea
        INNER JOIN exercises_v2 e ON e.exercise_id = ea.exercise_id
        WHERE ea.user_id = '70ed9d32-7bf5-4ae2-9aa9-d40ffeba4aea'
          AND e.activity_id = 'e5a83dce-c813-4c9f-acba-53438de9b004'
        ORDER BY ea.exercise_id, ea.submitted_at DESC
    )
    SELECT 
        COUNT(*) as total_attempted,
        SUM(CASE WHEN passed THEN 1 ELSE 0 END) as passed_count,
        ROUND(AVG(grade), 1) as avg_grade
    FROM latest_attempts;
    """
], capture_output=True, text=True, encoding='utf-8')

stats = result.stdout.strip().split('|')
if len(stats) >= 3:
    total_attempted = int(stats[0].strip())
    passed_count = int(stats[1].strip())
    avg_grade = float(stats[2].strip())
    
    print(f"Luna Estudiante - Estadísticas:")
    print(f"  Ejercicios intentados: {total_attempted}")
    print(f"  Ejercicios aprobados: {passed_count}")
    print(f"  Nota promedio: {avg_grade}/100")
    
    # Generate appropriate feedback
    if avg_grade >= 80:
        feedback = f"Buen trabajo. Entiendes los conceptos básicos, sigue practicando. Nota: {avg_grade}/100"
        risk = "BAJO"
    elif avg_grade >= 60:
        feedback = f"Aprobado. Necesitas reforzar algunos conceptos de iteración. Nota: {avg_grade}/100"
        risk = "MEDIO"
    else:
        feedback = f"⚠️ EN RIESGO: Requiere atención. Se recomienda tutoría. Nota: {avg_grade}/100"
        risk = "ALTO"
    
    print(f"  Feedback: {feedback}")
    print(f"  Nivel de riesgo: {risk}")
    
    # Update submission
    update_query = f"""
        UPDATE submissions
        SET status = 'completed',
            auto_grade = {avg_grade},
            final_grade = {avg_grade},
            ai_feedback = '{feedback}',
            test_results = jsonb_set(
                COALESCE(test_results, '{{}}'::jsonb),
                '{{risk_level}}',
                '"{risk}"'::jsonb
            )
        WHERE student_id = '70ed9d32-7bf5-4ae2-9aa9-d40ffeba4aea'
          AND activity_id = 'e5a83dce-c813-4c9f-acba-53438de9b004';
    """
    
    run_sql(update_query)
    print("\n✅ Submission actualizada exitosamente!")
    print(f"   Estado: completed | Nota: {avg_grade}/100 | Riesgo: {risk}")

else:
    print("Error al obtener estadísticas")
