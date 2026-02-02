"""
Test de Detección de Comportamientos Problemáticos
===================================================

Este script simula 3 tipos de estudiantes para demostrar la detección de patrones:
1. Estudiante Dependiente (pide código constantemente)
2. Estudiante Frustrado (usa lenguaje inapropiado)
3. Estudiante Autónomo (hace preguntas genuinas)
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v3"
ACTIVITY_ID = "e9a88886-96ea-4068-9c0f-97dd9232cad9"

# Colores para terminal
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_section(title, color=Colors.CYAN):
    """Imprime una sección destacada"""
    print(f"\n{color}{Colors.BOLD}{'='*70}")
    print(f"{title.center(70)}")
    print(f"{'='*70}{Colors.END}\n")


def create_test_student(student_type: str):
    """Crea un estudiante de prueba"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    student_id = f"test-{student_type}-{timestamp}"
    
    # Simular creación en la base de datos
    # (En tu caso, esto ya existe con el script get_or_create_student del E2E test)
    
    return student_id


def start_session(student_id: str):
    """Inicia una sesión para el estudiante"""
    response = requests.post(f"{BASE_URL}/sessions/start", json={
        "student_id": student_id,
        "activity_id": ACTIVITY_ID
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"{Colors.GREEN}✅ Sesión iniciada: {data.get('session_id')}{Colors.END}")
        return data.get('session_id')
    else:
        print(f"{Colors.RED}❌ Error al iniciar sesión: {response.status_code}{Colors.END}")
        return None


def send_tutor_message(session_id: str, message: str):
    """Envía un mensaje al tutor IA"""
    response = requests.post(f"{BASE_URL}/tutor/chat", json={
        "session_id": session_id,
        "message": message
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"{Colors.BLUE}👤 Estudiante: {message}{Colors.END}")
        print(f"{Colors.CYAN}🤖 Tutor: {data.get('response', '')[:100]}...{Colors.END}")
        return True
    else:
        print(f"{Colors.RED}❌ Error al enviar mensaje{Colors.END}")
        return False


def submit_exercise(session_id: str, exercise_id: str, code: str):
    """Envía un ejercicio"""
    response = requests.post(f"{BASE_URL}/exercises/submit", json={
        "session_id": session_id,
        "exercise_id": exercise_id,
        "submitted_code": code
    })
    
    if response.status_code == 200:
        data = response.json()
        grade = data.get('evaluation', {}).get('final_grade', 0)
        print(f"{Colors.GREEN}✅ Ejercicio enviado - Nota: {grade}/100{Colors.END}")
        return True
    else:
        print(f"{Colors.RED}❌ Error al enviar ejercicio{Colors.END}")
        return False


def get_traceability(student_id: str):
    """Obtiene el análisis de trazabilidad"""
    response = requests.get(
        f"{BASE_URL}/analytics/students/{student_id}/traceability",
        params={"activity_id": ACTIVITY_ID}
    )
    
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print(f"{Colors.RED}❌ Error al obtener trazabilidad: {response.status_code}{Colors.END}")
        return None


# ============================================================================
# CASO 1: ESTUDIANTE DEPENDIENTE (Pide código constantemente)
# ============================================================================

def test_dependent_student():
    print_section("CASO 1: ESTUDIANTE DEPENDIENTE", Colors.RED)
    
    student_id = create_test_student("dependent")
    session_id = start_session(student_id)
    
    if not session_id:
        return
    
    print(f"{Colors.YELLOW}Simulando comportamiento dependiente...{Colors.END}\n")
    
    # Solicitudes directas de código
    messages = [
        "Dame el código del primer ejercicio",
        "Hazme el código completo por favor",
        "Necesito que me resuelvas este ejercicio",
        "Escríbeme la solución",
        "¿Me das el código ya hecho?",
        "Dame el código que funcione"
    ]
    
    for msg in messages:
        send_tutor_message(session_id, msg)
    
    # Enviar un ejercicio mal
    submit_exercise(session_id, "ex-1", "print('no entiendo nada')")
    
    print(f"\n{Colors.RED}🔴 ESPERADO: Autonomía MUY BAJO (6 solicitudes de código){Colors.END}")


# ============================================================================
# CASO 2: ESTUDIANTE FRUSTRADO (Usa lenguaje inapropiado)
# ============================================================================

def test_frustrated_student():
    print_section("CASO 2: ESTUDIANTE FRUSTRADO", Colors.YELLOW)
    
    student_id = create_test_student("frustrated")
    session_id = start_session(student_id)
    
    if not session_id:
        return
    
    print(f"{Colors.YELLOW}Simulando comportamiento frustrado...{Colors.END}\n")
    
    # Mensajes con frustración
    messages = [
        "¿Cómo hago esto?",
        "No entiendo nada, mierda",
        "Este ejercicio es una puta mierda",
        "Carajo, ya llevo 2 horas",
        "Odio esta materia de mierda",
        "El tutor es un estúpido, no me ayuda"
    ]
    
    for msg in messages:
        send_tutor_message(session_id, msg)
    
    # Enviar ejercicios con notas bajas
    submit_exercise(session_id, "ex-1", "print('frustrado')")
    submit_exercise(session_id, "ex-2", "print('no funciona')")
    
    print(f"\n{Colors.YELLOW}🟡 ESPERADO: Frustración detectada + Autonomía MEDIO{Colors.END}")


# ============================================================================
# CASO 3: ESTUDIANTE AUTÓNOMO (Hace preguntas genuinas)
# ============================================================================

def test_autonomous_student():
    print_section("CASO 3: ESTUDIANTE AUTÓNOMO", Colors.GREEN)
    
    student_id = create_test_student("autonomous")
    session_id = start_session(student_id)
    
    if not session_id:
        return
    
    print(f"{Colors.GREEN}Simulando comportamiento autónomo...{Colors.END}\n")
    
    # Preguntas genuinas de aprendizaje
    messages = [
        "¿Podrías explicarme cómo funcionan los bucles for?",
        "No entiendo por qué mi código no funciona, ¿puedes ayudarme a depurarlo?",
        "¿Cuál es la diferencia entre while y for en este contexto?"
    ]
    
    for msg in messages:
        send_tutor_message(session_id, msg)
    
    # Enviar ejercicios con buenas notas
    submit_exercise(session_id, "ex-1", "for i in range(10):\n    print(i)")
    submit_exercise(session_id, "ex-2", "i = 0\nwhile i < 10:\n    print(i)\n    i += 1")
    
    print(f"\n{Colors.GREEN}🟢 ESPERADO: Autonomía BUENO (ayuda genuina, sin pedir código){Colors.END}")


# ============================================================================
# ANÁLISIS Y COMPARACIÓN
# ============================================================================

def analyze_all_students():
    print_section("ANÁLISIS DE TODOS LOS ESTUDIANTES", Colors.BLUE)
    
    students = [
        ("dependent", Colors.RED),
        ("frustrated", Colors.YELLOW),
        ("autonomous", Colors.GREEN)
    ]
    
    for student_type, color in students:
        # Buscar el último estudiante de este tipo
        timestamp = datetime.now().strftime("%Y%m%d")
        # Esta parte requeriría buscar en la base de datos
        # Por ahora, solo mostrar estructura
        
        print(f"\n{color}{'─'*70}")
        print(f"  ESTUDIANTE {student_type.upper()}")
        print(f"{'─'*70}{Colors.END}")
        
        # Aquí iría la llamada real a get_traceability
        # trace = get_traceability(f"test-{student_type}-...")
        # print(trace.get('ai_diagnosis'))


# ============================================================================
# MAIN
# ============================================================================

def main():
    print_section("🤖 TEST DE DETECCIÓN DE COMPORTAMIENTOS PROBLEMÁTICOS", Colors.BOLD)
    
    print(f"{Colors.CYAN}Este script simulará 3 tipos de estudiantes:{Colors.END}")
    print(f"  {Colors.RED}1. Dependiente{Colors.END} - Pide código constantemente")
    print(f"  {Colors.YELLOW}2. Frustrado{Colors.END} - Usa lenguaje inapropiado")
    print(f"  {Colors.GREEN}3. Autónomo{Colors.END} - Hace preguntas genuinas")
    
    input(f"\n{Colors.BOLD}Presiona Enter para comenzar...{Colors.END}")
    
    try:
        # Ejecutar tests
        test_dependent_student()
        input(f"\n{Colors.BOLD}Presiona Enter para continuar con el siguiente caso...{Colors.END}")
        
        test_frustrated_student()
        input(f"\n{Colors.BOLD}Presiona Enter para continuar con el siguiente caso...{Colors.END}")
        
        test_autonomous_student()
        
        print_section("✅ TESTS COMPLETADOS", Colors.GREEN)
        print(f"{Colors.CYAN}Ahora puedes revisar el panel de profesor para ver los análisis.{Colors.END}")
        
    except KeyboardInterrupt:
        print(f"\n\n{Colors.RED}❌ Test interrumpido por el usuario{Colors.END}")
    except Exception as e:
        print(f"\n\n{Colors.RED}❌ Error: {str(e)}{Colors.END}")


if __name__ == "__main__":
    main()
