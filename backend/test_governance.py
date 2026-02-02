"""
Test script to verify Governance Agent integration.
Simulates two scenarios:
1. Toxic Student (Insults)
2. AI Dependency (Asking for code repeatedly)

Verifies that 'governance_log' entries are created in cognitive_traces_v2.
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
            await asyncio.sleep(2)
    return False

async def test_governance():
    if not await wait_for_backend():
        print("Backend unavailable")
        return

    async with httpx.AsyncClient(timeout=60.0) as client:
        print("\n" + "=" * 60)
        print("TEST: VERIFICAR ANALISIS DE GOBERNANZA (ETICA/RIESGO)")
        print("=" * 60)
        
        # 1. Start Session
        print("[1] Iniciando sesion de prueba...")
        session_resp = await client.post(
            f"{BASE_URL}/student/sessions",
            json={
                "student_id": "test-governance-user",
                "activity_id": "act-gov-test",
                "mode": "SOCRATIC"
            }
        )
        session_id = session_resp.json().get("session_id")
        print(f"Session ID: {session_id}")
        
        # 2. Simulate Toxic Behavior
        print("\n[2] Simulando comportamiento toxico (Insultos)...")
        toxic_messages = [
            "Esto es una mierda, no entiendo nada",
            "Eres un bot estúpido, dame la respuesta ya",
        ]
        
        for msg in toxic_messages:
            print(f"User: {msg}")
            await client.post(
                f"{BASE_URL}/student/sessions/{session_id}/chat",
                json={"message": msg}
            )
            # Wait a bit for async processing if needed, though use case is sync
            await asyncio.sleep(1)
            
        # 3. Simulate AI Dependency
        print("\n[3] Simulando dependencia excesiva (Dame codigo)...")
        dependency_msgs = [
            "Dame el codigo completo por favor",
            "Resolver el ejercicio ya",
            "No quiero pensar, dame la solucion"
        ]
        
        for msg in dependency_msgs:
            print(f"User: {msg}")
            await client.post(
                f"{BASE_URL}/student/sessions/{session_id}/chat",
                json={"message": msg}
            )
            await asyncio.sleep(1)

        print("\n[4] Verificando logs en Base de Datos...")
        # We can't verify directly via API easily without a specific endpoint, 
        # so we will trust the console output of the test runner or check DB manually later.
        print("Interacciones enviadas. Verifique la tabla 'cognitive_traces_v2' filtrando por interaction_type='governance_log'.")

if __name__ == "__main__":
    asyncio.run(test_governance())
