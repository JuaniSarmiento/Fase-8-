"""
Initialize database using Docker exec
This script works around asyncpg Windows authentication issues
"""
import subprocess
import sys

def run_sql(sql_command):
    """Execute SQL command in Docker container"""
    cmd = [
        'docker', 'exec', 'ai_native_postgres',
        'psql', '-U', 'postgres', '-d', 'ai_native',
        '-c', sql_command
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0, result.stdout, result.stderr

# SQL to create all tables
create_tables_sql = """
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Courses table
CREATE TABLE IF NOT EXISTS courses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    teacher_id UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Student sessions table
CREATE TABLE IF NOT EXISTS student_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID REFERENCES users(id),
    course_id UUID REFERENCES courses(id),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    status VARCHAR(50),
    metadata_json JSONB
);

-- Exercises table
CREATE TABLE IF NOT EXISTS exercises (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    course_id UUID REFERENCES courses(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    difficulty VARCHAR(50),
    topic VARCHAR(255),
    content JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Student responses table
CREATE TABLE IF NOT EXISTS student_responses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES student_sessions(id),
    exercise_id UUID REFERENCES exercises(id),
    response_text TEXT,
    is_correct BOOLEAN,
    feedback TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cognitive traces table
CREATE TABLE IF NOT EXISTS cognitive_traces (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES student_sessions(id),
    event_type VARCHAR(100),
    event_data JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata_json JSONB
);

-- Risk assessments table
CREATE TABLE IF NOT EXISTS risk_assessments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID REFERENCES users(id),
    course_id UUID REFERENCES courses(id),
    risk_score FLOAT,
    risk_level VARCHAR(50),
    factors JSONB,
    recommendations TEXT[],
    assessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User profiles table
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE REFERENCES users(id),
    learning_style VARCHAR(100),
    preferences JSONB,
    metadata_json JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_student_sessions_student_id ON student_sessions(student_id);
CREATE INDEX IF NOT EXISTS idx_student_sessions_course_id ON student_sessions(course_id);
CREATE INDEX IF NOT EXISTS idx_exercises_course_id ON exercises(course_id);
CREATE INDEX IF NOT EXISTS idx_student_responses_session_id ON student_responses(session_id);
CREATE INDEX IF NOT EXISTS idx_cognitive_traces_session_id ON cognitive_traces(session_id);
CREATE INDEX IF NOT EXISTS idx_risk_assessments_student_id ON risk_assessments(student_id);
"""

print("🔨 Initializing database in Docker container...")

# Execute SQL in chunks to avoid command line length limits
sql_commands = [cmd.strip() for cmd in create_tables_sql.split(';') if cmd.strip()]

success_count = 0
error_count = 0

for i, cmd in enumerate(sql_commands, 1):
    if cmd:
        success, stdout, stderr = run_sql(cmd + ';')
        if success:
            success_count += 1
            if stdout.strip():
                print(f"✅ Command {i}/{len(sql_commands)}: {stdout.strip()}")
        else:
            error_count += 1
            print(f"❌ Command {i}/{len(sql_commands)} failed: {stderr}")

print(f"\n{'='*50}")
print(f"✅ Database initialization complete!")
print(f"   Successful commands: {success_count}")
print(f"   Failed commands: {error_count}")
print(f"{'='*50}")

if error_count > 0:
    sys.exit(1)
