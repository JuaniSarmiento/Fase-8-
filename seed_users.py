"""
Seed Users Script - Populate database with test users for development

Creates:
- Teacher: docente@test.com
- Student 1: alumno1@test.com  
- Student 2: alumno2@test.com

All with password: 123456
"""
import asyncio
import sys
import uuid
from pathlib import Path
from sqlalchemy import select

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.src_v3.infrastructure.persistence.database import AsyncSessionLocal
from backend.src_v3.infrastructure.persistence.sqlalchemy.simple_models import UserModel
from backend.src_v3.core.security import get_password_hash


# Test users configuration
TEST_USERS = [
    {
        "email": "docente@test.com",
        "username": "docente",
        "password": "123456",
        "full_name": "Profe Juani",
        "roles": ["teacher", "admin"]
    },
    {
        "email": "alumno1@test.com",
        "username": "alumno1",
        "password": "123456",
        "full_name": "Luna Estudiante",
        "roles": ["student"]
    },
    {
        "email": "alumno2@test.com",
        "username": "alumno2",
        "password": "123456",
        "full_name": "Lautaro Frontend",
        "roles": ["student"]
    }
]


async def seed_users():
    """Create test users in the database."""
    print("\n" + "="*60)
    print("SEEDING TEST USERS")
    print("="*60 + "\n")
    
    async with AsyncSessionLocal() as session:
        created_count = 0
        existing_count = 0
        
        for user_data in TEST_USERS:
            email = user_data["email"]
            
            # Check if user already exists
            result = await session.execute(
                select(UserModel).where(UserModel.email == email)
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print(f"⚠️  User {email} already exists (ID: {existing_user.id[:8]}...)")
                existing_count += 1
                continue
            
            # Create new user
            hashed_password = get_password_hash(user_data["password"])
            
            new_user = UserModel(
                id=str(uuid.uuid4()),
                email=user_data["email"],
                username=user_data["username"],
                hashed_password=hashed_password,
                full_name=user_data["full_name"],
                roles=user_data["roles"],
                is_active=True
            )
            
            session.add(new_user)
            await session.commit()
            
            print(f"✅ User {email} created")
            print(f"   - Username: {user_data['username']}")
            print(f"   - Name: {user_data['full_name']}")
            print(f"   - Roles: {', '.join(user_data['roles'])}")
            print(f"   - Password: {user_data['password']}")
            print(f"   - ID: {new_user.id}")
            print()
            
            created_count += 1
    
    print("="*60)
    print("SUMMARY")
    print("="*60)
    print(f"✅ Created: {created_count}")
    print(f"⚠️  Already existed: {existing_count}")
    print(f"📊 Total users: {created_count + existing_count}")
    print()
    
    if created_count > 0:
        print("🔐 Login Credentials:")
        print("-"*60)
        for user_data in TEST_USERS:
            print(f"Email: {user_data['email']}")
            print(f"Password: {user_data['password']}")
            print(f"Roles: {', '.join(user_data['roles'])}")
            print()
    
    print("="*60)
    print("✅ Seeding completed!")
    print("="*60)
    print()


async def main():
    """Main execution."""
    try:
        await seed_users()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
