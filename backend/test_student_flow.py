"""
Test E2E: Flujo completo de estudiante
Simula: Iniciar sesión -> Hablar con tutor -> Enviar código -> Evaluar nota

Ejecutar: python test_student_flow.py
"""
import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v3"
ACTIVITY_ID = "497b3fc2-fd0b-42b2-90e8-2a00dc737b64"  # Actividad Bucles
STUDENT_ID = "alumno-001"


async def test_student_flow():
    """Simula el flujo completo de un estudiante."""
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        print("=" * 60)
        print("TEST E2E: FLUJO COMPLETO DE ESTUDIANTE")
        print("=" * 60)
        
        # 1. Iniciar sesión
        print("\n📌 PASO 1: Iniciando sesión...")
        session_resp = await client.post(f"{BASE_URL}/student/sessions", json={
            "student_id": STUDENT_ID,
            "activity_id": ACTIVITY_ID,
            "mode": "SOCRATIC"
        })
        
        if session_resp.status_code not in [200, 201]:
            print(f"❌ Error iniciando sesión: {session_resp.status_code}")
            print(session_resp.text)
            return
        
        session_data = session_resp.json()
        session_id = session_data["session_id"]
        print(f"✅ Sesión iniciada: {session_id}")
        
        # 2. Obtener ejercicios
        print("\n📌 PASO 2: Obteniendo ejercicios...")
        exercises_resp = await client.get(f"{BASE_URL}/student/activities/{ACTIVITY_ID}/exercises")
        
        if exercises_resp.status_code != 200:
            print(f"❌ Error obteniendo ejercicios: {exercises_resp.status_code}")
            return
        
        exercises = exercises_resp.json()
        print(f"✅ Ejercicios obtenidos: {len(exercises)}")
        
        if not exercises:
            print("❌ No hay ejercicios")
            return
        
        exercise = exercises[0]
        exercise_id = exercise["exercise_id"]
        print(f"   📝 Ejercicio 1: {exercise['title']}")
        print(f"   📋 Descripción: {exercise.get('description', 'N/A')[:100]}...")
        
        # 3. Chatear con el tutor
        print("\n📌 PASO 3: Chateando con el tutor...")
        chat_resp = await client.post(f"{BASE_URL}/student/sessions/{session_id}/chat", json={
            "message": "Hola, ¿puedes ayudarme con este ejercicio de bucles?",
            "code_context": "",
            "exercise_context": {
                "title": exercise.get("title"),
                "description": exercise.get("description"),
                "mission": exercise.get("mission_markdown")
            }
        })
        
        if chat_resp.status_code == 200:
            tutor_response = chat_resp.json()
            print(f"✅ Respuesta del tutor: {tutor_response.get('content', 'N/A')[:200]}...")
        else:
            print(f"⚠️ Chat falló (continuando): {chat_resp.status_code}")
        
        # 4. Enviar código CORRECTO
        print("\n📌 PASO 4: Enviando código CORRECTO...")
        correct_code = '''
def iterar_cadena(texto):
    """Imprime cada carácter de la cadena con su índice."""
    for indice, caracter in enumerate(texto):
        print(f"Índice: {indice}, Carácter: {caracter}")

# Prueba
iterar_cadena("Hola")
'''
        
        submit_resp = await client.post(f"{BASE_URL}/student/sessions/{session_id}/submit", json={
            "code": correct_code,
            "language": "python",
            "exercise_id": exercise_id,
            "is_final_submission": False
        })
        
        if submit_resp.status_code == 200:
            result = submit_resp.json()
            print(f"✅ Código enviado correctamente")
            print(f"   📊 Nota: {result.get('grade')}/100")
            print(f"   ✔️ Tests pasaron: {result.get('tests_passed')}")
            print(f"   💬 Feedback: {result.get('feedback', 'N/A')[:200]}...")
            print(f"   💡 Sugerencia: {result.get('suggestion', 'N/A')[:150]}...")
            
            grade_correct = result.get('grade', 0)
        else:
            print(f"❌ Error enviando código: {submit_resp.status_code}")
            print(submit_resp.text)
            return
        
        # 5. Enviar código INCORRECTO (para comparar)
        print("\n📌 PASO 5: Enviando código INCORRECTO...")
        incorrect_code = '''
def iterar_cadena(texto):
    # Código incompleto
    pass
'''
        
        submit_resp_2 = await client.post(f"{BASE_URL}/student/sessions/{session_id}/submit", json={
            "code": incorrect_code,
            "language": "python",
            "exercise_id": exercise_id,
            "is_final_submission": False
        })
        
        if submit_resp_2.status_code == 200:
            result_2 = submit_resp_2.json()
            print(f"✅ Código incorrecto enviado")
            print(f"   📊 Nota: {result_2.get('grade')}/100")
            print(f"   ✔️ Tests pasaron: {result_2.get('tests_passed')}")
            print(f"   💬 Feedback: {result_2.get('feedback', 'N/A')[:200]}...")
            
            grade_incorrect = result_2.get('grade', 0)
        else:
            print(f"❌ Error: {submit_resp_2.status_code}")
        
        # 6. Enviar código con ERROR DE SINTAXIS
        print("\n📌 PASO 6: Enviando código con ERROR DE SINTAXIS...")
        syntax_error_code = '''
def iterar_cadena(texto)
    print("Falta los dos puntos")
'''
        
        submit_resp_3 = await client.post(f"{BASE_URL}/student/sessions/{session_id}/submit", json={
            "code": syntax_error_code,
            "language": "python",
            "exercise_id": exercise_id,
            "is_final_submission": False
        })
        
        if submit_resp_3.status_code == 200:
            result_3 = submit_resp_3.json()
            print(f"✅ Código con error enviado")
            print(f"   📊 Nota: {result_3.get('grade')}/100")
            print(f"   ❌ Error detectado: {'stderr' in result_3.get('execution', {})}")
            print(f"   💬 Feedback: {result_3.get('feedback', 'N/A')[:200]}...")
            
            grade_syntax_error = result_3.get('grade', 0)
        else:
            print(f"❌ Error: {submit_resp_3.status_code}")
        
        # 7. RESUMEN Y ANÁLISIS
        print("\n" + "=" * 60)
        print("📊 RESUMEN DE LA EVALUACIÓN")
        print("=" * 60)
        print(f"   Código CORRECTO:      {grade_correct}/100")
        print(f"   Código INCORRECTO:    {grade_incorrect}/100")
        print(f"   Código ERROR SINTAX:  {grade_syntax_error}/100")
        
        print("\n🔍 ANÁLISIS:")
        if grade_correct > grade_incorrect and grade_incorrect > grade_syntax_error:
            print("   ✅ El sistema diferencia correctamente entre los 3 tipos de código")
        else:
            print("   ⚠️ PROBLEMA: Las notas no reflejan la calidad del código")
            if grade_correct <= grade_incorrect:
                print("      - Código correcto tiene nota igual o menor que incorrecto")
            if grade_incorrect <= grade_syntax_error:
                print("      - Código incorrecto tiene nota igual o menor que código con error")
        
        if grade_correct >= 80:
            print("   ✅ Código correcto tiene nota aprobatoria (>=80)")
        else:
            print(f"   ⚠️ Código correcto tiene nota baja ({grade_correct}). Debería ser >= 80")
        
        if grade_syntax_error < 30:
            print("   ✅ Código con error de sintaxis tiene nota muy baja (correctamente)")
        else:
            print(f"   ⚠️ Código con error de sintaxis tiene nota alta ({grade_syntax_error}). Debería ser < 30")


if __name__ == "__main__":
    import sys
    # Also write to file
    with open("test_results.txt", "w", encoding="utf-8") as f:
        class Tee:
            def __init__(self, *files):
                self.files = files
            def write(self, x):
                for file in self.files:
                    file.write(x)
                    file.flush()
            def flush(self):
                for file in self.files:
                    file.flush()
        
        old_stdout = sys.stdout
        sys.stdout = Tee(sys.stdout, f)
        asyncio.run(test_student_flow())
        sys.stdout = old_stdout
    
    print("\n📁 Resultados guardados en test_results.txt")
