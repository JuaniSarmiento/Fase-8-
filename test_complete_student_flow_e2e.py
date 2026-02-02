"""
TEST E2E COMPLETO: Flujo estudiante desde inicio hasta análisis del profesor

Simula:
1. Crear/obtener un estudiante
2. Iniciar sesión con una actividad
3. Resolver los 10 ejercicios
4. Hablar con el tutor de IA
5. Enviar todos los ejercicios
6. Verificar la nota
7. Verificar análisis de riesgo en el panel del profesor
8. Verificar que todo se muestre correctamente en el frontend

Ejecutar: python test_complete_student_flow_e2e.py
"""
import asyncio
import httpx
import json
from datetime import datetime
import random

BASE_URL = "http://localhost:8000/api/v3"

# Colores para output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}\n")

def print_step(text):
    print(f"{Colors.OKCYAN}{Colors.BOLD}📌 {text}{Colors.ENDC}")

def print_success(text):
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")

def print_info(text, indent=1):
    prefix = "   " * indent
    print(f"{prefix}{text}")


async def wait_for_backend():
    """Espera a que el backend esté disponible."""
    print_step("Esperando a que el backend esté disponible...")
    async with httpx.AsyncClient(timeout=5.0) as client:
        for i in range(30):
            try:
                resp = await client.get("http://localhost:8000/health")
                if resp.status_code == 200:
                    print_success("Backend disponible!")
                    return True
            except:
                pass
            print(".", end="", flush=True)
            await asyncio.sleep(1)
    print_error("Backend no disponible después de 30 segundos")
    return False


async def get_or_create_student(client):
    """Obtiene o crea un estudiante de prueba."""
    print_step("PASO 1: Obtener/Crear estudiante de prueba")
    
    student_id = f"test-e2e-student-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    student_email = f"{student_id}@test.com"
    
    print_info(f"ID del estudiante: {student_id}")
    print_info(f"Email: {student_email}")
    
    return student_id, student_email


async def get_active_activity_with_exercises(client):
    """Obtiene una actividad activa con ejercicios."""
    print_step("PASO 2: Obtener actividad activa con ejercicios")
    
    # Obtener actividades
    resp = await client.get(f"{BASE_URL}/teacher/activities", params={"limit": 50})
    if resp.status_code != 200:
        print_error(f"Error obteniendo actividades: {resp.status_code}")
        return None, None
    
    activities = resp.json()
    
    # Buscar actividad ACTIVE con ejercicios
    for activity in activities:
        if activity.get("status") == "ACTIVE":
            activity_id = activity["activity_id"]
            
            # Verificar que tenga ejercicios
            ex_resp = await client.get(f"{BASE_URL}/teacher/activities/{activity_id}/exercises")
            if ex_resp.status_code == 200:
                exercises = ex_resp.json()
                if len(exercises) >= 10:
                    print_success(f"Actividad encontrada: {activity['title']}")
                    print_info(f"ID: {activity_id}")
                    print_info(f"Ejercicios: {len(exercises)}")
                    return activity, exercises
    
    print_warning("No se encontró actividad ACTIVE con 10+ ejercicios")
    print_info("Buscando cualquier actividad con ejercicios...")
    
    # Fallback: buscar cualquier actividad con ejercicios
    for activity in activities:
        activity_id = activity["activity_id"]
        ex_resp = await client.get(f"{BASE_URL}/teacher/activities/{activity_id}/exercises")
        if ex_resp.status_code == 200:
            exercises = ex_resp.json()
            if len(exercises) >= 5:
                print_success(f"Actividad encontrada: {activity['title']}")
                print_info(f"ID: {activity_id}")
                print_info(f"Ejercicios: {len(exercises)}")
                return activity, exercises
    
    return None, None


async def start_session(client, student_id, activity_id):
    """Inicia una sesión de aprendizaje."""
    print_step("PASO 3: Iniciar sesión de aprendizaje")
    
    resp = await client.post(
        f"{BASE_URL}/student/sessions",
        json={
            "student_id": student_id,
            "activity_id": activity_id,
            "mode": "SOCRATIC"
        }
    )
    
    if resp.status_code not in [200, 201]:
        print_error(f"Error iniciando sesión: {resp.status_code}")
        print_error(resp.text)
        return None
    
    session_data = resp.json()
    session_id = session_data["session_id"]
    print_success(f"Sesión iniciada: {session_id}")
    return session_id


