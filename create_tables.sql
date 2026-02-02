-- ===================================================================
-- Script SQL para crear tablas: submissions, grade_audits, exercises
-- ===================================================================
-- Ejecutar desde el contenedor:
-- docker exec -i ai_native_postgres psql -U postgres -d ai_native < create_tables.sql
-- ===================================================================

-- 1. Crear tabla exercises (si no existe)
CREATE TABLE IF NOT EXISTS exercises (
    exercise_id VARCHAR(36) PRIMARY KEY,
    activity_id VARCHAR(36) NOT NULL REFERENCES activities(activity_id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    difficulty VARCHAR(50),
    exercise_type VARCHAR(50) NOT NULL,
    language VARCHAR(50) NOT NULL DEFAULT 'python',
    test_cases JSONB,
    solution TEXT,  -- Reference solution (teacher only)
    template_code TEXT,  -- Starter code for students
    order_index INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_exercise_activity_id ON exercises(activity_id);

-- 2. Crear enum para status de submissions
DO $$ BEGIN
    CREATE TYPE submissionstatus AS ENUM ('pending', 'submitted', 'graded', 'reviewed');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 3. Crear tabla submissions
CREATE TABLE IF NOT EXISTS submissions (
    submission_id VARCHAR(36) PRIMARY KEY,
    student_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    activity_id VARCHAR(36) NOT NULL REFERENCES activities(activity_id) ON DELETE CASCADE,
    code_snapshot TEXT NOT NULL,
    status submissionstatus DEFAULT 'pending' NOT NULL,
    auto_grade FLOAT,
    final_grade FLOAT,
    is_manual_grade BOOLEAN DEFAULT FALSE NOT NULL,
    ai_feedback TEXT,
    teacher_feedback TEXT,
    test_results JSONB,
    execution_error TEXT,
    graded_by VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
    graded_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    submitted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_submission_student_activity ON submissions(student_id, activity_id);
CREATE INDEX IF NOT EXISTS idx_submission_status ON submissions(status);

-- 4. Crear tabla grade_audits
CREATE TABLE IF NOT EXISTS grade_audits (
    audit_id VARCHAR(36) PRIMARY KEY,
    submission_id VARCHAR(36) NOT NULL REFERENCES submissions(submission_id) ON DELETE CASCADE,
    instructor_id VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
    previous_grade FLOAT,
    new_grade FLOAT NOT NULL,
    was_auto_grade BOOLEAN NOT NULL,
    override_reason TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_submission ON grade_audits(submission_id);
CREATE INDEX IF NOT EXISTS idx_audit_instructor ON grade_audits(instructor_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON grade_audits(timestamp);

-- 5. Verificar tablas creadas
\dt

-- 6. Mostrar estructura de las tablas
\d exercises
\d submissions
\d grade_audits
