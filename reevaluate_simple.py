"""
Re-evaluate old exercise attempts using docker exec and Mistral AI.
"""
import subprocess
import json
import os
import sys
from langchain_mistralai import ChatMistralAI

# Set UTF-8 encoding for console output
sys.stdout.reconfigure(encoding='utf-8')

def run_sql_json(query):
    """Execute SQL query and return JSON output."""
    result = subprocess.run([
        'docker', 'exec', 'ai_native_postgres',
        'psql', '-U', 'postgres', '-d', 'ai_native', '-t', '-c', query
    ], capture_output=True, text=True)
    return result.stdout.strip()

def run_sql_update(query):
    """Execute UPDATE SQL query."""
    subprocess.run([
        'docker', 'exec', 'ai_native_postgres',
        'psql', '-U', 'postgres', '-d', 'ai_native', '-c', query
    ], capture_output=True, text=True)

def reevaluate_attempts():
    """Re-evaluate all exercise attempts with old feedback."""
    
    print("Searching for attempts with old feedback...\n")
    
    # Get attempts that need re-evaluation as JSON array
    attempts_output = run_sql_json("""
        SELECT json_agg(row_to_json(t))
        FROM (
            SELECT 
                ea.attempt_id,
                ea.code_submitted,
                e.title,
                e.mission_markdown,
                e.difficulty::text
            FROM exercise_attempts_v2 ea
            INNER JOIN exercises_v2 e ON e.exercise_id = ea.exercise_id
            WHERE ea.test_results IS NOT NULL
              AND ea.test_results::text LIKE '%evaluación manual%'
            ORDER BY ea.submitted_at DESC
        ) t;
    """)
    
    if not attempts_output or attempts_output == 'null':
        print("No attempts need re-evaluation. All feedback is up to date!")
        return
    
    attempts = json.loads(attempts_output)
    if not attempts:
        print("No attempts need re-evaluation. All feedback is up to date!")
        return
    
    print(f"Found {len(attempts)} attempts to re-evaluate\n")
    
    # Initialize Mistral AI
    mistral_api_key = os.getenv("MISTRAL_API_KEY")
    if not mistral_api_key:
        print("ERROR: MISTRAL_API_KEY not found in environment variables")
        return
    
    llm = ChatMistralAI(
        model="mistral-small-latest",
        api_key=mistral_api_key,
        temperature=0.3
    )
    
    updated_count = 0
    
    for attempt in attempts:
        attempt_id = attempt['attempt_id']
        code_submitted = attempt['code_submitted']
        exercise_title = attempt['title']
        exercise_mission = attempt['mission_markdown']
        exercise_difficulty = attempt['difficulty']
        
        print(f"\nRe-evaluating: {exercise_title}")
        print(f"  Attempt ID: {attempt_id[:20]}...")
        print(f"  Code length: {len(code_submitted)} chars")
        
        # AI Evaluation with improved prompt
        evaluation_prompt = f"""Eres un profesor evaluando código Python de un estudiante.

EJERCICIO: {exercise_title}
DIFICULTAD: {exercise_difficulty}

CONSIGNA:
{exercise_mission}

CÓDIGO DEL ESTUDIANTE:
```python
{code_submitted}
```

Evalúa el código ESTRICTAMENTE y proporciona:
1. NOTA (0-100): 
   - 90-100: Código excelente, limpio, eficiente, maneja casos edge
   - 70-89: Código correcto pero con áreas de mejora
   - 50-69: Código funcional pero con errores menores o ineficiencias
   - 30-49: Código incompleto o con errores significativos
   - 0-29: Código vacío, solo comentarios/TODOs, o no cumple la consigna

2. CORRECTO (true/false): true SOLO si el código cumple TODOS los requisitos y funciona correctamente

3. FEEDBACK (2-4 líneas): EXPLICA ESPECÍFICAMENTE:
   - ¿Por qué esa nota? (menciona qué hizo bien o mal)
   - Si tiene errores, ¿cuáles?
   - ¿Qué debe mejorar para obtener mejor nota?

Respuesta OBLIGATORIA en formato JSON:
{{
  "grade": 85,
  "is_correct": true,
  "feedback": "✅ 85/100: Implementación correcta. Falta validación de entrada (-10) y documentación (-5)."
}}"""
        
        try:
            response = llm.invoke(evaluation_prompt)
            response_text = response.content.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                response_text = response_text.split('\n', 1)[1] if '\n' in response_text else response_text[3:]
                if response_text.endswith('```'):
                    response_text = response_text[:-3]
                response_text = response_text.strip()
            
            eval_data = json.loads(response_text)
            new_grade = eval_data.get("grade", 0)
            is_correct = eval_data.get("is_correct", False)
            new_feedback = eval_data.get("feedback", "Evaluación completada.")
            
            print(f"  New grade: {new_grade}/100")
            print(f"  New feedback: {new_feedback[:80]}...")
            
            # Update test_results in database
            new_test_results = json.dumps({
                "grade": new_grade,
                "feedback": new_feedback,
                "evaluated_at": "2026-01-28T00:00:00",
                "re_evaluated": True
            })
            
            # Escape single quotes for SQL
            new_test_results_escaped = new_test_results.replace("'", "''")
            
            update_query = f"""
                UPDATE exercise_attempts_v2
                SET test_results = '{new_test_results_escaped}'::jsonb,
                    passed = {str(is_correct).lower()}
                WHERE attempt_id = '{attempt_id}';
            """
            
            run_sql_update(update_query)
            updated_count += 1
            print(f"  ✅ Updated successfully\n")
            
        except Exception as e:
            print(f"  ❌ Error: {str(e)}\n")
    
    print(f"\n{'='*60}")
    print(f"Re-evaluation complete!")
    print(f"Updated {updated_count} out of {len(attempts)} attempts")
    print(f"{'='*60}")

if __name__ == "__main__":
    reevaluate_attempts()
