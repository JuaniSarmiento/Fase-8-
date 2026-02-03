"""Test E2E Simplificado sin colores ni encoding complicado"""
import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v3"
ACTIVITY_ID = "e9a88886-96ea-4068-9c0f-97dd9232cad9"

print("\n=== TEST E2E SIMPLIFICADO ===\n")

# 1. Crear estudiante ID
timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
student_id = f"test-conv-{timestamp}"
print(f"[1] Estudiante ID: {student_id}")

# 2. Iniciar sesion
print(f"[2] Iniciando sesion...")
response = requests.post(f"{BASE_URL}/student/sessions", json={
    "student_id": student_id,
    "activity_id": ACTIVITY_ID,
    "mode": "SOCRATIC"
}, timeout=10)

if response.status_code != 201:
    print(f"ERROR: Status {response.status_code}")
    print(response.text)
    exit(1)

session_id = response.json()["session_id"]
print(f"    Session ID: {session_id}")

# 3. Conversacion (solo 3 mensajes para probar)
print(f"[3] Enviando mensajes...")
messages = [
    "Hola, necesito ayuda con bucles",
    "Como funciona el for?",
    "Gracias por la explicacion"
]

for i, msg in enumerate(messages, 1):
    print(f"    Mensaje {i}/3...", end="")
    try:
        response = requests.post(
            f"{BASE_URL}/student/sessions/{session_id}/chat",
            json={
                "message": msg,
                "current_code": "",
                "exercise_context": {}
            },
            timeout=30
        )
        
        if response.status_code == 200:
            print(" OK")
        else:
            print(f" ERROR {response.status_code}")
            print(response.text)
            break
    except Exception as e:
        print(f" EXCEPTION: {e}")
        break
    
    time.sleep(1)

# 4. Obtener ejercicios y enviar uno
print(f"[4] Obteniendo ejercicios...")
response = requests.get(
    f"{BASE_URL}/student/activities/{ACTIVITY_ID}/exercises",
    timeout=10
)

if response.status_code == 200:
    exercises = response.json()
    if exercises:
        exercise_id = exercises[0]["exercise_id"]
        print(f"    Enviando ejercicio {exercise_id}...")
        
        response = requests.post(
            f"{BASE_URL}/student/activities/{ACTIVITY_ID}/exercises/{exercise_id}/submit",
            json={
                "student_id": student_id,
                "session_id": session_id,
                "code": "for i in range(5):\n    print(i)",
                "context": {}
            },
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            result = response.json()
            print(f"    Nota: {result.get('grade', 0)}/100")
        else:
            print(f"    ERROR {response.status_code}")

# 5. Obtener analisis
print(f"[5] Obteniendo analisis...")
response = requests.get(
    f"{BASE_URL}/analytics/students/{student_id}/traceability",
    params={"activity_id": ACTIVITY_ID},
    timeout=10
)

if response.status_code == 200:
    data = response.json()
    print(f"\n=== ANALISIS IA ===")
    print(data.get("ai_diagnosis", "No disponible"))
    
print(f"\n=== TEST COMPLETADO ===")
print(f"Estudiante: {student_id}")
print(f"Session: {session_id}")
print(f"\nVer en: http://localhost:3000/teacher/activities/{ACTIVITY_ID}")
