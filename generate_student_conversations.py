"""
Generador de Conversaciones Realistas para Trazabilidad Cognitiva
==================================================================
Crea sesiones e interacciones variadas para todos los estudiantes de Comisión 1.

Perfiles de estudiantes:
1. Estudiantes buenos: Preguntan conceptualmente, autónomos
2. Dependientes: Piden mucho el código completo
3. Frustrados: Usan lenguaje inapropiado, se quejan
4. Mixtos: Combinación de comportamientos
"""

import asyncio
import asyncpg
import random
from datetime import datetime, timedelta
import json

# ==================== CONFIGURACIÓN ====================
DB_CONFIG = {
    "host": "postgres",
    "port": 5432,
    "database": "ai_native",
    "user": "postgres",
    "password": "yourpassword"
}

ACTIVITY_ID = "fd176d58-08a8-4e99-a81f-381ee0aed044"  # Bucles
COURSE_ID = "course-1"

# ==================== PLANTILLAS DE CONVERSACIÓN ====================

# Estudiante BUENO - Pregunta conceptualmente
GOOD_STUDENT_MESSAGES = [
    "Hola! No entiendo bien cómo funciona el enumerate()",
    "¿Podrías explicarme qué hace range() exactamente?",
    "¿Por qué se usa el break en un bucle?",
    "¿Cuál es la diferencia entre continue y break?",
    "¿Cómo funciona un bucle anidado?",
    "¿Me ayudas a entender por qué mi código da error en la línea 5?",
    "Creo que estoy cerca de la solución, ¿está bien este enfoque?",
    "Gracias! Ahora lo entiendo mejor",
    "Una última pregunta: ¿se puede usar else con un for?",
]

GOOD_TUTOR_RESPONSES = [
    "¡Excelente pregunta! `enumerate()` te da tanto el índice como el valor mientras iteras. ¿Qué sabes sobre iteración?",
    "`range()` genera una secuencia de números. Por ejemplo, `range(5)` da 0,1,2,3,4. ¿Cómo lo usarías en un bucle?",
    "`break` termina el bucle inmediatamente. Piensa en un ejemplo donde quieras salir antes de terminar todas las iteraciones.",
    "Buena observación. `continue` salta a la siguiente iteración, mientras `break` sale del bucle completamente. ¿Ves la diferencia?",
    "Los bucles anidados son un bucle dentro de otro. El interno se ejecuta completamente en cada iteración del externo. ¿Quieres un ejemplo?",
    "Revisemos ese error juntos. ¿Qué intentabas hacer en esa línea?",
    "Vas muy bien! Tu lógica es correcta. Ahora intenta implementarlo.",
    "¡Perfecto! Sigue practicando para afianzar estos conceptos.",
    "¡Sí! El `else` del for se ejecuta si el bucle termina normalmente (sin break). Es poco común pero útil.",
    "**Evaluación IA:** 85/100\n\n**Análisis:** Excelente comprensión de los conceptos. El código está bien estructurado y cumple todos los requisitos. ¡Buen trabajo!\n\n💡 **Sugerencia:** Podrías optimizar la solución usando list comprehension."
]

# Estudiante que PIDE CÓDIGO DIRECTAMENTE
CODE_REQUESTER_MESSAGES = [
    "hola",
    "no entiendo nada",
    "dame el código completo",
    "no se hacer esto, hazme el ejercicio",
    "dame la solucion",
    "ayuda pls",
    "codigo?",
    "no tengo tiempo, necesito la respuesta",
    "ok gracias"
]

CODE_REQUESTER_RESPONSES = [
    "¡Hola! Estoy aquí para ayudarte a aprender. ¿Qué parte específica no entiendes del ejercicio?",
    "Entiendo que puede parecer complicado al principio. ¿Qué has intentado hasta ahora?",
    "Mi función es guiarte, no darte el código completo. Eso no te ayudaría a aprender. ¿Empezamos por el primer paso?",
    "Comprendo que pueda ser difícil, pero necesito que intentes resolverlo tú mismo. ¿Qué sabes sobre bucles for?",
    "No puedo darte la solución directamente, pero puedo ayudarte paso a paso. ¿Comenzamos?",
    "Claro, te ayudaré. Primero, ¿entiendes qué te pide el ejercicio?",
    "Para escribir el código, primero necesitas entender la lógica. ¿Leíste el enunciado completo?",
    "Entiendo la presión del tiempo, pero copiar código no te prepara para el examen. Hagamos un intento rápido juntos.",
    "**Evaluación IA:** 45/100\n\n**Análisis:** El código funciona parcialmente pero muestra falta de comprensión de conceptos básicos. Se detectó alta dependencia de ayuda externa.\n\n💡 **Sugerencia:** Revisa los conceptos básicos de iteración antes de continuar."
]

