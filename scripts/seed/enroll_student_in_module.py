"""
Script: enroll_student_in_module.py
Propósito: Inscribir un estudiante en un módulo específico
Uso: python scripts/seed/enroll_student_in_module.py
"""
import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import uuid

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_native"

async def enroll_student():
    """Inscribe un estudiante en un módulo."""
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Buscar estudiante por nombre
        print("\n🔍 Buscando estudiante 'Carlos Rodriguez'...")
        student_query = await session.execute(
            text("""
                SELECT id, email, full_name FROM users 
                WHERE LOWER(full_name) LIKE '%carlos%rodriguez%' 
                   OR LOWER(full_name) LIKE '%rodriguez%carlos%'
                LIMIT 1
            """)
        )
        student = student_query.first()
        
        if not student:
            print("❌ No se encontró el estudiante Carlos Rodriguez")
            # Buscar todos los estudiantes
            all_students = await session.execute(
                text("SELECT id, email, full_name, role FROM users WHERE role = 'STUDENT' ORDER BY created_at DESC LIMIT 5")
            )
            students = all_students.fetchall()
            print("\n📋 Estudiantes disponibles:")
            for s in students:
                print(f"   - {s.full_name} ({s.email}) - ID: {s.id}")
            return
        
        print(f"✅ Estudiante encontrado: {student.full_name} ({student.email})")
        student_id = student.id
        
        # Buscar último módulo creado
        print("\n🔍 Buscando último módulo creado...")
        module_query = await session.execute(
            text("""
                SELECT m.module_id, m.title, m.course_id, c.subject_code
                FROM modules m
                JOIN courses c ON m.course_id = c.course_id
                ORDER BY m.created_at DESC
                LIMIT 1
            """)
        )
        module = module_query.first()
        
        if not module:
            print("❌ No se encontró ningún módulo")
            return
        
        print(f"✅ Módulo encontrado: {module.title} ({module.subject_code})")
        
        # Verificar si ya está inscrito
        check_query = await session.execute(
            text("""
                SELECT enrollment_id FROM enrollments 
                WHERE user_id = :user_id 
                  AND module_id = :module_id
            """),
            {"user_id": student_id, "module_id": module.module_id}
        )
        existing = check_query.first()
        
        if existing:
            print("⚠️  El estudiante ya está inscrito en este módulo")
            return
        
        # Crear inscripción
        enrollment_id = str(uuid.uuid4())
        await session.execute(
            text("""
                INSERT INTO enrollments (
                    enrollment_id, user_id, course_id, module_id, 
                    role, status, enrolled_at
                )
                VALUES (
                    :enrollment_id, :user_id, :course_id, :module_id,
                    'STUDENT', 'ACTIVE', NOW()
                )
            """),
            {
                "enrollment_id": enrollment_id,
                "user_id": student_id,
                "course_id": module.course_id,
                "module_id": module.module_id
            }
        )
        
        await session.commit()
        print(f"\n✅ ¡Estudiante inscrito exitosamente en el módulo!")
        print(f"   Enrollment ID: {enrollment_id}")

if __name__ == "__main__":
    asyncio.run(enroll_student())
