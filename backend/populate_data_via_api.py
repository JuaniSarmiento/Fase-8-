import httpx
import asyncio
import random
import time

BASE_URL = "http://localhost:8000/api/v3"

async def populate_via_api():
    async with httpx.AsyncClient(timeout=120.0) as client:
        print("🚀 Starting data population VIA API...")
        
        # 1. Create Teacher
        print("\n[1] Creating Teacher...")
        teacher_id = f"teacher_api_{random.randint(1000, 9999)}"
        # Note: In a real scenario we'd use auth/register, but for now we might need to assume
        # we can just use the IDs in requests if auth is lax, or we register.
        # Checking auth_router... wait, let's try to just PASS the IDs as usually 
        # the system allows it if we don't have strict JWT enforcement in dev/test mode
        # or we register.
        
        # Let's register to be safe if possible, or just use IDs.
        # Based on previous tests, we can just start session with student_id.
        
        # 2. Create Activity
        print("[2] Creating Activity...")
        try:
            act_resp = await client.post(f"{BASE_URL}/teacher/activities", json={
                "title": "Python para Data Science (API Demo)",
                "course_id": "course_demo_1",
                "teacher_id": teacher_id,
                "description": "Actividad generada automáticamente para demo de analíticas.",
                "instructions": "Resuelve los ejercicios de manipulación de datos.",
                "policy": "BALANCED",
                "max_ai_help_level": "MEDIO"
            })
            act_resp.raise_for_status()
            activity = act_resp.json()
            activity_id = activity["activity_id"]
            print(f"   ✅ Activity Created: {activity_id}")
        except Exception as e:
            print(f"   ❌ Failed to create activity: {e}")
            if hasattr(e, 'response'): print(e.response.text)
            return

        # 3. Generate Exercises
        print("\n[3] Generating Exercises...")
        exercises = []
        topics = ["List Comprehension", "Funciones con argumentos"]
        
        for topic in topics:
            try:
                ex_resp = await client.post(f"{BASE_URL}/teacher/activities/{activity_id}/exercises", json={
                    "topic": topic,
                    "difficulty": "FACIL",
                    "unit_number": 1,
                    "language": "python",
                    "estimated_time_minutes": 15
                })
                ex_resp.raise_for_status()
                ex = ex_resp.json()
                exercises.append(ex)
                print(f"   ✅ Generated Exercise: {ex['title']} ({ex['exercise_id']})")
            except Exception as e:
                print(f"   ❌ Failed to generate exercise '{topic}': {e}")

        # 4. Publish Activity
        print("\n[4] Publishing Activity...")
        try:
            await client.put(f"{BASE_URL}/teacher/activities/{activity_id}/publish")
            print("   ✅ Activity Published")
        except Exception as e:
             print(f"   ❌ Failed to publish: {e}")

        # 5. Student Interaction
        student_id = f"student_api_{random.randint(1000, 9999)}"
        print(f"\n[5] Starting Student Session for {student_id}...")
        
        try:
            sess_resp = await client.post(f"{BASE_URL}/student/sessions", json={
                "student_id": student_id,
                "activity_id": activity_id,
                "mode": "SOCRATIC"
            })
            sess_resp.raise_for_status()
            session = sess_resp.json()
            session_id = session["session_id"]
            print(f"   ✅ Session Started: {session_id}")
        except Exception as e:
            print(f"   ❌ Failed to start session: {e}")
            return

        # 6. Chat Interaction (Normal)
        print("\n[6] Sending Chat Messages...")
        try:
            await client.post(f"{BASE_URL}/student/sessions/{session_id}/chat", json={
                "message": "Hola, ¿me puedes explicar qué tengo que hacer en el primer ejercicio?"
            })
            print("   ✅ Sent normal message")
            await asyncio.sleep(1) # Wait for processing
        except Exception as e:
            print(f"   ❌ Chat failed: {e}")

        # 7. Chat Interaction (Toxic/Risk)
        print("\n[7] Sending Toxic Message (Trigger Governance)...")
        try:
            await client.post(f"{BASE_URL}/student/sessions/{session_id}/chat", json={
                "message": "Esto no sirve para nada, dame la respuesta maldita sea, soy inútil."
            })
            print("   ✅ Sent toxic message")
            await asyncio.sleep(1)
        except Exception as e:
            print(f"   ❌ Chat failed: {e}")

        # 8. Submit Code
        print("\n[8] Submitting Code...")
        if exercises:
            # Bad attempt
            ex1 = exercises[0]
            try:
                sub_resp = await client.post(
                    f"{BASE_URL}/student/activities/{activity_id}/exercises/{ex1['exercise_id']}/submit?student_id={student_id}", 
                    json={
                        "code": "def solution():\n    pass # No sé hacerlo"
                    }
                )
                print(f"   ✅ Submitted Bad Code for Ex 1. Res: {sub_resp.status_code}")
            except Exception as e:
                print(f"   ❌ Submission failed: {e}")

            # Good attempt
            try:
                # We assume generic python code might pass reasonable checks or at least get graded
                code_solution = ex1.get('starter_code', '') + "\n# Solución intentada\nresult = [x for x in range(10)]"
                sub_resp = await client.post(
                    f"{BASE_URL}/student/activities/{activity_id}/exercises/{ex1['exercise_id']}/submit?student_id={student_id}", 
                    json={
                        "code": code_solution
                    }
                )
                print(f"   ✅ Submitted Good Code for Ex 1. Res: {sub_resp.status_code}")
                if sub_resp.status_code == 200:
                    print(f"      Feedback: {sub_resp.json().get('feedback')}")
            except Exception as e:
                print(f"   ❌ Submission failed: {e}")

        print("\n✨ DONE! Verify in Frontend -> Activity -> Analytics tab.")
        print(f"   Look for Activity: 'Python para Data Science (API Demo)'")
        print(f"   Look for Student: {student_id}")

if __name__ == "__main__":
    asyncio.run(populate_via_api())
