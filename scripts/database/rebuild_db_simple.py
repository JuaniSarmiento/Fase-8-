"""
Script simple para reconstruir la base de datos PostgreSQL
Usa Python para mayor compatibilidad
"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys
import os
from pathlib import Path

print("\n" + "="*60)
print("RECONSTRUCCION DE BASE DE DATOS POSTGRESQL")
print("="*60 + "\n")

# Credenciales
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "postgres"  # Cambiar si es necesario
POSTGRES_HOST = "127.0.0.1"
POSTGRES_PORT = 5433
DATABASE_NAME = "ai_native"

# Probar diferentes contraseñas
passwords_to_try = [
    "postgres",
    "admin123",
    "password",
    "admin",
]

print("[1/5] Conectando a PostgreSQL...")
conn = None
working_password = None

for password in passwords_to_try:
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=POSTGRES_USER,
            password=password,
            database="postgres"
        )
        working_password = password
        print(f"   ✓ Conectado con password: {password}")
        break
    except psycopg2.OperationalError:
        continue

if conn is None:
    print("   ✗ ERROR: No se pudo conectar con ninguna password conocida")
    print("\n   Passwords probadas:", passwords_to_try)
    print("\n   Necesitas ejecutar como Administrador:")
    print("   .\\rebuild_database.ps1")
    sys.exit(1)

print()

try:
    # Configurar para crear base de datos
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    # [2/5] Terminar conexiones activas
    print("[2/5] Terminando conexiones activas a ai_native...")
    try:
        cursor.execute(f"""
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = '{DATABASE_NAME}'
            AND pid <> pg_backend_pid();
        """)
        print("   ✓ Conexiones terminadas")
    except Exception as e:
        print(f"   ! Advertencia: {e}")
    
    print()
    
    # [3/5] Eliminar base de datos
    print("[3/5] Eliminando base de datos existente...")
    try:
        cursor.execute(f"DROP DATABASE IF EXISTS {DATABASE_NAME};")
        print(f"   ✓ Base de datos '{DATABASE_NAME}' eliminada")
    except Exception as e:
        print(f"   ! Error al eliminar: {e}")
    
    print()
    
    # [4/5] Crear base de datos
    print("[4/5] Creando base de datos nueva...")
    try:
        cursor.execute(f"CREATE DATABASE {DATABASE_NAME} OWNER {POSTGRES_USER};")
        print(f"   ✓ Base de datos '{DATABASE_NAME}' creada")
    except Exception as e:
        print(f"   ✗ ERROR al crear base de datos: {e}")
        cursor.close()
        conn.close()
        sys.exit(1)
    
    cursor.close()
    conn.close()
    
    print()
    
    # [5/5] Actualizar .env
    print("[5/5] Actualizando archivo .env...")
    env_path = Path(".env")
    db_url = f"DATABASE_URL=postgresql+asyncpg://{POSTGRES_USER}:{working_password}@{POSTGRES_HOST}:{POSTGRES_PORT}/{DATABASE_NAME}"
    
    if env_path.exists():
        with open(env_path, 'r') as f:
            lines = f.readlines()
        
        with open(env_path, 'w') as f:
            updated = False
            for line in lines:
                if line.startswith("DATABASE_URL="):
                    f.write(db_url + "\n")
                    updated = True
                else:
                    f.write(line)
            
            if not updated:
                f.write("\n" + db_url + "\n")
        
        print(f"   ✓ Archivo .env actualizado")
    else:
        print(f"   ! Advertencia: .env no encontrado")
    
    print()
    
    # [6/5] Crear tablas usando SQLAlchemy
    print("[6/5] Creando tablas con SQLAlchemy...")
    
    # Actualizar variable de entorno
    os.environ["DATABASE_URL"] = f"postgresql+asyncpg://{POSTGRES_USER}:{working_password}@{POSTGRES_HOST}:{POSTGRES_PORT}/{DATABASE_NAME}"
    
    import asyncio
    sys.path.insert(0, str(Path(__file__).parent))
    
    from backend.src_v3.infrastructure.persistence.database import init_db
    
    asyncio.run(init_db())
    
    print()
    print("="*60)
    print("✓ RECONSTRUCCION COMPLETADA!")
    print("="*60)
    print()
    print("Credenciales:")
    print(f"  Host: {POSTGRES_HOST}")
    print(f"  Puerto: {POSTGRES_PORT}")
    print(f"  Usuario: {POSTGRES_USER}")
    print(f"  Password: {working_password}")
    print(f"  Base de datos: {DATABASE_NAME}")
    print()
    print("Proximo paso:")
    print("  python audit_schema.py")
    print()
    
except Exception as e:
    print(f"\n✗ ERROR FATAL: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
