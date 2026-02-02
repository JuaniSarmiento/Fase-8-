"""
Test grading system with new exercises.
"""
import httpx
import asyncio

BASE_URL = "http://localhost:8000/api/v3"

async def test_grading():
    async with httpx.AsyncClient(timeout=120.0) as client:
        print("=" * 60)
        print("TEST: VERIFICAR SISTEMA DE CORRECCION")
        print("=" * 60)
        
        # 1. Get activities
        print("\n[1] Buscando actividades...")
        activities_resp = await client.get(f"{BASE_URL}/teacher/activities", params={"limit": 5})
        if activities_resp.status_code != 200:
            print(f"Error getting activities: {activities_resp.text}")
            return
        
        activities = activities_resp.json()
        if not activities:
            print("No hay actividades")
            return
        
        activity = activities[0]
        activity_id = activity["activity_id"]
        print(f"OK - Actividad: {activity['title']}")
        
        # 2. Get exercises  
        print("\n[2] Buscando ejercicios...")
        exercises_resp = await client.get(f"{BASE_URL}/teacher/activities/{activity_id}/exercises")
        if exercises_resp.status_code != 200:
            print(f"Error: {exercises_resp.text}")
            return
        
        exercises = exercises_resp.json()
        if not exercises:
            print("No hay ejercicios")
            return
        
        print(f"OK - Encontrados {len(exercises)} ejercicios")
        
        # 3. Inspect exercises (find one with solution)
        ex = None
        for e in exercises:
            if e.get('solution_code'):
                ex = e
                break
        
        if not ex:
            ex = exercises[0]
            print("WARN - Ninguno tiene solution_code, usando el primero")
        
        print(f"\n[3] Ejercicio seleccionado: {ex['title']}")
        
        mission = ex.get('mission_markdown', '')
        solution = ex.get('solution_code', '')
        
        print(f"    - Mission: {'SI (' + str(len(mission)) + ' chars)' if mission else 'NO'}")
        print(f"    - Solution: {'SI (' + str(len(solution)) + ' chars)' if solution else 'NO'}")
        
        # 4. Create student session (POST /student/sessions)
        print("\n[4] Iniciando sesion de estudiante...")
        session_resp = await client.post(
            f"{BASE_URL}/student/sessions",
            json={
                "student_id": "test-student-123",
                "activity_id": activity_id,
                "mode": "SOCRATIC"
            }
        )
        
        if session_resp.status_code not in [200, 201]:
            print(f"Error starting session: {session_resp.status_code}")
            print(session_resp.text[:500])
            return
        
        session = session_resp.json()
        session_id = session.get("session_id")
        print(f"OK - Session ID: {session_id}")
        
        # 5. Submit code (POST /student/sessions/{session_id}/submit)
        exercise_id = ex["exercise_id"]
        student_code = solution if solution else "for i in range(10): print(i)"
        
        print(f"\n[5] Enviando codigo para: {ex['title']}")
        print(f"    Codigo ({len(student_code)} chars): {student_code[:80]}...")
        
        submit_resp = await client.post(
            f"{BASE_URL}/student/sessions/{session_id}/submit",
            json={
                "code": student_code,
                "language": "python",
                "exercise_id": exercise_id,
                "is_final_submission": False
            }
        )
        
        if submit_resp.status_code != 200:
            print(f"Error submitting: {submit_resp.status_code}")
            print(submit_resp.text[:800])
            return
        
        result = submit_resp.json()
        
        print("\n" + "=" * 60)
        print("RESULTADO DE LA EVALUACION:")
        print("=" * 60)
        
        grade = result.get('grade', 0)
        tests_passed = result.get('tests_passed', 'N/A')
        passed = result.get('passed', 'N/A')
        feedback = str(result.get('feedback', 'N/A'))
        suggestion = str(result.get('suggestion', 'N/A'))
        
        # Make output ASCII safe
        safe_feedback = ''.join(c if ord(c) < 128 else '?' for c in feedback[:400])
        safe_suggestion = ''.join(c if ord(c) < 128 else '?' for c in suggestion[:200])
        
        print(f"Nota: {grade}/100")
        print(f"Tests pasados: {tests_passed}")
        print(f"Aprobado: {passed}")
        print(f"\nFeedback:\n{safe_feedback}")
        print(f"\nSugerencia:\n{safe_suggestion}")
        
        print("\n" + "=" * 60)
        if grade >= 70:
            print(f"RESULTADO: EXCELENTE - Nota alta ({grade})")
        elif grade >= 50:
            print(f"RESULTADO: REGULAR - Nota media ({grade})")
        else:
            print(f"RESULTADO: REVISAR - Nota baja ({grade})")
        print("=" * 60)
        
        return result

if __name__ == "__main__":
    asyncio.run(test_grading())
