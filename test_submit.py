import requests
import json

resp = requests.post(
    'http://localhost:8000/api/v3/student/activities/e5a83dce-c813-4c9f-acba-53438de9b004/submit?student_id=70ed9d32-7bf5-4ae2-9aa9-d40ffeba4aea',
    json={'code': '', 'is_final_submission': True}
)

data = resp.json()
print(f"Status: {resp.status_code}")
print(f"Ejercicios en respuesta: {len(data.get('exercises_details', []))}")
print("\nPrimeros 5 ejercicios:")
for i, ex in enumerate(data.get('exercises_details', [])[:5]):
    feedback_short = ex['feedback'][:90] + '...' if len(ex['feedback']) > 90 else ex['feedback']
    print(f"\n{i+1}. {ex['title']}")
    print(f"   Dificultad: {ex['difficulty']} | Nota: {ex['grade']}/100 | Pasó: {ex['passed']}")
    print(f"   Feedback: {feedback_short}")
