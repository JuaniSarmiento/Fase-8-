"""
Re-evaluate all old exercise attempts with new improved AI feedback system.
Updates test_results in exercise_attempts_v2 table.
"""
import json
import os
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from langchain_mistralai import ChatMistralAI

# Database configuration
DATABASE_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'ai_native',
    'user': 'postgres',
    'password': 'postgres'
}

def reevaluate_attempts():
    """Re-evaluate all exercise attempts with old feedback."""
    
    conn = psycopg2.connect(**DATABASE_CONFIG)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Get all attempts that need re-evaluation (old generic feedback)
        cursor.execute("""
            SELECT 
                ea.attempt_id,
                ea.exercise_id,
                ea.code_submitted,
                ea.test_results,
                e.title,
                e.mission_markdown,
                e.difficulty::text
            FROM exercise_attempts_v2 ea
            INNER JOIN exercises_v2 e ON e.exercise_id = ea.exercise_id
            WHERE ea.test_results IS NOT NULL
              AND ea.test_results::text LIKE '%evaluación manual%'
            ORDER BY ea.submitted_at DESC
        """)
        
        attempts = cursor.fetchall()
        
        print(f"Found {len(attempts)} attempts to re-evaluate\n")
        
        if len(attempts) == 0:
            print("No attempts need re-evaluation. All feedback is up to date!")
            return
        
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
            old_test_results = attempt['test_results']
            exercise_title = attempt['title']
            exercise_mission = attempt['mission_markdown']
            exercise_difficulty = attempt['difficulty']
            
            print(f"Re-evaluating: {exercise_title}")
            print(f"  Attempt ID: {attempt_id}")
            print(f"  Old feedback: {old_test_results.get('feedback', 'N/A')[:60]}...")
            
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
   
EJEMPLOS DE BUEN FEEDBACK:
- "✅ 85/100: Implementación correcta del bucle for. Falta manejo de listas vacías (-10) y nombres de variables poco descriptivos (-5)."
- "❌ 45/100: El código tiene error de sintaxis en línea 3 (falta ':' en el for). La lógica es correcta pero no ejecuta."
- "❌ 20/100: Solo tiene comentarios y 'pass'. No hay implementación real del ejercicio."

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
                new_test_results = {
                    "grade": new_grade,
                    "feedback": new_feedback,
                    "evaluated_at": datetime.utcnow().isoformat(),
                    "re_evaluated": True
                }
                
                cursor.execute("""
                    UPDATE exercise_attempts_v2
                    SET test_results = %s,
                        passed = %s
                    WHERE attempt_id = %s
                """, (
                    json.dumps(new_test_results),
                    is_correct,
                    attempt_id
                ))
                
                conn.commit()
                updated_count += 1
                print(f"  ✅ Updated successfully\n")
                
            except Exception as e:
                print(f"  ❌ Error: {str(e)}\n")
                conn.rollback()
        
        print(f"\n{'='*60}")
        print(f"Re-evaluation complete!")
        print(f"Updated {updated_count} out of {len(attempts)} attempts")
        print(f"{'='*60}")
        
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    reevaluate_attempts()
