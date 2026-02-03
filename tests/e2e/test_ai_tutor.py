"""
Test AI Tutor (chat endpoint) and see how it logs interactions.
"""
import requests
import json

# Test chat with AI tutor
chat_request = {
    "message": "¿Cómo puedo hacer un bucle for que itere sobre una lista?",
    "activity_context": "Bucles en Python",
    "code_context": ""
}

response = requests.post(
    "http://localhost:8000/api/v3/student/activities/e5a83dce-c813-4c9f-acba-53438de9b004/chat?student_id=70ed9d32-7bf5-4ae2-9aa9-d40ffeba4aea",
    json=chat_request
)

print("AI Tutor Response:")
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"Response: {data.get('response', 'N/A')[:200]}...")
else:
    print(f"Error: {response.text}")
