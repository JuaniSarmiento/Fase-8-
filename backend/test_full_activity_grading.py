"""
Test script to simulate a student completing an entire activity (all exercises).
It submits the reference solution for each exercise and reports:
1. Grade per exercise
2. Feedback per exercise
3. Final average grade
"""
import httpx
import asyncio
import json
import time

BASE_URL = "http://localhost:8000/api/v3"

async def wait_for_backend():
    print("Waiting for backend...")
    async with httpx.AsyncClient(timeout=5.0) as client:
        for i in range(10):
            try:
                resp = await client.get("http://localhost:8000/health")
                if resp.status_code == 200:
                    print("Backend is UP!")
                    return True
            except:
                pass
            print(".", end="", flush=True)
            await asyncio.sleep(1)
    return False

async def run_full_activity_test():
    if not await wait_for_backend():
        print("Backend not available.")
        return

    async with httpx.AsyncClient(timeout=120.0) as client:
        print("\n" + "=" * 60)
        print("TEST: EVALUACIÓN COMPLETA DE ACTIVIDAD (10 EJERCICIOS)")
        print("=" * 60)
        
        # 1. Get activities
        activities_resp = await client.get(f"{BASE_URL}/teacher/activities", params={"limit": 5})
        activities = activities_resp.json()
        
        if not activities:
            print("No hay actividades disponibles.")
            return
            
        # Select activity with exercises
        activity = activities[0]
        activity_id = activity["activity_id"]
        print(f"Actividad Seleccionada: {activity['title']}")
        
        # 2. Get exercises
        exercises_resp = await client.get(f"{BASE_URL}/teacher/activities/{activity_id}/exercises")
        exercises = exercises_resp.json()
        
        if not exercises:
            print("La actividad no tiene ejercicios.")
            return

        print(f"Total Ejercicios: {len(exercises)}")
        
        # 3. Start Session
        session_resp = await client.post(
            f"{BASE_URL}/student/sessions",
            json={
                "student_id": "test-student-full-run",
                "activity_id": activity_id
            }
        )
        session_id = session_resp.json().get("session_id")
        print(f"Sesión iniciada: {session_id}\n")
        
        results = []
        
        # 4. Submit all exercises
        for i, ex in enumerate(exercises):
            print(f"Evaluanado Ejercicio {i+1}/{len(exercises)}: {ex['title']}...")
            
            # Use solution code or fallback if missing (to see how AI reacts)
            student_code = ex.get('solution_code')
            used_solution = True
            
            if not student_code:
                student_code = f"# No solution code found in DB\n# Trying generic solution\nprint('Ejercicio {i+1}')"
                used_solution = False
                
            submit_resp = await client.post(
                f"{BASE_URL}/student/sessions/{session_id}/submit",
                json={
                    "code": student_code,
                    "language": "python",
                    "exercise_id": ex["exercise_id"],
                    "is_final_submission": False
                }
            )
            
            if submit_resp.status_code == 200:
                res = submit_resp.json()
                grade = res.get('grade')
                feedback = res.get('feedback', '')
                results.append({
                    "title": ex['title'],
                    "grade": grade,
                    "feedback": feedback,
                    "used_solution": used_solution
                })
                print(f"  -> Nota: {grade}/100")
            else:
                print(f"  -> Error al enviar: {submit_resp.status_code}")
                results.append({
                    "title": ex['title'],
                    "grade": 0,
                    "feedback": "Error de sistema",
                    "used_solution": used_solution
                })
            
            # Small delay to not overwhelm local LLM if running locally
            await asyncio.sleep(1)

        # 5. Report Results
        print("\n" + "=" * 60)
        print("RESULTADOS FINALES")
        print("=" * 60)
        
        total_score = sum(r['grade'] for r in results)
        average = total_score / len(results) if results else 0
        
        print(f"{'EJERCICIO':<40} | {'NOTA':<5} | {'TIPO CODE':<10}")
        print("-" * 65)
        for r in results:
            code_type = "Reference" if r['used_solution'] else "Generic"
            print(f"{r['title'][:40]:<40} | {r['grade']:<5} | {code_type:<10}")
            
        print("-" * 65)
        print(f"PROMEDIO FINAL: {average:.2f}/100")
        
        # Save detailed log
        with open("full_test_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
            
        print("\nDetalles guardados en full_test_results.json")

if __name__ == "__main__":
    asyncio.run(run_full_activity_test())