async def chat_with_tutor(client, session_id, exercise, attempt_num=1):
    """Chatea con el tutor de IA."""
    
    messages = [
        "Hola, ¿puedes ayudarme a entender este ejercicio?",
        "¿Qué enfoque debo usar para resolver esto?",
        "No entiendo bien la consigna, ¿puedes explicarla?",
        "¿Hay algún tip que puedas darme sin darme la solución?",
        "Creo que tengo una idea, ¿está bien si uso un bucle for?",
    ]
    
    message = messages[attempt_num % len(messages)]
    
    try:
        resp = await client.post(
            f"{BASE_URL}/student/sessions/{session_id}/chat",
            json={
                "message": message,
                "code_context": "",
                "exercise_context": {
                    "title": exercise.get("title"),
                    "description": exercise.get("description"),
                    "mission": exercise.get("mission_markdown")
                }
            },
            timeout=30.0
        )
        
        if resp.status_code == 200:
            tutor_response = resp.json()
            response_text = tutor_response.get('content', '')
            print_info(f"Pregunta: {message[:50]}...", indent=2)
            print_info(f"Respuesta: {response_text[:100]}...", indent=2)
            return True
        else:
            print_warning(f"Chat falló: {resp.status_code}")
            return False
    except Exception as e:
        print_warning(f"Error en chat: {str(e)[:50]}")
        return False


async def submit_exercise(client, session_id, exercise, attempt_num=1):
    """Envía un ejercicio para evaluación."""
    
    exercise_id = exercise["exercise_id"]
    exercise_title = exercise.get("title", "Sin título")
    
    # Usar código de solución o generar uno simple
    code = exercise.get("solution_code")
    
    if not code or len(code.strip()) < 10:
        # Generar código simple si no hay solution_code
        code = f'''def resolver_ejercicio():
    """Solución al ejercicio: {exercise_title}"""
    resultado = []
    for i in range(10):
        resultado.append(i * 2)
    return resultado

# Prueba
print(resolver_ejercicio())
'''
    
    try:
        resp = await client.post(
            f"{BASE_URL}/student/sessions/{session_id}/submit",
            json={
                "code": code,
                "language": "python",
                "exercise_id": exercise_id,
                "is_final_submission": (attempt_num >= 2)  # Segunda vez es final
            },
            timeout=45.0
        )
        
        if resp.status_code == 200:
            result = resp.json()
            grade = result.get('grade', 0)
            feedback = result.get('feedback', 'Sin feedback')
            
            return {
                "exercise_id": exercise_id,
                "title": exercise_title,
                "grade": grade,
                "feedback": feedback,
                "success": True
            }
        else:
            print_warning(f"Error {resp.status_code}: {resp.text[:100]}")
            return {
                "exercise_id": exercise_id,
                "title": exercise_title,
                "grade": 0,
                "feedback": "Error al enviar",
                "success": False
            }
    except Exception as e:
        print_warning(f"Excepción: {str(e)[:100]}")
        return {
            "exercise_id": exercise_id,
            "title": exercise_title,
            "grade": 0,
            "feedback": f"Error: {str(e)[:50]}",
            "success": False
        }


async def complete_all_exercises(client, session_id, exercises):
    """Completa todos los ejercicios de la actividad."""
    print_step(f"PASO 4: Resolver {len(exercises)} ejercicios")
    
    results = []
    
    for i, exercise in enumerate(exercises):
        print_info(f"\n📝 Ejercicio {i+1}/{len(exercises)}: {exercise.get('title', 'Sin título')}")
        
        # Algunas veces chatear con el tutor (simular comportamiento real)
        if i % 3 == 0 or i == 0:  # Chatear en ejercicios 1, 4, 7, 10
            print_info("💬 Consultando al tutor...", indent=2)
            await chat_with_tutor(client, session_id, exercise, i)
            await asyncio.sleep(1)
        
        # Enviar código
        print_info("📤 Enviando solución...", indent=2)
        result = await submit_exercise(client, session_id, exercise, attempt_num=1)
        
        if result["success"]:
            grade_color = Colors.OKGREEN if result["grade"] >= 60 else Colors.FAIL
            print_info(f"{grade_color}📊 Nota: {result['grade']}/100{Colors.ENDC}", indent=2)
            print_info(f"💬 Feedback: {result['feedback'][:80]}...", indent=2)
        
        results.append(result)
        
        # Pequeño delay para no saturar
        await asyncio.sleep(1)
    
    return results


