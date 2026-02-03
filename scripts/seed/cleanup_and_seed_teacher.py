"""
Script para limpiar la base de datos y crear el usuario docente único.

Ejecutar: python cleanup_and_seed_teacher.py
"""
import asyncio
import json
import os
import sys
import uuid
from datetime import datetime

import asyncpg
import bcrypt

# Database configuration - usa 'postgres' dentro de Docker, 'localhost' fuera
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "postgres"),  
    "port": int(os.getenv("DB_PORT", "5432")),  # Dentro de Docker es 5432
    "database": os.getenv("DB_NAME", "ai_native"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
}


async def cleanup_database(conn: asyncpg.Connection):
    """Limpiar todas las tablas de la base de datos."""
    print("\n🧹 Limpiando base de datos...")
    
    tables_to_clean = [
        # Orden inverso de dependencias
        "cognitive_traces_v2",
        "risks_v2",
        "exercise_attempts_v2",
        "sessions_v2",
        "submissions",
        "enrollments",
        "users",
    ]
    
    for table in tables_to_clean:
        try:
            result = await conn.execute(f"DELETE FROM {table}")
            print(f"  ✓ {table}: {result}")
        except Exception as e:
            print(f"  ⚠️  Error limpiando {table}: {e}")
    
    print("✅ Base de datos limpiada")


async def create_teacher_account(conn: asyncpg.Connection):
    """Crear el único usuario docente."""
    print("\n👨‍🏫 Creando cuenta de docente...")
    
    # Credenciales del docente
    teacher_data = {
        "id": str(uuid.uuid4()),
        "username": "docente",
        "email": "docente@ainative.edu",
        "full_name": "Profesor",
        "password": "docente123",  # Password que espera el backend
        "roles": ["TEACHER"],
    }
    
    # Hash the password
    hashed_password = bcrypt.hashpw(
        teacher_data["password"].encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')
    
    # Insert teacher
    try:
        await conn.execute("""
            INSERT INTO users (
                id, username, email, hashed_password, full_name, 
                roles, is_active, created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6::jsonb, $7, $8, $9
            )
        """,
        teacher_data["id"],
        teacher_data["username"],
        teacher_data["email"],
        hashed_password,
        teacher_data["full_name"],
        json.dumps(teacher_data["roles"]),  # Convert list to JSON string
        True,  # is_active
        datetime.now(),
        datetime.now()
        )
        
        print(f"  ✓ Docente creado:")
        print(f"    Usuario: {teacher_data['username']}")
        print(f"    Email: {teacher_data['email']}")
        print(f"    Contraseña: {teacher_data['password']}")
        print(f"    ID: {teacher_data['id']}")
        
    except Exception as e:
        print(f"  ❌ Error creando docente: {e}")
        raise
    
    print("✅ Cuenta de docente creada exitosamente")


async def verify_setup(conn: asyncpg.Connection):
    """Verificar que la configuración es correcta."""
    print("\n🔍 Verificando configuración...")
    
    # Check users
    users = await conn.fetch("SELECT id, username, email, full_name, roles FROM users")
    print(f"\n📊 Usuarios en la base de datos: {len(users)}")
    for user in users:
        print(f"  - {user['username']} ({user['email']}) - Roles: {user['roles']}")
    
    # Check other tables
    tables_count = {
        "sessions_v2": await conn.fetchval("SELECT COUNT(*) FROM sessions_v2"),
        "cognitive_traces_v2": await conn.fetchval("SELECT COUNT(*) FROM cognitive_traces_v2"),
        "risks_v2": await conn.fetchval("SELECT COUNT(*) FROM risks_v2"),
        "submissions": await conn.fetchval("SELECT COUNT(*) FROM submissions"),
        "enrollments": await conn.fetchval("SELECT COUNT(*) FROM enrollments"),
    }
    
    print("\n📊 Conteo de registros por tabla:")
    for table, count in tables_count.items():
        print(f"  {table}: {count}")
    
    print("\n✅ Verificación completada")


async def main():
    """Main execution function."""
    print("=" * 60)
    print("🔄 LIMPIEZA Y CONFIGURACIÓN DE BASE DE DATOS")
    print("=" * 60)
    print(f"\nConectando a: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    
    # Connect to database
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        print("✅ Conexión establecida")
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        print("\n💡 Si estás usando Docker, asegúrate de:")
        print("  1. El contenedor de postgres está corriendo: docker ps")
        print("  2. Usar host='localhost' si ejecutas desde fuera de Docker")
        print("  3. O ejecutar este script dentro del contenedor backend")
        sys.exit(1)
    
    try:
        # Confirm action
        print("\n⚠️  ADVERTENCIA: Este script va a:")
        print("  1. BORRAR todos los usuarios, sesiones, entregas, etc.")
        print("  2. Crear un único usuario docente")
        print("  3. Los estudiantes deberán registrarse de nuevo")
        
        response = input("\n¿Continuar? (escribe 'SI' para confirmar): ")
        if response.upper() != "SI":
            print("❌ Operación cancelada")
            return
        
        # Execute cleanup and seed
        await cleanup_database(conn)
        await create_teacher_account(conn)
        await verify_setup(conn)
        
        print("\n" + "=" * 60)
        print("✅ PROCESO COMPLETADO EXITOSAMENTE")
        print("=" * 60)
        print("\n📝 Próximos pasos:")
        print("  1. Reinicia el backend si está corriendo")
        print("  2. Usa estas credenciales para login de docente:")
        print("     Usuario: docente")
        print("     Contraseña: docente")
        print("  3. Los estudiantes deben registrarse en /register")
        
    except Exception as e:
        print(f"\n❌ Error durante la ejecución: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await conn.close()
        print("\n👋 Conexión cerrada")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Proceso interrumpido por el usuario")
        sys.exit(1)
