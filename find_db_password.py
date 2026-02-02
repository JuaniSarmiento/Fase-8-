"""Quick script to find the correct PostgreSQL password."""
import psycopg2
import sys

passwords_to_try = [
    "postgres",
    "admin123",
    "password",
    "admin",
    "1234",
    "root",
    "",  # empty password
    "ai_native_password_dev",
    "12345",
    "123456",
    "postgres123",
    "postgres18",
    "Pass1234",
    "Password1",
    "qwerty",
    "abc123",
]

host = "127.0.0.1"
port = 5433
user = "postgres"
database = "ai_native"

print(f"🔍 Testing PostgreSQL connection...")
print(f"   Host: {host}:{port}")
print(f"   User: {user}")
print(f"   Database: {database}\n")

for password in passwords_to_try:
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            connect_timeout=3
        )
        print(f"✅ SUCCESS! Password is: '{password}'")
        print(f"\n📝 Update your .env file with:")
        print(f"DATABASE_URL=postgresql+asyncpg://postgres:{password}@127.0.0.1:5433/ai_native")
        conn.close()
        sys.exit(0)
    except psycopg2.OperationalError as e:
        if "password authentication failed" in str(e):
            print(f"❌ Wrong password: '{password}'")
        elif "database" in str(e) and "does not exist" in str(e):
            print(f"⚠️  Password '{password}' works but database 'ai_native' doesn't exist!")
            print(f"   You need to create the database first")
            sys.exit(0)
        else:
            print(f"❌ Error with '{password}': {e}")
    except Exception as e:
        print(f"❌ Unexpected error with '{password}': {e}")

print(f"\n❌ None of the common passwords worked!")
print(f"💡 You may need to reset the PostgreSQL password or check your installation")
