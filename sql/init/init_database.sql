-- ===================================================================
-- SCRIPT DE INICIALIZACIÓN COMPLETA DE BASE DE DATOS
-- Fase 8 - AI-Native MVP V3
-- ===================================================================
-- Ejecutar: docker exec ai_native_postgres psql -U postgres -d ai_native -f /tmp/init_database.sql
-- ===================================================================

-- Limpiar base de datos existente (CUIDADO: Esto borra TODOS los datos)
DROP TABLE IF EXISTS grade_audits CASCADE;
DROP TABLE IF EXISTS submissions CASCADE;
DROP TABLE IF EXISTS exercises CASCADE;
DROP TABLE IF EXISTS activities CASCADE;
DROP TABLE IF EXISTS enrollments CASCADE;
DROP TABLE IF EXISTS commissions CASCADE;
DROP TABLE IF EXISTS courses CASCADE;
DROP TABLE IF EXISTS subjects CASCADE;
DROP TABLE IF EXISTS user_profiles CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Limpiar tipos enumerados
DROP TYPE IF EXISTS submissionstatus CASCADE;
DROP TYPE IF EXISTS activitystatus CASCADE;
DROP TYPE IF EXISTS difficultylevel CASCADE;
DROP TYPE IF EXISTS userrole CASCADE;

-- ===================================================================
-- 1. CREAR TIPOS ENUMERADOS
-- ===================================================================

CREATE TYPE userrole AS ENUM ('student', 'teacher', 'admin');
CREATE TYPE activitystatus AS ENUM ('draft', 'active', 'archived');
CREATE TYPE difficultylevel AS ENUM ('INICIAL', 'INTERMEDIO', 'AVANZADO');
CREATE TYPE submissionstatus AS ENUM ('pending', 'submitted', 'graded', 'reviewed');

-- ===================================================================
-- 2. TABLA USERS (Base de autenticación)
-- ===================================================================

CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    roles JSONB DEFAULT '[]'::jsonb NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE NOT NULL,
    last_login TIMESTAMP WITH TIME ZONE,
    login_count INTEGER DEFAULT 0 NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_active ON users(is_active);

-- ===================================================================
-- 3. ESTRUCTURA ACADÉMICA
-- ===================================================================

-- 3.1 Subjects (Materias)
CREATE TABLE subjects (
    code VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    credits INTEGER,
    semester INTEGER,
    is_active BOOLEAN DEFAULT TRUE NOT NULL
);

CREATE INDEX idx_subjects_active ON subjects(is_active);

-- 3.2 Courses (Instancias de materias)
CREATE TABLE courses (
    course_id VARCHAR(36) PRIMARY KEY,
    subject_code VARCHAR(50) NOT NULL REFERENCES subjects(code) ON DELETE CASCADE,
    academic_year INTEGER NOT NULL,
    academic_period VARCHAR(10) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    UNIQUE(subject_code, academic_year, academic_period)
);

CREATE INDEX idx_courses_subject ON courses(subject_code);
CREATE INDEX idx_courses_period ON courses(academic_year, academic_period);

