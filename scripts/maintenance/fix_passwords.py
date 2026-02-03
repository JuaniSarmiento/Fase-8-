import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import bcrypt

# Configuración
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5433/ai_native"

def get_password_hash(password: str) -> str:
    """Hash password with bcrypt (12 rounds) exactly as backend does."""
    password_bytes = password.encode("utf-8")[:72]
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=12)).decode("utf-8")

async def fix_passwords():
    print("🔧 Iniciando reparación de contraseñas...")
    
    # 1. Generar hash limpio
    new_hash = get_password_hash("demo123")
    print(f"✅ Hash generado: {new_hash}")
    
    # 2. Conectar a BD
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        async with session.begin():
            # 3. Actualizar usuarios
            stmt = text("UPDATE users SET hashed_password = :pwd WHERE email IN ('docente@test.com', 'alumno@test.com')")
            await session.execute(stmt, {"pwd": new_hash})
            
            # Verificar
            result = await session.execute(text("SELECT email, hashed_password FROM users WHERE email IN ('docente@test.com', 'alumno@test.com')"))
            rows = result.fetchall()
            for row in rows:
                print(f"📝 Actualizado: {row[0]} -> {row[1][:10]}...")
                
    await engine.dispose()
    print("✨ Proceso completado exitosamente")

if __name__ == "__main__":
    # Instalar dependencias si faltan
    try:
        import sqlalchemy
        import asyncpg
        import bcrypt
    except ImportError:
        print("⚠️ Instalando dependencias necesarias...")
        os.system("pip install sqlalchemy asyncpg bcrypt")
    
    # Ejecutar en Windows loop policy
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    asyncio.run(fix_passwords())
