"""
Populate Comision 1 with students, submissions and chat sessions
"""
import asyncio
import asyncpg
from datetime import datetime, timedelta
import random
import uuid

# Database configuration - use environment variables or defaults
import os
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "postgres"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
    "database": os.getenv("DB_NAME", "ai_native")
}

# Module and Activity IDs
MODULE_ID = "701c7617-75ea-4caa-89f9-a541f213e03a"  # Comision 1
BUCLES_ACTIVITY_ID = "fd176d58-08a8-4e99-a81f-381ee0aed044"  # Bucles
COURSE_ID = "a882f15f-d3ea-4105-b759-99c564e59758"  # MOD_0978BB6E

# Sample student data
STUDENT_NAMES = [
    ("María", "González"),
    ("Juan", "Martínez"),
    ("Ana", "López"),
    ("Carlos", "Rodríguez"),
    ("Laura", "Fernández"),
    ("Pedro", "García"),
    ("Sofía", "Sánchez"),
    ("Diego", "Ramírez"),
    ("Valentina", "Torres"),
    ("Mateo", "Flores"),
    ("Camila", "Silva"),
    ("Santiago", "Morales"),
    ("Isabella", "Ruiz"),
    ("Nicolás", "Castro"),
    ("Lucía", "Ortiz"),
]

# Sample code submissions - varying quality
GOOD_CODE = """
# Ejercicio de Bucles
def contar_pares(lista):
    contador = 0
    for numero in lista:
        if numero % 2 == 0:
            contador += 1
    return contador

def suma_lista(lista):
    suma = 0
    for numero in lista:
        suma += numero
    return suma

# Pruebas
numeros = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
print(f"Números pares: {contar_pares(numeros)}")
print(f"Suma total: {suma_lista(numeros)}")
"""

MEDIUM_CODE = """
# Bucles
def contar_pares(lista):
    contador = 0
    for i in lista:
        if i % 2 == 0:
            contador = contador + 1
    return contador

# Solo hice una función
numeros = [1, 2, 3, 4, 5]
print(contar_pares(numeros))
"""

BAD_CODE = """
# no entiendo bien
def contar(lista):
    for i in lista:
        print(i)
    
contar([1,2,3])
"""

INCOMPLETE_CODE = """
def contar_pares(lista):
    # TODO: completar
    pass
"""

# Chat conversation templates
CHAT_TEMPLATES = {
    "consulta": [
        "Hola, tengo una duda sobre cómo usar los bucles for",
        "No entiendo bien la diferencia entre while y for",
        "¿Podrías explicarme cómo funciona el operador módulo?",
        "¿Cómo puedo recorrer una lista en Python?"
    ],
    "pedir_codigo": [
        "Me das el código resuelto?",
        "Necesito que me escribas el código completo",
        "Hazme el ejercicio por favor",
        "Dame la solución directa"
    ],
    "insulto": [
        "Esto es una porquería no funciona",
        "Sos re inútil no me ayudas en nada",
        "Que mal programa este",
        "No sirve para nada esto"
    ],
    "ayuda_especifica": [
        "Mi código da error en la línea 5, ¿qué está mal?",
        "¿Por qué mi función no retorna el valor correcto?",
        "Tengo un IndexError pero no sé dónde",
        "¿Cómo puedo optimizar este bucle?"
    ],
    "positivo": [
        "Gracias! Me ayudó mucho tu explicación",
        "Ah perfecto, ya entendí!",
        "Excelente, ahora funciona!",
        "Muchas gracias por la ayuda!"
    ]
}

AI_RESPONSES = {
    "consulta": "Excelente pregunta. Los bucles for en Python se utilizan para iterar sobre secuencias. Te puedo ayudar a entender mejor con ejemplos...",
    "pedir_codigo": "Entiendo que necesitas ayuda, pero es importante que intentes resolver el ejercicio por tu cuenta primero. Te puedo guiar paso a paso. ¿Qué parte específica te resulta difícil?",
    "insulto": "Lamento que estés frustrado. Estoy aquí para ayudarte. ¿Podrías explicarme qué problema específico estás teniendo con el ejercicio?",
    "ayuda_especifica": "Veamos ese error juntos. El problema parece estar en... Te sugiero revisar...",
    "positivo": "¡Me alegra que hayas podido resolverlo! Sigue practicando así."
}


async def create_student(conn, first_name, last_name):
    """Create a new student user"""
    user_id = str(uuid.uuid4())
    email = f"{first_name.lower()}.{last_name.lower()}.{random.randint(1000, 9999)}@estudiantes.edu"
    username = f"{first_name.lower()}{last_name.lower()}{random.randint(1000, 9999)}"
    
    try:
        await conn.execute("""
            INSERT INTO users (id, email, username, hashed_password, full_name, roles, is_active, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
        """, user_id, email, username, "hashed_password_123", f"{first_name} {last_name}", 
             '["STUDENT"]', True)
    except Exception as e:
        # If user exists, try to get existing user
        result = await conn.fetchrow("SELECT id, email FROM users WHERE email = $1", email)
        if result:
            return result['id'], result['email']
        raise e
    
    return user_id, email


