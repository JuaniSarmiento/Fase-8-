import psycopg2
import uuid
import sys

# Set encoding for Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

# Connect to database
conn = psycopg2.connect(
    host='127.0.0.1',
    port=5433,
    dbname='ai_native',
    user='postgres',
    password='postgres'
)
cursor = conn.cursor()

try:
    # Get teacher ID
    cursor.execute("SELECT id FROM users WHERE email = 'docente@test.com'")
    teacher_row = cursor.fetchone()
    
    if not teacher_row:
        print("Error: Teacher user not found!")
        sys.exit(1)
    
    teacher_id = teacher_row[0]
    print(f"Teacher found: {teacher_id}\n")
    
    # Check if activities exist
    cursor.execute("SELECT COUNT(*) FROM activities")
    count = cursor.fetchone()[0]
    
    if count > 0:
        print(f"Database already has {count} activities. Skipping.")
        sys.exit(0)
    
    # Create activities
    activities = [
        ("Introducción a Variables y Tipos de Datos", "ACTIVE"),
        ("Control de Flujo: If, Else, Elif", "ACTIVE"),
        ("Bucles: For y While", "ACTIVE"),
        ("Funciones y Parámetros", "DRAFT"),
        ("Estructuras de Datos: Listas y Diccionarios", "DRAFT"),
        ("Manejo de Excepciones", "DRAFT"),
    ]
    
    print("Creating activities...\n")
    
    unit_counter = 1
    for title, status in activities:
        activity_id = str(uuid.uuid4())
        instructions = f"Practica y aprende sobre {title.lower()}. Esta actividad incluye ejercicios progresivos."
        
        cursor.execute("""
            INSERT INTO activities (
                activity_id, title, subject, unit_id, instructions, teacher_id, status, created_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, NOW()
            )
        """, (
            activity_id, 
            title,
            "Python Programming",
            unit_counter,
            instructions, 
            teacher_id, 
            status
        ))
        
        status_emoji = "[ACT]" if status == "ACTIVE" else "[DRF]"
        print(f"  {status_emoji} Unit {unit_counter}: {title}")
        unit_counter += 1
    
    conn.commit()
    
    # Verify
    cursor.execute("SELECT COUNT(*) FROM activities")
    total = cursor.fetchone()[0]
    
    print(f"\n✓ Successfully created {len(activities)} activities!")
    print(f"✓ Total activities in database: {total}")
    print(f"\n  - 3 published (visible to students)")
    print(f"  - 3 drafts (only visible to teacher)")

except Exception as e:
    conn.rollback()
    print(f"\nError: {e}")
    sys.exit(1)
finally:
    cursor.close()
    conn.close()