# Estudiante FRUSTRADO - Usa lenguaje inapropiado
FRUSTRATED_MESSAGES = [
    "esto no tiene sentido",
    "odio programar",
    "esto es una mierda no funciona",
    "no entiendo un carajo",
    "por qué es tan difícil esto??",
    "me quiero morir con este ejercicio",
    "la puta madre no me sale",
    "ya probé todo y nada funciona",
    "dame el codigo de una vez"
]

FRUSTRATED_RESPONSES = [
    "Entiendo que puede ser frustrante. Tomemos un respiro y veamos el problema paso a paso.",
    "La programación tiene una curva de aprendizaje, es normal sentirse así al principio. ¿En qué parte específica te trabas?",
    "Veo que estás frustrado. Revisemos juntos qué está fallando. ¿Me muestras tu código actual?",
    "Es normal encontrar dificultades. Vamos a dividir el problema en partes más pequeñas.",
    "Sé que parece complicado, pero lo estás intentando y eso es lo importante. ¿Qué parte te confunde más?",
    "Entiendo tu frustración. A veces un descanso ayuda. Cuando vuelvas, intentemos un enfoque diferente.",
    "No te rindas! Ya has progresado más de lo que crees. Veamos qué errores tiene el código.",
    "He visto muchos estudiantes superar esto. Tú también puedes. ¿Revisamos el error juntos?",
    "**Evaluación IA:** 35/100\n\n**Análisis:** El código tiene múltiples errores de sintaxis y lógica. Se detectó alta frustración durante la sesión. El estudiante necesita apoyo adicional.\n\n💡 **Sugerencia:** Considera solicitar una tutoría personalizada para reforzar conceptos básicos."
]

# Estudiante MIXTO - Comportamiento variado
MIXED_MESSAGES = [
    "Hola, tengo dudas sobre este ejercicio",
    "¿Cómo empiezo?",
    "Ok intenté esto pero me da error",
    "ahh ya entiendo",
    "pero ahora me sale otro error jaja",
    "esto es complicado",
    "dame una pista?",
    "creo que ya lo tengo",
    "gracias!"
]

MIXED_RESPONSES = [
    "¡Hola! Claro, ¿qué dudas tienes específicamente?",
    "Buen inicio! Comienza definiendo la variable principal. ¿Qué tipo de dato necesitas?",
    "Veamos ese error. ¿Qué mensaje te aparece exactamente?",
    "¡Perfecto! Ahora intenta aplicar esa lógica al ejercicio.",
    "Jaja es parte del proceso! Muéstrame el nuevo error y lo resolvemos.",
    "Es desafiante, pero estás avanzando bien. ¿Qué parte te resulta más difícil?",
    "Claro! Piensa en cómo recorrer una lista elemento por elemento. ¿Qué estructura usarías?",
    "¡Excelente! Ejecuta el código y verifica que pase todos los tests.",
    "**Evaluación IA:** 70/100\n\n**Análisis:** El código cumple con la mayoría de requisitos. Hubo algunos errores durante el proceso pero fueron corregidos. Buen trabajo colaborativo con el tutor.\n\n💡 **Sugerencia:** Practica la depuración de errores para ganar más autonomía."
]


# ==================== FUNCIONES DE GENERACIÓN ====================

def generate_session_id():
    """Genera un UUID válido para session_id"""
    import uuid
    return str(uuid.uuid4())