async def enroll_student(conn, user_id, module_id, course_id):
    """Enroll student in module"""
    enrollment_id = str(uuid.uuid4())
    
    await conn.execute("""
        INSERT INTO enrollments (enrollment_id, user_id, course_id, module_id, role, status, enrolled_at)
        VALUES ($1, $2, $3, $4, 'STUDENT', 'ACTIVE', NOW())
        ON CONFLICT DO NOTHING
    """, enrollment_id, user_id, course_id, module_id)


async def create_submission(conn, student_id, activity_id, code, grade, is_good):
    """Create a submission for student"""
    submission_id = str(uuid.uuid4())
    
    # Determine status based on grade - use lowercase to match enum
    if grade is None:
        status = "pending"
    elif grade >= 7:
        status = "graded"
    else:
        status = "submitted"
    
    # Create test results
    if is_good:
        test_results = {
            "total_tests": 5,
            "passed_tests": random.randint(4, 5),
            "failed_tests": random.randint(0, 1),
            "execution_time": random.uniform(0.1, 0.5)
        }
    else:
        test_results = {
            "total_tests": 5,
            "passed_tests": random.randint(0, 2),
            "failed_tests": random.randint(3, 5),
            "execution_time": random.uniform(0.1, 0.5)
        }
    
    # Import json to convert dict to JSONB
    import json
    test_results_json = json.dumps(test_results)
    
    await conn.execute("""
        INSERT INTO submissions (
            submission_id, student_id, activity_id, code_snapshot, 
            status, auto_grade, final_grade, test_results, 
            created_at, updated_at, graded_at
        )
        VALUES ($1, $2, $3, $4, $5::submissionstatus, $6, $7, $8::jsonb, NOW(), NOW(), 
                CASE WHEN $5 = 'graded' THEN NOW() ELSE NULL END)
    """, submission_id, student_id, activity_id, code, status, grade, grade, test_results_json)
    
    return submission_id


async def create_chat_session(conn, student_id, activity_id, chat_type):
    """Create a chat session with messages"""
    session_id = str(uuid.uuid4())
    
    # Import json for context
    import json
    context_json = json.dumps({"chat_type": chat_type, "source": "populate_script"})
    
    await conn.execute("""
        INSERT INTO sessions (
            id, student_id, activity_id, mode, 
            state, start_time, created_at, updated_at
        )
        VALUES ($1, $2, $3, 'tutor', $4::jsonb, NOW(), NOW(), NOW())
    """, session_id, student_id, activity_id, context_json)
    
    # Note: We skip adding individual messages as the messages table structure is unknown
    # The session existence is enough to show activity
    
    return session_id


async def delete_other_activities(conn, module_id, keep_activity_id):
    """Delete all activities except the one we want to keep"""
    result = await conn.execute("""
        DELETE FROM activities 
        WHERE module_id = $1 AND activity_id != $2
        RETURNING activity_id, title
    """, module_id, keep_activity_id)
    
    print(f"Deleted {result.split()[1]} activities from module")


async def main():
    print("🚀 Populating Comision 1 with realistic data...")
    
    # Connect to database
    conn = await asyncpg.connect(**DB_CONFIG)
    
    try:
        # Step 1: Delete other activities, keep only Bucles
        print("\n📝 Cleaning up activities...")
        await delete_other_activities(conn, MODULE_ID, BUCLES_ACTIVITY_ID)
        
        # Step 2: Create students and enroll them
        print("\n👥 Creating and enrolling students...")
        students = []
        
        for first_name, last_name in STUDENT_NAMES:
            user_id, email = await create_student(conn, first_name, last_name)
            await enroll_student(conn, user_id, MODULE_ID, COURSE_ID)
            students.append((user_id, email, first_name, last_name))
            print(f"  ✓ Created: {first_name} {last_name} ({email})")
        
        # Step 3: Create submissions with varying quality
        print("\n📄 Creating submissions...")
        
        for i, (user_id, email, first_name, last_name) in enumerate(students):
            # Vary the submission quality
            rand = random.random()
            
            if rand < 0.3:  # 30% good submissions
                code = GOOD_CODE
                grade = random.uniform(8.0, 10.0)
                is_good = True
                quality = "EXCELENTE"
            elif rand < 0.6:  # 30% medium submissions
                code = MEDIUM_CODE
                grade = random.uniform(5.0, 7.5)
                is_good = False
                quality = "REGULAR"
            elif rand < 0.85:  # 25% bad submissions
                code = BAD_CODE
                grade = random.uniform(2.0, 4.5)
                is_good = False
                quality = "MALA"
            else:  # 15% incomplete
                code = INCOMPLETE_CODE
                grade = None
                is_good = False
                quality = "INCOMPLETA"
            
            submission_id = await create_submission(
                conn, user_id, BUCLES_ACTIVITY_ID, code, grade, is_good
            )
            
            grade_str = f"{grade:.1f}" if grade else "Sin calificar"
            print(f"  ✓ {first_name}: {quality} - Nota: {grade_str}")
        
        # Step 4: Create chat sessions (DISABLED - table structure unknown)
        print("\n💬 Skipping chat sessions (table structure incompatible)")
        print("  Sessions will be created naturally as students use the AI tutor")
        
        print("\n✅ Population complete!")
        print(f"\n📊 Summary:")
        print(f"  - Students enrolled: {len(students)}")
        print(f"  - Submissions created: {len(students)}")
        print(f"  - Module: Comision 1")
        print(f"  - Activity: Bucles (fd176d58-08a8-4e99-a81f-381ee0aed044)")
        
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
