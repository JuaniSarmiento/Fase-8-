"""
Test grading system with NEW 100% AI FORMULA.
"""
import httpx
import asyncio
import time

BASE_URL = "http://localhost:8000/api/v3"

async def wait_for_backend():
    print("Waiting for backend...")
    async with httpx.AsyncClient(timeout=5.0) as client:
        for i in range(30): # Wait up to 30 seconds
            try:
                resp = await client.get("http://localhost:8000/health")
                if resp.status_code == 200:
                    print("Backend is UP!")
                    return True
            except:
                pass
            print(".", end="", flush=True)
            await asyncio.sleep(1)
    print("\nBackend not responding after 30s")
    return False

async def test_grading():
    if not await wait_for_backend():
        return

    async with httpx.AsyncClient(timeout=120.0) as client:
        print("\n" + "=" * 60)
        print("TEST: VERIFICAR SISTEMA DE CORRECCION (100% AI)")
        print("=" * 60)
        
        # 1. Get activities
        activities_resp = await client.get(f"{BASE_URL}/teacher/activities", params={"limit": 5})
        activities = activities_resp.json()
        
        if not activities:
            print("No hay actividades")
            return
            
        activity = activities[0]
        activity_id = activity["activity_id"]
        
        # 2. Get exercises
        exercises_resp = await client.get(f"{BASE_URL}/teacher/activities/{activity_id}/exercises")
        exercises = exercises_resp.json()
        
        # 3. Pick exercise with solution
        ex = next((e for e in exercises if e.get('solution_code')), exercises[0])
        print(f"Ejercicio: {ex['title']}")
        
        # 4. Start session
        session_resp = await client.post(
            f"{BASE_URL}/student/sessions",
            json={
                "student_id": "test-student-ai-grading",
                "activity_id": activity_id
            }
        )
        session_id = session_resp.json().get("session_id")
        
        # 5. Submit solution code
        student_code = ex.get('solution_code')
        if not student_code:
            student_code = "print('Hello World')"
            
        print(f"Enviando codigo (len={len(student_code)}):")
        print("-" * 20)
        print(student_code)
        print("-" * 20)
        
        submit_resp = await client.post(
            f"{BASE_URL}/student/sessions/{session_id}/submit",
            json={
                "code": student_code,
                "language": "python",
                "exercise_id": ex["exercise_id"],
                "is_final_submission": False
            }
        )
        
        if submit_resp.status_code != 200:
            print(f"Error: {submit_resp.status_code}")
            return
            
        result = submit_resp.json()
        
        grade = result.get('grade')
        feedback = result.get('feedback', '')
        
        print("\n" + "-" * 40)
        print(f"NOTA FINAL: {grade}/100")
        print("-" * 40)
        
        # Clean output
        safe_feedback = ''.join(c if ord(c) < 128 else '?' for c in feedback[:200])
        print(f"Feedback: {safe_feedback}...")
        
        result_data = {
            "grade": grade,
            "feedback": feedback,
            "status": "PASS" if grade >= 70 else "FAIL"
        }
        
        import json
        with open("test_outcome.json", "w", encoding="utf-8") as f:
            json.dump(result_data, f, indent=2)
            
        print(f"Test finished. Result saved to test_outcome.json. Grade: {grade}")

if __name__ == "__main__":
    asyncio.run(test_grading())