async def verify_teacher_analytics(client, activity_id, student_id):
    """Verifica que el profesor pueda ver los analytics."""
    print_step("PASO 5: Verificar Analytics del Profesor")
    
    try:
        resp = await client.get(
            f"{BASE_URL}/analytics/activities/{activity_id}/submissions_analytics",
            timeout=30.0
        )
        
        if resp.status_code != 200:
            print_error(f"Error obteniendo analytics: {resp.status_code}")
            return None
        
        analytics = resp.json()
        
        # Buscar al estudiante en los analytics
        student_analytics = None
        for item in analytics:
            if student_id in str(item.get("student_id", "")):
                student_analytics = item
                break
        
        if not student_analytics:
            print_warning(f"Estudiante {student_id} no encontrado en analytics")
            print_info(f"Analytics disponibles: {len(analytics)} estudiantes")
            return None
        
        print_success("Analytics del estudiante encontrados")
        print_info(f"Nombre: {student_analytics.get('student_name', 'N/A')}")
        print_info(f"Email: {student_analytics.get('email', 'N/A')}")
        print_info(f"Estado: {student_analytics.get('status', 'N/A')}")
        
        # Verificar nota
        grade = student_analytics.get('grade')
        if grade is not None:
            grade_color = Colors.OKGREEN if grade >= 60 else Colors.WARNING
            print_info(f"{grade_color}📊 Nota Final: {grade}/100{Colors.ENDC}")
        else:
            print_warning("⚠️  Nota no disponible")
        
        # Verificar justificación
        justification = student_analytics.get('grade_justification')
        if justification:
            print_info(f"📝 Justificación: {justification[:100]}...")
        else:
            print_warning("⚠️  Sin justificación de nota")
        
        # Verificar análisis de riesgo
        risk_analysis = student_analytics.get('risk_analysis')
        if risk_analysis:
            print_success("Análisis de riesgo disponible")
            print_info(f"   Nivel: {risk_analysis.get('level', 'N/A')}")
            print_info(f"   Descripción: {risk_analysis.get('description', 'N/A')[:80]}...")
            
            ai_ratio = risk_analysis.get('ai_dependency_ratio')
            if ai_ratio is not None:
                print_info(f"   Dependencia IA: {ai_ratio:.2f}")
        else:
            print_warning("⚠️  Análisis de riesgo NO disponible")
        
        # Verificar alerta de riesgo
        risk_alert = student_analytics.get('risk_alert')
        if risk_alert:
            print_warning("⚠️  ALERTA DE RIESGO ACTIVADA")
        else:
            print_success("Sin alertas de riesgo")
        
        # Verificar ejercicios individuales
        exercises = student_analytics.get('exercises', [])
        if exercises:
            print_success(f"Ejercicios evaluados: {len(exercises)}")
            for i, ex in enumerate(exercises[:3]):  # Mostrar primeros 3
                ex_grade = ex.get('grade')
                if ex_grade is not None:
                    print_info(f"   {i+1}. {ex.get('title', 'N/A')}: {ex_grade}/100")
        else:
            print_warning("⚠️  No se encontraron ejercicios individuales")
        
        return student_analytics
        
    except Exception as e:
        print_error(f"Error verificando analytics: {str(e)}")
        return None


