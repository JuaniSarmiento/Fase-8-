import requests
import json

# Enviar código real para un ejercicio (Uso de la Sentencia continue)
code = """
# Bucle for con continue
for i in range(10):
    if i % 2 == 0:
        continue
    print(i)
"""

resp = requests.post(
    'http://localhost:8000/api/v3/student/activities/e5a83dce-c813-4c9f-acba-53438de9b004/exercises/80e44b32-8503-4b82-b468-fb7c824674e1/submit?student_id=70ed9d32-7bf5-4ae2-9aa9-d40ffeba4aea',
    json={'code': code}
)

result = resp.json()
print("Resultado de evaluación individual:")
print(f"Status: {resp.status_code}")
print(f"Nota: {result.get('grade')}/100")
print(f"Feedback: {result.get('ai_feedback')}")
