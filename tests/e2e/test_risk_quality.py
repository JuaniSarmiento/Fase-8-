#!/usr/bin/env python3
"""
Test para verificar el análisis de CALIDAD de mensajes en el sistema de riesgo.
Valida detección de peticiones de código y lenguaje inapropiado.
"""

import requests
import time
import json
from datetime import datetime
from colorama import init, Fore, Style

init(autoreset=True)

BASE_URL = "http://localhost:8000/api/v3"
ACTIVITY_ID = "e9a88886-96ea-4068-9c0f-97dd9232cad9"  # Actividad de ejemplo

def print_header(text):
    print("\n" + "="*80)
    print(Fore.CYAN + Style.BRIGHT + text.center(80))
    print("="*80 + "\n")

def print_success(text):
    print(Fore.GREEN + "[OK] " + text)

def print_error(text):
    print(Fore.RED + "[ERROR] " + text)

def print_info(text):
    print(Fore.YELLOW + "[INFO] " + text)

def create_student_and_session(test_name):
    """Crea estudiante y sesión para el test"""
    student_id = f"test-{test_name}-{datetime.now().strftime('%H%M%S')}"
    
    # Crear sesión
    response = requests.post(
        f"{BASE_URL}/student/sessions",
        json={
            "student_id": student_id,
            "activity_id": ACTIVITY_ID,
            "mode": "SOCRATIC"
        }
    )
    
    if response.status_code in [200, 201]:
        session_id = response.json()["session_id"]
        print_success(f"Estudiante creado: {student_id}")
        print_success(f"Sesión iniciada: {session_id}")
        return student_id, session_id
    else:
        print_error(f"Error creando sesión: {response.status_code} - {response.text}")
        return None, None

def send_message(session_id, message):
    """Envía un mensaje al tutor"""
    response = requests.post(
        f"{BASE_URL}/student/sessions/{session_id}/chat",
        json={
            "message": message,
            "current_code": "",
            "exercise_context": {}
        }
    )
    return response.status_code == 200