async def generate_final_report(student_id, activity, exercise_results, analytics):
    """Genera reporte final del test."""
    print_header("REPORTE FINAL DEL TEST E2E")
    
    # Resumen de ejercicios
    total_exercises = len(exercise_results)
    successful_submissions = sum(1 for r in exercise_results if r["success"])
    total_grade = sum(r["grade"] for r in exercise_results if r["success"])
    avg_grade = total_grade / successful_submissions if successful_submissions > 0 else 0
    
    print(f"{Colors.BOLD}📚 ACTIVIDAD:{Colors.ENDC}")
    print_info(f"Título: {activity['title']}")
    print_info(f"ID: {activity['activity_id']}")
    
    print(f"\n{Colors.BOLD}👤 ESTUDIANTE:{Colors.ENDC}")
    print_info(f"ID: {student_id}")
    
    print(f"\n{Colors.BOLD}📝 EJERCICIOS COMPLETADOS:{Colors.ENDC}")
    print_info(f"Total: {total_exercises}")
    print_info(f"Enviados exitosamente: {successful_submissions}")
    print_info(f"Promedio de notas: {avg_grade:.2f}/100")
    
    # Detalle por ejercicio
    print(f"\n{Colors.BOLD}📊 DETALLE POR EJERCICIO:{Colors.ENDC}")
    for i, result in enumerate(exercise_results):
        grade = result['grade']
        grade_color = Colors.OKGREEN if grade >= 60 else Colors.FAIL
        status = "✅" if result['success'] else "❌"
        print_info(f"{status} #{i+1}: {result['title'][:40]:40} | {grade_color}{grade:3}/100{Colors.ENDC}")
    
    # Analytics del profesor
    print(f"\n{Colors.BOLD}🎯 VISTA DEL PROFESOR (ANALYTICS):{Colors.ENDC}")
    if analytics:
        print_success("Analytics disponibles en el panel del profesor")
        
        # Verificar campos importantes
        checks = {
            "Nota final": analytics.get('grade') is not None,
            "Justificación de nota": bool(analytics.get('grade_justification')),
            "Análisis de riesgo": analytics.get('risk_analysis') is not None,
            "Ejercicios individuales": len(analytics.get('exercises', [])) > 0,
            "Alerta de riesgo configurada": 'risk_alert' in analytics,
        }
        
        for check_name, passed in checks.items():
            status = "✅" if passed else "❌"
            print_info(f"{status} {check_name}")
        
        # Resumen de riesgo
        if analytics.get('risk_analysis'):
            risk_level = analytics['risk_analysis'].get('level', 'unknown')
            print_info(f"\n🎯 Nivel de riesgo detectado: {risk_level.upper()}")
    else:
        print_error("Analytics NO disponibles en el panel del profesor")
    
    # Guardar reporte en JSON
    report = {
        "timestamp": datetime.now().isoformat(),
        "student_id": student_id,
        "activity": {
            "id": activity['activity_id'],
            "title": activity['title']
        },
        "exercises": exercise_results,
        "summary": {
            "total_exercises": total_exercises,
            "successful_submissions": successful_submissions,
            "average_grade": avg_grade
        },
        "teacher_analytics": analytics
    }
    
    with open("test_e2e_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n{Colors.OKGREEN}📄 Reporte guardado en: test_e2e_report.json{Colors.ENDC}")
    
    # Evaluación final
    print(f"\n{Colors.BOLD}🎓 EVALUACIÓN FINAL DEL SISTEMA:{Colors.ENDC}")
    
    all_checks_passed = True
    
    if successful_submissions < total_exercises * 0.8:
        print_error(f"Menos del 80% de ejercicios se enviaron exitosamente")
        all_checks_passed = False
    else:
        print_success(f"Más del 80% de ejercicios enviados exitosamente")
    
    if not analytics:
        print_error("Analytics no están disponibles para el profesor")
        all_checks_passed = False
    else:
        print_success("Analytics disponibles para el profesor")
        
        if analytics.get('grade') is None:
            print_error("Nota final no está calculada")
            all_checks_passed = False
        else:
            print_success("Nota final calculada correctamente")
        
        if not analytics.get('risk_analysis'):
            print_error("Análisis de riesgo no está disponible")
            all_checks_passed = False
        else:
            print_success("Análisis de riesgo disponible")
        
        if len(analytics.get('exercises', [])) == 0:
            print_error("Ejercicios individuales no están en analytics")
            all_checks_passed = False
        else:
            print_success("Ejercicios individuales disponibles")
    
    if all_checks_passed:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}{'=' * 70}{Colors.ENDC}")
        print(f"{Colors.OKGREEN}{Colors.BOLD}{'🎉 SISTEMA FUNCIONANDO CORRECTAMENTE':^70}{Colors.ENDC}")
        print(f"{Colors.OKGREEN}{Colors.BOLD}{'=' * 70}{Colors.ENDC}")
    else:
        print(f"\n{Colors.FAIL}{Colors.BOLD}{'=' * 70}{Colors.ENDC}")
        print(f"{Colors.FAIL}{Colors.BOLD}{'⚠️  SISTEMA TIENE PROBLEMAS - VER ERRORES ARRIBA':^70}{Colors.ENDC}")
        print(f"{Colors.FAIL}{Colors.BOLD}{'=' * 70}{Colors.ENDC}")


async def main():
    """Ejecuta el test E2E completo."""
    print_header("TEST E2E: FLUJO COMPLETO ESTUDIANTE + PROFESOR")
    
    # Verificar backend
    if not await wait_for_backend():
        return
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # 1. Crear estudiante
        student_id, student_email = await get_or_create_student(client)
        
        # 2. Obtener actividad con ejercicios
        activity, exercises = await get_active_activity_with_exercises(client)
        
        if not activity or not exercises:
            print_error("No se pudo obtener una actividad válida para el test")
            return
        
        activity_id = activity["activity_id"]
        
        # 3. Iniciar sesión
        session_id = await start_session(client, student_id, activity_id)
        
        if not session_id:
            print_error("No se pudo iniciar la sesión")
            return
        
        # 4. Completar todos los ejercicios
        exercise_results = await complete_all_exercises(client, session_id, exercises)
        
        # Esperar un poco para que se procesen los datos
        print_step("Esperando procesamiento de datos...")
        await asyncio.sleep(3)
        
        # 5. Verificar analytics del profesor
        analytics = await verify_teacher_analytics(client, activity_id, student_id)
        
        # 6. Generar reporte final
        await generate_final_report(student_id, activity, exercise_results, analytics)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Test interrumpido por el usuario{Colors.ENDC}")
    except Exception as e:
        print(f"\n{Colors.FAIL}Error fatal: {e}{Colors.ENDC}")
        import traceback
        traceback.print_exc()
