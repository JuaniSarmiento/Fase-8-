import asyncio
import os
import bcrypt
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# URL interna de docker (nombre del servicio en docker-compose)
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@postgres:5432/ai_native"

def get_password_hash(password: str) -> str:
    password_bytes = password.encode("utf-8")[:72]
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=12)).decode("utf-8")

async def fix_passwords():
    print("🔧 [DOCKER] Generando nuevos hashes...")
    new_hash = get_password_hash("demo123")
    print(f"✅ Hash generado: {new_hash}")
    
    print(f"🔌 Conectando a {DATABASE_URL}...")
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as session:
            async with session.begin():
                stmt = text("UPDATE users SET hashed_password = :pwd WHERE email IN ('docente@test.com', 'alumno@test.com')")
                await session.execute(stmt, {"pwd": new_hash})
                
                result = await session.execute(text("SELECT email, hashed_password FROM users WHERE email IN ('docente@test.com', 'alumno@test.com')"))
                rows = result.fetchall()
                print("📊 Resultados:")
                for row in rows:
                    print(f"   - {row[0]}: {row[1][:15]}...")
                    
        print("✨ ¡Éxito! Contraseñas actualizadas.")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(fix_passwords())
