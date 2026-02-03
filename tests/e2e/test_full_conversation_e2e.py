"""
Test E2E Completo con Múltiples Conversaciones
==============================================

Este test crea un estudiante nuevo, hace ejercicios y HABLA MUCHO con el tutor IA
para demostrar el análisis de conversación.
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Optional

# Configurar encoding para Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

BASE_URL = "http://localhost:8000/api/v3"
ACTIVITY_ID = "e9a88886-96ea-4068-9c0f-97dd9232cad9"  # Bucles

# Colores ANSI para terminal
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text: str, color=Colors.CYAN):
    """Imprime un encabezado destacado"""
    print(f"\n{color}{Colors.BOLD}{'='*80}")
    print(f"{text.center(80)}")
    print(f"{'='*80}{Colors.END}\n")


def print_step(step_num: int, text: str):
    """Imprime un paso del test"""
    print(f"{Colors.BOLD}{Colors.BLUE}[PASO {step_num}]{Colors.END} {text}")


def print_success(text: str):
    """Imprime mensaje de éxito"""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")


def print_error(text: str):
    """Imprime mensaje de error"""
    print(f"{Colors.RED}❌ {text}{Colors.END}")


def print_info(text: str):
    """Imprime información"""
    print(f"{Colors.CYAN}ℹ️  {text}{Colors.END}")


def print_conversation(speaker: str, message: str):
    """Imprime un mensaje de conversación"""
    if speaker == "Estudiante":
        print(f"{Colors.YELLOW}👤 {speaker}:{Colors.END} {message}")
    else:
        print(f"{Colors.CYAN}🤖 {speaker}:{Colors.END} {message[:100]}...")


# ============================================================================
# 1. CREAR ESTUDIANTE (sin tabla users, solo ID)
# ============================================================================

def create_student() -> str:
    """Genera un ID de estudiante de prueba"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    student_id = f"test-conversation-{timestamp}"
    
    print_step(1, f"Generando ID de estudiante: {student_id}")
    print_success(f"Estudiante ID: {student_id}")
    
    return student_id


# ============================================================================
# 2. INICIAR SESIÓN
# ============================================================================

def start_session(student_id: str) -> Optional[str]:
    """Inicia una sesión para el estudiante"""
    print_step(2, f"Iniciando sesión para {student_id}")
    
    response = requests.post(f"{BASE_URL}/student/sessions", json={
        "student_id": student_id,
        "activity_id": ACTIVITY_ID,
        "mode": "SOCRATIC"
    })
    
    if response.status_code in [200, 201]:
        data = response.json()
        session_id = data.get('session_id')
        print_success(f"Sesión iniciada: {session_id}")
        return session_id
    else:
        print_error(f"Error al iniciar sesión: {response.status_code}")
        print_info(f"Response: {response.text}")
        return None


# ============================================================================
# 3. CONVERSACIONES CON EL TUTOR
# ============================================================================

