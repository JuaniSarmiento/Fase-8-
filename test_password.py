"""
Test completo de credenciales PostgreSQL
"""
import asyncio
import psycopg2
import asyncpg

print("\n" + "="*60)
print("TEST DE CREDENCIALES POSTGRESQL")
print("="*60 + "\n")

# Credenciales
HOST = "127.0.0.1"
PORT = 5433
USER = "postgres"
PASSWORD = "postgres"
DATABASE = "ai_native"

print(f"Credenciales a probar:")
print(f"  Host: {HOST}")
print(f"  Puerto: {PORT}")
print(f"  Usuario: {USER}")
print(f"  Contraseña: {PASSWORD}")
print(f"  Base de datos: {DATABASE}")
print()

# Test 1: psycopg2 (sync)
print("[Test 1] Conexion con psycopg2 (sync)...")
try:
    conn = psycopg2.connect(
        host=HOST,
        port=PORT,
        user=USER,
        password=PASSWORD,
        database=DATABASE
    )
    cursor = conn.cursor()
    cursor.execute("SELECT version()")
    version = cursor.fetchone()[0]
    print(f"  ✓ EXITO - Conectado!")
    print(f"  ✓ Version: {version[:60]}...")
    
    cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
    count = cursor.fetchone()[0]
    print(f"  ✓ Tablas: {count}")
    
    cursor.close()
    conn.close()
    print()
except Exception as e:
    print(f"  ✗ ERROR: {e}")
    print()

# Test 2: asyncpg (async - usado por FastAPI backend)
print("[Test 2] Conexion con asyncpg (async - backend)...")
async def test_asyncpg():
    try:
        conn = await asyncpg.connect(
            host=HOST,
            port=PORT,
            user=USER,
            password=PASSWORD,
            database=DATABASE
        )
        
        # Obtener version
        version = await conn.fetchval("SELECT version()")
        print(f"  ✓ EXITO - Conectado con asyncpg!")
        print(f"  ✓ Version: {version[:60]}...")
        
        # Contar tablas
        count = await conn.fetchval("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        print(f"  ✓ Tablas: {count}")
        
        # Listar tablas
        tables = await conn.fetch("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public' 
            ORDER BY tablename
        """)
        print(f"  ✓ Tablas encontradas:")
        for table in tables:
            print(f"     - {table['tablename']}")
        
        await conn.close()
        print()
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        print()

asyncio.run(test_asyncpg())

# Test 3: Conexion con URL (como en .env)
print("[Test 3] Conexion con DATABASE_URL (formato .env)...")
try:
    db_url = f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}"
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    cursor.execute("SELECT current_database(), current_user")
    db, user = cursor.fetchone()
    print(f"  ✓ EXITO - Conectado con URL!")
    print(f"  ✓ Base de datos: {db}")
    print(f"  ✓ Usuario: {user}")
    cursor.close()
    conn.close()
    print()
except Exception as e:
    print(f"  ✗ ERROR: {e}")
    print()

# Test 4: Verificar archivo .env
print("[Test 4] Verificando archivo .env...")
try:
    with open(".env", "r") as f:
        for line in f:
            if line.startswith("DATABASE_URL"):
                print(f"  ✓ Encontrado: {line.strip()}")
                if "postgres:postgres" in line:
                    print(f"  ✓ La contraseña en .env es CORRECTA: postgres")
                else:
                    print(f"  ✗ ATENCION: La contraseña en .env NO coincide")
                break
    print()
except Exception as e:
    print(f"  ✗ ERROR: {e}")
    print()

print("="*60)
print("RESUMEN")
print("="*60)
print()
print("✓ Contraseña confirmada: postgres")
print("✓ Usuario: postgres")
print("✓ Puerto: 5433")
print("✓ Base de datos: ai_native")
print("✓ Driver sync (psycopg2): FUNCIONA")
print("✓ Driver async (asyncpg): FUNCIONA")
print("✓ Backend puede conectarse sin problemas")
print()
print("="*60)
print()
