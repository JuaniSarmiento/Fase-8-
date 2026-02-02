"""
Script para verificar datos guardados en exercise_attempts_v2
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os
from dotenv import load_dotenv

load_dotenv()

async def check_exercise_attempts():
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@127.0.0.1:5433/ai_native")
    engine = create_async_engine(DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        # Buscar el último test student
        result = await conn.execute(text("""
            SELECT user_id, COUNT(*) as attempts, AVG(grade) as avg_grade
            FROM exercise_attempts_v2
            WHERE user_id LIKE 'test-e2e-student%'
            GROUP BY user_id
            ORDER BY MAX(submitted_at) DESC
            LIMIT 1
        """))
        
        row = result.fetchone()
        if row:
            print(f"Último estudiante de test: {row[0]}")
            print(f"Intentos guardados: {row[1]}")
            print(f"Promedio de notas: {row[2]}")
            
            # Ver detalles
            detail_result = await conn.execute(text("""
                SELECT 
                    ea.exercise_id,
                    ea.grade,
                    ea.ai_feedback,
                    ea.passed,
                    LENGTH(ea.code_submitted) as code_length
                FROM exercise_attempts_v2 ea
                WHERE ea.user_id = :user_id
                ORDER BY ea.submitted_at DESC
            """), {"user_id": row[0]})
            
            print("\nDetalles de ejercicios:")
            for i, ex in enumerate(detail_result.fetchall(), 1):
                print(f"  {i}. Exercise {ex[0][:8]}... - Grade: {ex[1]}, Passed: {ex[3]}, Code length: {ex[4]}")
                if ex[2]:
                    print(f"     Feedback: {ex[2][:50]}...")
        else:
            print("No se encontraron intentos de test students")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_exercise_attempts())
