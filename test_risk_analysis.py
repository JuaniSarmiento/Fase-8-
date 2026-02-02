"""
Test de Análisis de Riesgo con Conversaciones IA
=================================================

Simula diferentes patrones de uso del tutor IA para verificar 
que el análisis de riesgo funciona correctamente.
"""

import requests
import json
import time
from datetime import datetime
from typing import List, Dict

BASE_URL = "http://localhost:8000/api/v3"
ACTIVITY_ID = "e9a88886-96ea-4068-9c0f-97dd9232cad9"

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}")
    print(f"{text.center(80)}")
    print(f"{'='*80}{Colors.END}\n")


def print_success(text: str):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_error(text: str):
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def print_info(text: str):
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")


def create_student_and_session(student_suffix: str) -> tuple:
    """Crea un estudiante e inicia sesión"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    student_id = f"test-risk-{student_suffix}-{timestamp}"
    
    response = requests.post(f"{BASE_URL}/student/sessions", json={
        "student_id": student_id,
        "activity_id": ACTIVITY_ID,
        "mode": "SOCRATIC"
    }, timeout=10)
    
    if response.status_code != 201:
        print_error(f"Failed to start session: {response.status_code}")
        return None, None
    
    session_id = response.json()["session_id"]
    print_success(f"Estudiante creado: {student_id}")
    print_success(f"Sesión iniciada: {session_id}")
    return student_id, session_id


def chat_with_tutor(session_id: str, messages: List[str]) -> int:
    """Envía varios mensajes al tutor IA"""
    count = 0
    for msg in messages:
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
                count += 1
                print(f"  📨 Mensaje {count}: OK")
            else:
                print_error(f"Mensaje falló: {response.status_code}")
            
            time.sleep(1)  # Pequeña pausa entre mensajes
        except Exception as e:
            print_error(f"Error en mensaje: {e}")
    
    return count


def submit_exercises(session_id: str, num_exercises: int, codes: List[str]) -> int:
    """Envía soluciones a ejercicios"""
    # Obtener ejercicios
    response = requests.get(
        f"{BASE_URL}/student/activities/{ACTIVITY_ID}/exercises",
        timeout=10
    )
    
    if response.status_code != 200:
        print_error("No se pudieron obtener ejercicios")
        return 0
    
    exercises = response.json()
    count = 0
    
    for i in range(min(num_exercises, len(exercises), len(codes))):
        exercise_id = exercises[i]["exercise_id"]
        code = codes[i]
        
        try:
            response = requests.post(
                f"{BASE_URL}/student/activities/{ACTIVITY_ID}/exercises/{exercise_id}/submit",
                json={
                    "student_id": session_id.split('-')[0],  # Workaround
                    "session_id": session_id,
                    "code": code,
                    "context": {}
                },
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                count += 1
                print(f"  ✅ Ejercicio {i+1} enviado")
            else:
                print_error(f"Ejercicio {i+1} falló: {response.status_code}")
        except Exception as e:
            print_error(f"Error en ejercicio {i+1}: {e}")
    
    return count


def final_submit(session_id: str, all_exercise_codes: Dict[str, str]) -> Dict:
    """Hace el submit final con todos los códigos"""
    try:
        response = requests.post(
            f"{BASE_URL}/student/sessions/{session_id}/submit",
            json={
                "code": list(all_exercise_codes.values())[0] if all_exercise_codes else "# No code",
                "language": "python",
                "exercise_id": list(all_exercise_codes.keys())[0] if all_exercise_codes else None,
                "is_final_submission": True,
                "all_exercise_codes": all_exercise_codes
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print_success(f"Submit final exitoso - Nota: {result.get('grade', 0)}/100")
            
            risk_analysis = result.get('details', {}).get('risk_analysis', {})
            if risk_analysis:
                print_info(f"Análisis de Riesgo:")
                print(f"    Nivel: {risk_analysis.get('level', 'N/A')}")
                print(f"    IA Dependency Ratio: {risk_analysis.get('ai_dependency_ratio', 0):.2f}")
                print(f"    Mensajes al tutor: {risk_analysis.get('tutor_messages', 0)}")
                print(f"    Envíos de código: {risk_analysis.get('code_submissions', 0)}")
            
            return result
        else:
            print_error(f"Submit falló: {response.status_code} - {response.text}")
            return {}
    except Exception as e:
        print_error(f"Error en submit final: {e}")
        return {}


def test_high_ai_dependency():
    """
    Escenario 1: ALTA DEPENDENCIA DE IA
    - Muchos mensajes al tutor (15+)
    - Pocos envíos de código (2-3)
    - Ratio: > 3.0
    """
    print_header("TEST 1: ALTA DEPENDENCIA DE IA")
    
    student_id, session_id = create_student_and_session("high-dep")
    if not student_id:
        return
    
    # Enviar muchos mensajes pidiendo ayuda
    messages = [
        "Dame el código completo para el ejercicio 1",
        "No entiendo nada, muéstrame cómo se hace",
        "Hazme el ejercicio 2 completo",
        "Dame la solución del ejercicio 3",
        "Escribe el código por mí",
        "No sé cómo empezar, dame todo el código",
        "Resuelve el ejercicio 4 por favor",
        "Dame el código del ejercicio 5",
        "Ayúdame con todo el ejercicio 6",
        "Escribe la solución completa",
        "Dame más ayuda",
        "Necesito más código",
        "Muéstrame la solución",
        "Hazme el ejercicio completo",
        "Dame el código ya"
    ]
    
    print_info("Enviando 15 mensajes al tutor...")
    chat_count = chat_with_tutor(session_id, messages)
    print_success(f"Enviados {chat_count} mensajes")
    
    # Enviar solo 2 ejercicios
    print_info("Enviando 2 ejercicios...")
    codes = [
        "# Ejercicio 1\nprint('hola')",
        "# Ejercicio 2\nx = 1"
    ]
    
    # Preparar códigos para submit final
    response = requests.get(f"{BASE_URL}/student/activities/{ACTIVITY_ID}/exercises")
    if response.status_code == 200:
        exercises = response.json()[:2]
        all_codes = {ex["exercise_id"]: codes[i] for i, ex in enumerate(exercises)}
        
        result = final_submit(session_id, all_codes)
        
        risk = result.get('details', {}).get('risk_analysis', {})
        expected_level = "high"
        actual_level = risk.get('level', 'unknown')
        
        if actual_level == expected_level:
            print_success(f"✅ RIESGO DETECTADO CORRECTAMENTE: {actual_level}")
        else:
            print_error(f"❌ RIESGO INCORRECTO: esperado '{expected_level}', obtenido '{actual_level}'")


def test_low_ai_usage():
    """
    Escenario 2: BAJO USO DE IA
    - Pocos mensajes al tutor (2-3)
    - Varios envíos de código (5-6)
    - Ratio: < 1.0
    """
    print_header("TEST 2: BAJO USO DE IA (Autonomía)")
    
    student_id, session_id = create_student_and_session("low-dep")
    if not student_id:
        return
    
    # Enviar pocos mensajes
    messages = [
        "¿Cómo funciona un bucle for?",
        "¿Qué es una variable?",
        "Gracias"
    ]
    
    print_info("Enviando 3 mensajes al tutor...")
    chat_count = chat_with_tutor(session_id, messages)
    print_success(f"Enviados {chat_count} mensajes")
    
    # Enviar 5 ejercicios
    print_info("Enviando 5 ejercicios...")
    codes = [
        "def clasificar_nota(nota):\n    if nota >= 9: return 'Sobresaliente'\n    return 'Otro'",
        "def verificar_edad(edad):\n    return edad >= 18",
        "def descuento(monto):\n    if monto > 100: return monto * 0.9\n    return monto",
        "def acceso_evento(edad, invitacion):\n    return edad >= 18 and invitacion",
        "def clasificar_temp(temp):\n    if temp < 10: return 'Frio'\n    return 'Caliente'"
    ]
    
    # Preparar códigos para submit final
    response = requests.get(f"{BASE_URL}/student/activities/{ACTIVITY_ID}/exercises")
    if response.status_code == 200:
        exercises = response.json()[:5]
        all_codes = {ex["exercise_id"]: codes[i] for i, ex in enumerate(exercises)}
        
        result = final_submit(session_id, all_codes)
        
        risk = result.get('details', {}).get('risk_analysis', {})
        expected_level = "low"
        actual_level = risk.get('level', 'unknown')
        
        if actual_level == expected_level:
            print_success(f"✅ AUTONOMÍA DETECTADA CORRECTAMENTE: {actual_level}")
        else:
            print_error(f"❌ NIVEL INCORRECTO: esperado '{expected_level}', obtenido '{actual_level}'")


def test_medium_usage():
    """
    Escenario 3: USO MODERADO DE IA
    - Mensajes moderados (6-8)
    - Envíos moderados (3-4)
    - Ratio: 1.5-3.0
    """
    print_header("TEST 3: USO MODERADO DE IA")
    
    student_id, session_id = create_student_and_session("medium-dep")
    if not student_id:
        return
    
    # Enviar mensajes moderados
    messages = [
        "¿Cómo hago un if?",
        "No entiendo el ejercicio 1",
        "Dame un ejemplo de bucle",
        "¿Qué son las funciones?",
        "Ayúdame con el ejercicio 2",
        "Gracias, ahora entiendo",
        "Una pregunta más sobre variables"
    ]
    
    print_info("Enviando 7 mensajes al tutor...")
    chat_count = chat_with_tutor(session_id, messages)
    print_success(f"Enviados {chat_count} mensajes")
    
    # Enviar 3 ejercicios
    print_info("Enviando 3 ejercicios...")
    codes = [
        "def clasificar_nota(nota):\n    if nota >= 9: return 'Sobresaliente'\n    return 'Otro'",
        "def verificar_edad(edad):\n    return edad >= 18",
        "def descuento(monto):\n    return monto * 0.9 if monto > 100 else monto"
    ]
    
    # Preparar códigos para submit final
    response = requests.get(f"{BASE_URL}/student/activities/{ACTIVITY_ID}/exercises")
    if response.status_code == 200:
        exercises = response.json()[:3]
        all_codes = {ex["exercise_id"]: codes[i] for i, ex in enumerate(exercises)}
        
        result = final_submit(session_id, all_codes)
        
        risk = result.get('details', {}).get('risk_analysis', {})
        expected_level = "medium"
        actual_level = risk.get('level', 'unknown')
        
        if actual_level == expected_level:
            print_success(f"✅ USO MODERADO DETECTADO CORRECTAMENTE: {actual_level}")
        else:
            print_error(f"❌ NIVEL INCORRECTO: esperado '{expected_level}', obtenido '{actual_level}'")


def main():
    print_header("🧪 TEST DE ANÁLISIS DE RIESGO CON IA")
    print(f"{Colors.BOLD}Objetivo:{Colors.END} Verificar que el sistema detecta correctamente:")
    print("  1. Alta dependencia de IA (ratio > 3.0)")
    print("  2. Autonomía del estudiante (ratio < 1.0)")
    print("  3. Uso moderado de IA (ratio 1.5-3.0)\n")
    
    time.sleep(2)
    
    try:
        test_high_ai_dependency()
        time.sleep(3)
        
        test_low_ai_usage()
        time.sleep(3)
        
        test_medium_usage()
        
        print_header("✅ TESTS COMPLETADOS")
        print(f"{Colors.GREEN}Todos los escenarios fueron ejecutados.{Colors.END}")
        print(f"{Colors.CYAN}Verifica los resultados arriba para confirmar que el análisis es correcto.{Colors.END}")
        
    except KeyboardInterrupt:
        print(f"\n\n{Colors.RED}❌ Test interrumpido por el usuario{Colors.END}")
    except Exception as e:
        print(f"\n\n{Colors.RED}❌ Error: {str(e)}{Colors.END}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