def chat_with_tutor(session_id: str, message: str) -> bool:
    """Envía un mensaje al tutor IA"""
    print_conversation("Estudiante", message)
    
    response = requests.post(f"{BASE_URL}/student/sessions/{session_id}/chat", json={
        "message": message,
        "current_code": "",
        "exercise_context": {}
    }, timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        tutor_response = data.get('content', '')
        print_conversation("Tutor IA", tutor_response)
        time.sleep(0.5)  # Pausa breve para simular lectura
        return True
    else:
        print_error(f"Error al chatear: {response.status_code}")
        return False


def have_extended_conversation(session_id: str):
    """Mantiene una conversación extensa con el tutor"""
    print_step(3, "Conversando con el tutor IA (múltiples mensajes)")
    
    # Lista de mensajes para simular una conversación real
    messages = [
        "Hola, ¿puedes ayudarme con los ejercicios de bucles?",
        "No entiendo muy bien cómo funciona el bucle for",
        "¿Podrías explicarme la diferencia entre for y while?",
        "¿Cómo sé cuándo usar cada tipo de bucle?",
        "Tengo un error en mi código, ¿puedes ayudarme a depurarlo?",
        "¿Es normal que mi bucle se ejecute una vez de más?",
        "¿Por qué necesito usar range() en el for?",
        "¿Qué pasa si no incremento la variable en el while?",
        "Gracias, creo que ahora entiendo mejor",
        "Una última pregunta: ¿puedo anidar bucles?"
    ]
    
    successful_chats = 0
    for i, msg in enumerate(messages, 1):
        print(f"\n{Colors.MAGENTA}--- Mensaje {i}/{len(messages)} ---{Colors.END}")
        if chat_with_tutor(session_id, msg):
            successful_chats += 1
        time.sleep(1)  # Pausa entre mensajes
    
    print_success(f"Conversación completa: {successful_chats}/{len(messages)} mensajes enviados")
    return successful_chats


# ============================================================================
# 4. RESOLVER EJERCICIOS
# ============================================================================

def get_exercises() -> list:
    """Obtiene la lista de ejercicios de la actividad"""
    response = requests.get(f"{BASE_URL}/student/activities/{ACTIVITY_ID}/exercises")
    
    if response.status_code == 200:
        exercises = response.json()
        return exercises[:5]  # Solo 5 ejercicios para ir más rápido
    else:
        print_error(f"Error al obtener ejercicios: {response.status_code}")
        return []


def submit_exercise(session_id: str, exercise_id: str, code: str, title: str) -> Optional[dict]:
    """Envía un ejercicio"""
    print(f"{Colors.WHITE}📝 Enviando: {title}{Colors.END}")
    
    response = requests.post(f"{BASE_URL}/student/sessions/{session_id}/submit", json={
        "code": code,
        "language": "python",
        "exercise_id": exercise_id,
        "is_final_submission": True
    }, timeout=45)
    
    if response.status_code == 200:
        data = response.json()
        grade = data.get('grade', 0)
        
        if grade >= 80:
            print_success(f"Nota: {grade}/100 - ¡Excelente!")
        elif grade >= 60:
            print(f"{Colors.YELLOW}✓ Nota: {grade}/100 - Aprobado{Colors.END}")
        else:
            print(f"{Colors.RED}✗ Nota: {grade}/100 - Reprobado{Colors.END}")
        
        return data
    else:
        print_error(f"Error al enviar ejercicio: {response.status_code}")
        return None


def solve_exercises(session_id: str):
    """Resuelve varios ejercicios"""
    print_step(4, "Resolviendo ejercicios")
    
    exercises = get_exercises()
    print_info(f"Se resolverán {len(exercises)} ejercicios")
    
    submitted = 0
    for i, exercise in enumerate(exercises, 1):
        print(f"\n{Colors.MAGENTA}--- Ejercicio {i}/{len(exercises)} ---{Colors.END}")
        
        # Código de ejemplo (algunos correctos, otros con errores)
        if i % 3 == 0:
            # Código con error intencional
            code = f"# Ejercicio {i}\nfor i in range(10\n    print(i)"  # Sintaxis incorrecta
        elif i % 2 == 0:
            # Código medio
            code = f"# Ejercicio {i}\ni = 0\nwhile i < 5:\n    print(i)"  # Falta incremento
        else:
            # Código correcto
            code = f"# Ejercicio {i}\nfor i in range(10):\n    print(i)"
        
        result = submit_exercise(
            session_id, 
            exercise['exercise_id'], 
            code,
            exercise['title']
        )
        
        if result:
            submitted += 1
        
        time.sleep(0.5)
    
    print_success(f"Ejercicios enviados: {submitted}/{len(exercises)}")
    return submitted


# ============================================================================
# 5. ANALIZAR EN PANEL DOCENTE
# ============================================================================

def get_traceability(student_id: str) -> Optional[dict]:
    """Obtiene los datos de trazabilidad del estudiante"""
    print_step(5, "Obteniendo análisis de trazabilidad")
    
    response = requests.get(
        f"{BASE_URL}/analytics/students/{student_id}/traceability",
        params={"activity_id": ACTIVITY_ID}
    )
    
    if response.status_code == 200:
        data = response.json()
        print_success("Datos de trazabilidad obtenidos")
        return data
    else:
        print_error(f"Error al obtener trazabilidad: {response.status_code}")
        return None


def display_analysis(trace_data: dict):
    """Muestra el análisis generado por la IA"""
    print_header("ANÁLISIS DE LA IA", Colors.GREEN)
    
    print(f"{Colors.BOLD}Estudiante:{Colors.END} {trace_data.get('student_name')}")
    print(f"{Colors.BOLD}Actividad:{Colors.END} {trace_data.get('activity_title')}")
    print(f"{Colors.BOLD}Nota Final:{Colors.END} {trace_data.get('final_grade', 'N/A')}/100")
    print(f"{Colors.BOLD}Riesgo:{Colors.END} {trace_data.get('risk_level', 'N/A')}")
    
    print(f"\n{Colors.CYAN}{'─'*80}{Colors.END}")
    print(trace_data.get('ai_diagnosis', 'No hay análisis disponible'))
    print(f"{Colors.CYAN}{'─'*80}{Colors.END}\n")
    
    # Resumen de interacciones
    interactions = trace_data.get('interactions', [])
    user_msgs = len([i for i in interactions if i.get('type') == 'user'])
    ai_msgs = len([i for i in interactions if i.get('type') == 'ai'])
    
    print(f"{Colors.BOLD}📊 Resumen de Interacciones:{Colors.END}")
    print(f"  • Mensajes del estudiante: {user_msgs}")
    print(f"  • Respuestas del tutor: {ai_msgs}")
    print(f"  • Total de interacciones: {len(interactions)}")
    
    # Resumen de ejercicios
    exercises = trace_data.get('exercises', [])
    print(f"\n{Colors.BOLD}📝 Resumen de Ejercicios:{Colors.END}")
    print(f"  • Ejercicios enviados: {len(exercises)}")
    
    if exercises:
        avg_grade = sum([e.get('grade', 0) for e in exercises]) / len(exercises)
        passed = len([e for e in exercises if e.get('grade', 0) >= 60])
        print(f"  • Promedio: {avg_grade:.1f}/100")
        print(f"  • Aprobados: {passed}/{len(exercises)}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    print_header("🎓 TEST E2E COMPLETO CON CONVERSACIÓN EXTENSA", Colors.BOLD)
    
    try:
        # 1. Crear estudiante
        student_id = create_student()
        
        # 2. Iniciar sesión
        session_id = start_session(student_id)
        if not session_id:
            print_error("No se pudo iniciar la sesión. Abortando.")
            return
        
        # 3. Conversación extensa con el tutor
        chat_count = have_extended_conversation(session_id)
        
        # 4. Resolver ejercicios
        exercises_submitted = solve_exercises(session_id)
        
        # 5. Obtener y mostrar análisis
        trace_data = get_traceability(student_id)
        if trace_data:
            display_analysis(trace_data)
        
        # Resumen final
        print_header("✅ TEST COMPLETADO EXITOSAMENTE", Colors.GREEN)
        print(f"{Colors.BOLD}Estudiante ID:{Colors.END} {student_id}")
        print(f"{Colors.BOLD}Session ID:{Colors.END} {session_id}")
        print(f"{Colors.BOLD}Conversaciones:{Colors.END} {chat_count} mensajes")
        print(f"{Colors.BOLD}Ejercicios:{Colors.END} {exercises_submitted} enviados")
        print(f"\n{Colors.CYAN}🌐 Puedes ver los resultados en:{Colors.END}")
        print(f"   http://localhost:3000/teacher/activities/{ACTIVITY_ID}")
        
    except KeyboardInterrupt:
        print(f"\n\n{Colors.RED}❌ Test interrumpido por el usuario{Colors.END}")
    except Exception as e:
        print(f"\n\n{Colors.RED}❌ Error: {str(e)}{Colors.END}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
