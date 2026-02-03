import asyncio
import asyncpg

async def update_passwords():
    conn = await asyncpg.connect(
        host='localhost',
        port=5433,
        user='postgres',
        password='postgres',
        database='ai_native'
    )
    
    # Hash generado con bcrypt para "admin123"
    admin_hash = '$2b$12$hWeK0VYBoY28EJCKlr71TO6fFf5Yp5bDR6Lx/Uhs028vpFebfaesy'
    
    await conn.execute(
        'UPDATE users SET hashed_password = $1 WHERE email = $2',
        admin_hash, 'admin@ainative.dev'
    )
    
    await conn.execute(
        'UPDATE users SET hashed_password = $1 WHERE email = $2',
        admin_hash, 'teacher@ainative.dev'
    )
    
    await conn.execute(
        'UPDATE users SET hashed_password = $1 WHERE email = $2',
        admin_hash, 'student@ainative.dev'
    )
    
    print("✅ Passwords actualizados correctamente")
    print(f"   admin@ainative.dev / admin123")
    print(f"   teacher@ainative.dev / admin123")
    print(f"   student@ainative.dev / admin123")
    
    await conn.close()

if __name__ == '__main__':
    asyncio.run(update_passwords())