async def create_session(conn, student_id: str, start_time: datetime, duration_minutes: int):
    """Crea una sesión en sessions_v2"""
    session_id = generate_session_id()
    end_time = start_time + timedelta(minutes=duration_minutes)
    
    session_metrics = {
        "total_time_minutes": duration_minutes,
        "hints_given": random.randint(0, 5),
        "code_executions": random.randint(3, 15),
        "final_grade": None  # Se agregará después según el perfil
    }
    
    cognitive_status = {
        "understanding_level": random.uniform(0.4, 0.9),
        "frustration_level": random.uniform(0.1, 0.7),
        "autonomy_level": random.uniform(0.3, 0.8)
    }
    
    await conn.execute("""
        INSERT INTO sessions_v2 (
            session_id, user_id, activity_id, course_id, 
            status, mode, session_metrics, cognitive_status, 
            start_time, end_time, created_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
    """, session_id, student_id, ACTIVITY_ID, COURSE_ID,
         "completed", "socratic", json.dumps(session_metrics), json.dumps(cognitive_status),
         start_time, end_time, datetime.now())
    
    return session_id


async def create_interaction(conn, session_id: str, timestamp: datetime, 
                            interaction_type: str, content: str, role: str):
    """Crea una interacción en cognitive_traces_v2"""
    import uuid
    
    trace_id = str(uuid.uuid4())
    
    interactional_data = {
        "role": role,
        "content": content,
        "timestamp": timestamp.isoformat()
    }
    
    await conn.execute("""
        INSERT INTO cognitive_traces_v2 (
            trace_id, session_id, activity_id, timestamp, interaction_type, interactional_data
        ) VALUES ($1, $2, $3, $4, $5, $6)
    """, trace_id, session_id, ACTIVITY_ID, timestamp, interaction_type, json.dumps(interactional_data))


async def generate_conversation(conn, student_id: str, profile: str, submission_grade: float):
    """
    Genera una conversación completa según el perfil del estudiante
    
    Perfiles:
    - good: Estudiante autónomo, pregunta bien
    - code_requester: Pide código directamente
    - frustrated: Usa lenguaje inapropiado
    - mixed: Comportamiento mixto
    """
    
    # Seleccionar plantillas según perfil
    if profile == "good":
        messages = GOOD_STUDENT_MESSAGES
        responses = GOOD_TUTOR_RESPONSES
        duration = random.randint(15, 35)
        num_messages = random.randint(6, 9)
    elif profile == "code_requester":
        messages = CODE_REQUESTER_MESSAGES
        responses = CODE_REQUESTER_RESPONSES
        duration = random.randint(8, 20)
        num_messages = random.randint(5, 9)
    elif profile == "frustrated":
        messages = FRUSTRATED_MESSAGES
        responses = FRUSTRATED_RESPONSES
        duration = random.randint(10, 30)
        num_messages = random.randint(5, 9)
    else:  # mixed
        messages = MIXED_MESSAGES
        responses = MIXED_RESPONSES
        duration = random.randint(12, 28)
        num_messages = random.randint(6, 9)
    
    # Crear sesión
    start_time = datetime.now() - timedelta(days=random.randint(1, 7))
    session_id = await create_session(conn, student_id, start_time, duration)
    
    # Generar conversación
    current_time = start_time
    
    for i in range(min(num_messages, len(messages), len(responses))):
        # Mensaje del estudiante
        await create_interaction(
            conn, session_id, current_time,
            "student_message", messages[i], "user"
        )
        
        current_time += timedelta(seconds=random.randint(5, 30))
        
        # Respuesta del tutor
        await create_interaction(
            conn, session_id, current_time,
            "tutor_response", responses[i], "assistant"
        )
        
        current_time += timedelta(seconds=random.randint(30, 180))
    
    # Crear risk analysis en risks_v2
    import uuid
    risk_id = str(uuid.uuid4())
    risk_level = "low"
    risk_dimension = "cognitive"
    description = "Estudiante trabajó de forma autónoma"
    recommendations = {}
    
    if profile == "code_requester":
        risk_level = "high"
        risk_dimension = "ai_dependency"
        code_requests = random.randint(3, 6)
        description = f"Estudiante solicitó el código completo {code_requests} veces. Alta dependencia de IA."
        recommendations = {
            "action": "Revisar comprensión conceptual",
            "priority": "high",
            "code_requests": code_requests,
            "ai_dependency_ratio": 0.8
        }
    elif profile == "frustrated":
        risk_level = "high"
        risk_dimension = "emotional"
        profanity_count = random.randint(2, 5)
        description = f"Estudiante expresó frustración con lenguaje inapropiado {profanity_count} veces."
        recommendations = {
            "action": "Ofrecer apoyo personalizado y ajustar nivel de dificultad",
            "priority": "high",
            "profanity_count": profanity_count
        }
    elif profile == "mixed":
        risk_level = "medium" if submission_grade < 7 else "low"
        risk_dimension = "cognitive"
        description = "Estudiante mostró comportamiento mixto con algunos pedidos de ayuda."
        recommendations = {
            "action": "Monitorear progreso",
            "priority": "medium" if submission_grade < 7 else "low",
            "code_requests": random.randint(0, 2),
            "ai_dependency_ratio": 0.4
        }
    
    await conn.execute("""
        INSERT INTO risks_v2 (
            risk_id, session_id, activity_id, risk_level, risk_dimension,
            description, recommendations, resolved, created_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
    """, risk_id, session_id, ACTIVITY_ID, risk_level, risk_dimension,
         description, json.dumps(recommendations), False, current_time)
    
    # Actualizar session_metrics con final_grade
    await conn.execute("""
        UPDATE sessions_v2 
        SET session_metrics = jsonb_set(
            session_metrics::jsonb, 
            '{final_grade}', 
            to_jsonb($2::float)
        )
        WHERE session_id = $1
    """, session_id, submission_grade * 10)  # Convertir 0-10 a 0-100
    
    return session_id