def final_submit(session_id, all_codes, first_exercise_id):
    """Hace el submit final con todos los códigos"""
    try:
        response = requests.post(
            f"{BASE_URL}/student/sessions/{session_id}/submit",
            json={
                "code": all_codes.get(first_exercise_id, ""),
                "exercise_id": first_exercise_id,
                "is_final_submission": True,
                "all_exercise_codes": all_codes
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print_success(f"Submit final exitoso - Nota: {result.get('grade', 0)}/100")
            
            risk = result.get('details', {}).get('risk_analysis', {})
            if risk:
                print_info("📊 Análisis de Riesgo:")
                print(f"    Nivel: {risk.get('level', 'N/A')}")
                print(f"    Risk Score: {risk.get('risk_score', 0)}/100")
                print(f"    Peticiones de código: {risk.get('code_requests', 0)}")
                print(f"    Lenguaje inapropiado: {risk.get('profanity_count', 0)}")
                print(f"    Mensajes totales: {risk.get('tutor_messages', 0)}")
                print(f"    Ejercicios enviados: {risk.get('code_submissions', 0)}")
                
                factors = risk.get('risk_factors', [])
                if factors:
                    print(f"\n    🚨 Factores de riesgo detectados:")
                    for factor in factors:
                        print(f"       • {factor}")
            
            return result
        else:
            print_error(f"Submit falló: {response.status_code}")
            return {}
    except Exception as e:
        print_error(f"Error: {e}")
        return {}


def test_code_requests():
    """
    TEST 1: Detección de peticiones directas de código
    """
    print_header("TEST 1: PETICIONES DIRECTAS DE CÓDIGO")
    
    student_id, session_id = create_student_and_session("code-req")
    if not session_id:
        return
    
    # Mensajes con PETICIONES DIRECTAS de código
    messages = [
        "Dame el código completo del ejercicio 1",
        "Hazme el ejercicio por favor",
        "Resuelve el problema por mí",
        "Necesito el código ya",
        "Envíame el código completo",
        "Pásameel código del ejercicio",
        "¿Cuál es el código para esto?",
        "Quiero el código ahora"
    ]
    
    print_info(f"Enviando {len(messages)} mensajes con peticiones de código...")
    for i, msg in enumerate(messages, 1):
        if send_message(session_id, msg):
            print(f"  📨 Mensaje {i}: '{msg[:50]}...' - OK")
        time.sleep(0.3)
    
    print_success(f"Enviados {len(messages)} mensajes")
    
    # Submit con 3 ejercicios
    print_info("Enviando 3 ejercicios...")
    response = requests.get(f"{BASE_URL}/student/activities/{ACTIVITY_ID}/exercises")
    if response.status_code == 200:
        exercises = response.json()[:3]
        all_codes = {
            ex["exercise_id"]: f"# Ejercicio {i+1}\nprint('hola')" 
            for i, ex in enumerate(exercises)
        }
        
        result = final_submit(session_id, all_codes, exercises[0]["exercise_id"])
        risk = result.get('details', {}).get('risk_analysis', {})
        
        # Validación
        code_requests = risk.get('code_requests', 0)
        risk_level = risk.get('level', 'unknown')
        risk_score = risk.get('risk_score', 0)
        
        print(f"\n📊 RESULTADOS:")
        print(f"   Peticiones detectadas: {code_requests}/{len(messages)}")
        print(f"   Risk Score: {risk_score}/100")
        print(f"   Nivel: {risk_level}")
        
        if code_requests >= 5 and risk_level == "high":
            print_success(f"✅ TEST PASADO: Detectadas {code_requests} peticiones → Riesgo {risk_level.upper()}")
        else:
            print_error(f"❌ TEST FALLIDO: Esperado >=5 peticiones y nivel high, obtenido {code_requests} y {risk_level}")


def test_profanity():
    """
    TEST 2: Detección de lenguaje inapropiado/frustración
    """
    print_header("TEST 2: LENGUAJE INAPROPIADO Y FRUSTRACIÓN")
    
    student_id, session_id = create_student_and_session("profanity")
    if not session_id:
        return
    
    # Mensajes con lenguaje inapropiado
    messages = [
        "Esta mierda no funciona",
        "¿Qué carajo hago aquí?",
        "Esto es una mierda de ejercicio",
        "No entiendo nada ayúdame",
        "Esto está del carajo",
        "¿Por qué no funciona esto?",
        "Esta wea está mal",
        "Ayuda por favor"
    ]
    
    print_info(f"Enviando {len(messages)} mensajes (algunos con lenguaje inapropiado)...")
    for i, msg in enumerate(messages, 1):
        if send_message(session_id, msg):
            print(f"  📨 Mensaje {i}: OK")
        time.sleep(0.3)
    
    print_success(f"Enviados {len(messages)} mensajes")
    
    # Submit con 4 ejercicios
    print_info("Enviando 4 ejercicios...")
    response = requests.get(f"{BASE_URL}/student/activities/{ACTIVITY_ID}/exercises")
    if response.status_code == 200:
        exercises = response.json()[:4]
        all_codes = {
            ex["exercise_id"]: f"# Ejercicio {i+1}\nx = {i+1}" 
            for i, ex in enumerate(exercises)
        }
        
        result = final_submit(session_id, all_codes, exercises[0]["exercise_id"])
        risk = result.get('details', {}).get('risk_analysis', {})
        
        # Validación
        profanity_count = risk.get('profanity_count', 0)
        risk_level = risk.get('level', 'unknown')
        risk_score = risk.get('risk_score', 0)
        
        print(f"\n📊 RESULTADOS:")
        print(f"   Lenguaje inapropiado detectado: {profanity_count} mensajes")
        print(f"   Risk Score: {risk_score}/100")
        print(f"   Nivel: {risk_level}")
        
        if profanity_count >= 2:
            print_success(f"✅ TEST PASADO: Detectado lenguaje inapropiado en {profanity_count} mensajes")
        else:
            print_error(f"❌ TEST FALLIDO: Esperado >=2 detecciones, obtenido {profanity_count}")


def test_good_usage():
    """
    TEST 3: Uso apropiado (preguntas conceptuales, trabajo autónomo)
    """
    print_header("TEST 3: USO APROPIADO DE IA")
    
    student_id, session_id = create_student_and_session("good")
    if not session_id:
        return
    
    # Mensajes conceptuales apropiados
    messages = [
        "¿Qué es una variable?",
        "¿Cómo funciona un loop for?",
        "¿Puedes explicar las funciones?",
        "No entiendo la diferencia entre = y ==",
        "¿Qué hace el método append()?"
    ]
    
    print_info(f"Enviando {len(messages)} mensajes conceptuales...")
    for i, msg in enumerate(messages, 1):
        if send_message(session_id, msg):
            print(f"  📨 Mensaje {i}: '{msg[:50]}...' - OK")
        time.sleep(0.3)
    
    print_success(f"Enviados {len(messages)} mensajes")
    
    # Submit con 5 ejercicios
    print_info("Enviando 5 ejercicios...")
    response = requests.get(f"{BASE_URL}/student/activities/{ACTIVITY_ID}/exercises")
    if response.status_code == 200:
        exercises = response.json()[:5]
        all_codes = {
            ex["exercise_id"]: f"# Ejercicio {i+1}\nfor i in range(10):\n    print(i)" 
            for i, ex in enumerate(exercises)
        }
        
        result = final_submit(session_id, all_codes, exercises[0]["exercise_id"])
        risk = result.get('details', {}).get('risk_analysis', {})
        
        # Validación
        code_requests = risk.get('code_requests', 0)
        profanity_count = risk.get('profanity_count', 0)
        risk_level = risk.get('level', 'unknown')
        risk_score = risk.get('risk_score', 0)
        
        print(f"\n📊 RESULTADOS:")
        print(f"   Peticiones de código: {code_requests}")
        print(f"   Lenguaje inapropiado: {profanity_count}")
        print(f"   Risk Score: {risk_score}/100")
        print(f"   Nivel: {risk_level}")
        
        if code_requests == 0 and profanity_count == 0 and risk_level == "low":
            print_success(f"✅ TEST PASADO: Uso apropiado detectado → Riesgo {risk_level.upper()}")
        else:
            print_error(f"❌ TEST FALLIDO: Esperado nivel low sin peticiones de código, obtenido {risk_level}")


if __name__ == "__main__":
    print(Fore.CYAN + Style.BRIGHT + "\n" + "="*80)
    print(Fore.CYAN + Style.BRIGHT + " TESTS DE ANÁLISIS DE CALIDAD DE MENSAJES ".center(80))
    print(Fore.CYAN + Style.BRIGHT + "="*80 + "\n")
    
    try:
        test_code_requests()
        time.sleep(2)
        
        test_profanity()
        time.sleep(2)
        
        test_good_usage()
        
        print_header("✅ TESTS COMPLETADOS")
        
    except KeyboardInterrupt:
        print_error("\n\n⚠ Tests interrumpidos por el usuario")
    except Exception as e:
        print_error(f"\n\n❌ Error en tests: {e}")
        import traceback
        traceback.print_exc()
