"""
Script para limpiar datos de actividades, sesiones y ejercicios de estudiantes.
Mantiene las actividades y ejercicios, pero elimina:
- Sesiones de estudiantes
- Intentos de ejercicios
- Submissions
- Cognitive traces
- Governance logs
"""
import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

load_dotenv()

async def clean_activity_data():
    """Limpia datos de sesiones y attempts de estudiantes."""
    
    # Usar DATABASE_URL del .env (postgresql+asyncpg://postgres:postgres@127.0.0.1:5433/ai_native)
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@127.0.0.1:5433/ai_native")
    
    # Crear engine SQLAlchemy
    engine = create_async_engine(DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        try:
            print("=" * 60)
            print("LIMPIANDO DATOS DE ACTIVIDADES DE ESTUDIANTES")
            print("=" * 60)
            
            # 1. Limpiar cognitive traces
            print("\n🧹 Limpiando cognitive_traces_v2...")
            result = await conn.execute(text("DELETE FROM cognitive_traces_v2"))
            print(f"   ✅ {result.rowcount} registros eliminados")
            
            # 2. Limpiar exercise attempts
            print("\n🧹 Limpiando exercise_attempts_v2...")
            result = await conn.execute(text("DELETE FROM exercise_attempts_v2"))
            print(f"   ✅ {result.rowcount} registros eliminados")
            
            # 3. Limpiar submissions
            print("\n🧹 Limpiando submissions...")
            result = await conn.execute(text("DELETE FROM submissions"))
            print(f"   ✅ {result.rowcount} registros eliminados")
            
            # 4. Limpiar sessions
            print("\n🧹 Limpiando sessions_v2...")
            result = await conn.execute(text("DELETE FROM sessions_v2"))
            print(f"   ✅ {result.rowcount} registros eliminados")
            
            # 5. Limpiar risks_v2 (si existe)
            print("\n🧹 Limpiando risks_v2...")
            try:
                result = await conn.execute(text("DELETE FROM risks_v2"))
                print(f"   ✅ {result.rowcount} registros eliminados")
            except Exception as e:
                print(f"   ⚠️ Tabla risks_v2 no existe o error: {e}")
            
            print("\n" + "=" * 60)
            print("✅ LIMPIEZA COMPLETADA")
            print("=" * 60)
            print("Datos eliminados:")
            print("  - Sesiones de estudiantes")
            print("  - Intentos de ejercicios")
            print("  - Submissions")
            print("  - Cognitive traces")
            print("  - Governance logs")
            print("\nDatos preservados:")
            print("  - Actividades")
            print("  - Ejercicios")
            print("  - Usuarios")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ Error durante la limpieza: {e}")
            raise
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(clean_activity_data())
