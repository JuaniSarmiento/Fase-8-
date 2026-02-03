"""Verify seeded users in database"""
import asyncio
import asyncpg

async def verify():
    conn = await asyncpg.connect(
        'postgresql://postgres:postgres@127.0.0.1:5433/ai_native'
    )
    
    users = await conn.fetch("""
        SELECT email, username, full_name, roles, is_active, created_at
        FROM users 
        ORDER BY email
    """)
    
    print("\n" + "="*60)
    print("USUARIOS EN BASE DE DATOS")
    print("="*60 + "\n")
    
    for i, user in enumerate(users, 1):
        print(f"{i}. {user['email']}")
        print(f"   Username: {user['username']}")
        print(f"   Name: {user['full_name']}")
        print(f"   Roles: {user['roles']}")
        print(f"   Active: {user['is_active']}")
        print(f"   Created: {user['created_at']}")
        print()
    
    print("="*60)
    print(f"Total: {len(users)} usuarios")
    print("="*60)
    print()
    
    await conn.close()

asyncio.run(verify())
