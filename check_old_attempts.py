import subprocess
import json

# Run SQL directly in container
result = subprocess.run([
    'docker', 'exec', 'ai_native_postgres',
    'psql', '-U', 'postgres', '-d', 'ai_native', '-t', '-c',
    '''SELECT 
        ea.attempt_id,
        ea.code_submitted,
        ea.test_results->>'feedback' as old_feedback,
        e.title,
        e.mission_markdown,
        e.difficulty::text
    FROM exercise_attempts_v2 ea
    INNER JOIN exercises_v2 e ON e.exercise_id = ea.exercise_id
    WHERE ea.test_results IS NOT NULL
      AND ea.test_results::text LIKE '%evaluación manual%'
    LIMIT 3;'''
], capture_output=True, text=True)

print("Attempts that need re-evaluation:")
print(result.stdout)