async def main():
    """Función principal"""
    print("🚀 Iniciando generación de conversaciones...")
    
    try:
        # Conectar a la base de datos
        conn = await asyncpg.connect(**DB_CONFIG)
        print("✅ Conectado a la base de datos")
        
        # Obtener todos los estudiantes con submissions en la actividad Bucles
        students = await conn.fetch("""
            SELECT DISTINCT s.student_id, u.full_name, s.final_grade
            FROM submissions s
            LEFT JOIN users u ON s.student_id = u.id
            WHERE s.activity_id = $1
            ORDER BY u.full_name
        """, ACTIVITY_ID)
        
        print(f"\n📊 Encontrados {len(students)} estudiantes con submissions")
        
        # Distribuir perfiles:
        # 30% buenos, 25% piden código, 20% frustrados, 25% mixtos
        profiles = (
            ["good"] * int(len(students) * 0.30) +
            ["code_requester"] * int(len(students) * 0.25) +
            ["frustrated"] * int(len(students) * 0.20) +
            ["mixed"] * (len(students) - int(len(students) * 0.75))
        )
        random.shuffle(profiles)
        
        created_count = 0
        for idx, student in enumerate(students):
            student_id = student['student_id']
            full_name = student['full_name'] or f"Usuario {student_id[:8]}"
            submission_grade = student['final_grade'] or 5.0
            
            # Verificar si ya tiene sesión
            existing = await conn.fetchval("""
                SELECT session_id FROM sessions_v2 
                WHERE user_id = $1 AND activity_id = $2
            """, student_id, ACTIVITY_ID)
            
            if existing:
                print(f"⏭️  {full_name}: Ya tiene sesión, saltando...")
                continue
            
            # Asignar perfil
            profile = profiles[idx] if idx < len(profiles) else "mixed"
            
            # Generar conversación
            session_id = await generate_conversation(conn, student_id, profile, submission_grade)
            created_count += 1
            
            profile_emoji = {
                "good": "🟢",
                "code_requester": "🔴",
                "frustrated": "😤",
                "mixed": "🟡"
            }
            
            print(f"{profile_emoji.get(profile, '⚪')} {full_name}: Sesión creada ({profile})")
        
        print(f"\n✅ Proceso completado!")
        print(f"📊 Sesiones creadas: {created_count}")
        print(f"🎭 Distribución de perfiles:")
        print(f"   🟢 Buenos (autónomos): ~30%")
        print(f"   🔴 Piden código: ~25%")
        print(f"   😤 Frustrados: ~20%")
        print(f"   🟡 Mixtos: ~25%")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