-- 3.3 Commissions (Comisiones/secciones de cursos)
CREATE TABLE commissions (
    commission_id VARCHAR(36) PRIMARY KEY,
    course_id VARCHAR(36) NOT NULL REFERENCES courses(course_id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    instructor_id VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
    schedule JSONB,
    max_students INTEGER,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_commissions_course ON commissions(course_id);
CREATE INDEX idx_commissions_instructor ON commissions(instructor_id);

-- 3.4 Enrollments (Inscripciones de estudiantes)
CREATE TABLE enrollments (
    enrollment_id VARCHAR(36) PRIMARY KEY,
    student_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    commission_id VARCHAR(36) NOT NULL REFERENCES commissions(commission_id) ON DELETE CASCADE,
    enrolled_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    status VARCHAR(20) DEFAULT 'active' NOT NULL,
    final_grade FLOAT,
    UNIQUE(student_id, commission_id)
);

CREATE INDEX idx_enrollments_student ON enrollments(student_id);
CREATE INDEX idx_enrollments_commission ON enrollments(commission_id);

-- ===================================================================
-- 4. ACTIVITIES (Actividades de aprendizaje)
-- ===================================================================

CREATE TABLE activities (
    activity_id VARCHAR(36) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    instructions TEXT NOT NULL,
    evaluation_criteria JSONB DEFAULT '[]'::jsonb,
    course_id VARCHAR(36) REFERENCES courses(course_id) ON DELETE CASCADE,
    teacher_id VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
    policies JSONB DEFAULT '{}'::jsonb NOT NULL,
    difficulty difficultylevel,
    estimated_duration_minutes INTEGER,
    learning_objectives JSONB DEFAULT '[]'::jsonb,
    tags JSONB DEFAULT '[]'::jsonb,
    status activitystatus DEFAULT 'draft' NOT NULL,
    max_score FLOAT DEFAULT 10.0 NOT NULL,
    passing_score FLOAT DEFAULT 6.0 NOT NULL,
    visibility_start TIMESTAMP WITH TIME ZONE,
    visibility_end TIMESTAMP WITH TIME ZONE,
    is_published BOOLEAN DEFAULT FALSE NOT NULL,
    published_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_activities_course ON activities(course_id);
CREATE INDEX idx_activities_teacher ON activities(teacher_id);
CREATE INDEX idx_activities_status ON activities(status);
CREATE INDEX idx_activities_published ON activities(is_published);

-- ===================================================================
-- 5. EXERCISES (Ejercicios de programación)
-- ===================================================================

CREATE TABLE exercises (
    exercise_id VARCHAR(36) PRIMARY KEY,
    activity_id VARCHAR(36) NOT NULL REFERENCES activities(activity_id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    difficulty VARCHAR(50),
    exercise_type VARCHAR(50) NOT NULL,
    language VARCHAR(50) NOT NULL DEFAULT 'python',
    test_cases JSONB,
    solution TEXT,
    template_code TEXT,
    order_index INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_exercises_activity ON exercises(activity_id);
CREATE INDEX idx_exercises_type ON exercises(exercise_type);

-- ===================================================================
-- 6. SUBMISSIONS (Entregas de estudiantes)
-- ===================================================================

CREATE TABLE submissions (
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

CREATE INDEX idx_submissions_student_activity ON submissions(student_id, activity_id);
CREATE INDEX idx_submissions_status ON submissions(status);
CREATE INDEX idx_submissions_graded_by ON submissions(graded_by);

-- ===================================================================
-- 7. GRADE AUDITS (Auditoría de calificaciones)
-- ===================================================================

CREATE TABLE grade_audits (
    audit_id VARCHAR(36) PRIMARY KEY,
    submission_id VARCHAR(36) NOT NULL REFERENCES submissions(submission_id) ON DELETE CASCADE,
    instructor_id VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
    previous_grade FLOAT,
    new_grade FLOAT NOT NULL,
    was_auto_grade BOOLEAN NOT NULL,
    override_reason TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_grade_audits_submission ON grade_audits(submission_id);
CREATE INDEX idx_grade_audits_instructor ON grade_audits(instructor_id);
CREATE INDEX idx_grade_audits_timestamp ON grade_audits(timestamp);

-- ===================================================================
-- 8. DATOS DE PRUEBA (OPCIONAL)
-- ===================================================================

-- Usuario administrador
INSERT INTO users (id, email, username, hashed_password, full_name, roles, is_active, is_verified)
VALUES (
    'admin-001',
    'admin@ainative.dev',
    'admin',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5lW7aJzz.KMN2', -- password: admin123
    'Administrator',
    '["admin", "teacher"]'::jsonb,
    TRUE,
    TRUE
);

-- Profesor de ejemplo
INSERT INTO users (id, email, username, hashed_password, full_name, roles, is_active, is_verified)
VALUES (
    'teacher-001',
    'teacher@ainative.dev',
    'teacher',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5lW7aJzz.KMN2', -- password: teacher123
    'Professor Smith',
    '["teacher"]'::jsonb,
    TRUE,
    TRUE
);

-- Estudiante de ejemplo
INSERT INTO users (id, email, username, hashed_password, full_name, roles, is_active, is_verified)
VALUES (
    'student-001',
    'student@ainative.dev',
    'student',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5lW7aJzz.KMN2', -- password: student123
    'John Student',
    '["student"]'::jsonb,
    TRUE,
    TRUE
);

-- Materia de ejemplo
INSERT INTO subjects (code, name, description, credits, semester, is_active)
VALUES (
    'PROG1',
    'Programación I',
    'Introducción a la programación con Python',
    6,
    1,
    TRUE
);

-- Curso de ejemplo
INSERT INTO courses (course_id, subject_code, academic_year, academic_period, is_active)
VALUES (
    'course-001',
    'PROG1',
    2026,
    '1C',
    TRUE
);

-- Comisión de ejemplo
INSERT INTO commissions (commission_id, course_id, name, instructor_id, max_students, is_active)
VALUES (
    'comm-001',
    'course-001',
    'Comisión A',
    'teacher-001',
    50,
    TRUE
);

-- Inscripción de ejemplo
INSERT INTO enrollments (enrollment_id, student_id, commission_id, status)
VALUES (
    'enroll-001',
    'student-001',
    'comm-001',
    'active'
);

-- ===================================================================
-- 9. VERIFICACIÓN
-- ===================================================================

\echo '=== Tablas creadas ==='
\dt

\echo '=== Conteo de registros ==='
SELECT 'users' AS table_name, COUNT(*) AS count FROM users
UNION ALL
SELECT 'subjects', COUNT(*) FROM subjects
UNION ALL
SELECT 'courses', COUNT(*) FROM courses
UNION ALL
SELECT 'commissions', COUNT(*) FROM commissions
UNION ALL
SELECT 'enrollments', COUNT(*) FROM enrollments
UNION ALL
SELECT 'activities', COUNT(*) FROM activities
UNION ALL
SELECT 'exercises', COUNT(*) FROM exercises
UNION ALL
SELECT 'submissions', COUNT(*) FROM submissions
UNION ALL
SELECT 'grade_audits', COUNT(*) FROM grade_audits;

\echo '=== Base de datos inicializada correctamente ==='
