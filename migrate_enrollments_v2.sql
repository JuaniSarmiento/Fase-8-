-- ========================================
-- LMS Hierarchical Architecture Migration V2
-- ========================================
-- Handles existing enrollments table (renames to enrollments_old)
-- Creates new structure with course_id and roles

-- ========================================
-- 1. RENAME EXISTING ENROLLMENTS TABLE
-- ========================================
ALTER TABLE IF EXISTS enrollments RENAME TO enrollments_old;

-- ========================================
-- 2. CREATE NEW ENROLLMENT TYPES
-- ========================================
DO $$ BEGIN
    CREATE TYPE enrollment_role AS ENUM ('STUDENT', 'TEACHER', 'TA', 'OBSERVER');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE enrollment_status_new AS ENUM ('ACTIVE', 'INACTIVE', 'COMPLETED', 'DROPPED');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- ========================================
-- 3. CREATE NEW ENROLLMENTS TABLE
-- ========================================
CREATE TABLE IF NOT EXISTS enrollments (
    enrollment_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id VARCHAR(36) NOT NULL REFERENCES courses(course_id) ON DELETE CASCADE,
    role enrollment_role NOT NULL DEFAULT 'STUDENT',
    status enrollment_status_new NOT NULL DEFAULT 'ACTIVE',
    enrolled_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    dropped_at TIMESTAMPTZ,
    metadata_json JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, course_id)
);

-- Indexes for enrollments
CREATE INDEX IF NOT EXISTS idx_enrollments_user ON enrollments(user_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_course ON enrollments(course_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_user_course ON enrollments(user_id, course_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_status_new ON enrollments(status);
CREATE INDEX IF NOT EXISTS idx_enrollments_role ON enrollments(role);

COMMENT ON TABLE enrollments IS 'Many-to-Many enrollment relationship between users and courses (LMS V3)';

-- ========================================
-- 4. MIGRATE DATA FROM OLD ENROLLMENTS
-- ========================================
-- Migrate old enrollments to new structure (commission -> course mapping)
INSERT INTO enrollments (enrollment_id, user_id, course_id, role, status, enrolled_at)
SELECT 
    e.enrollment_id,
    e.student_id AS user_id,
    cm.course_id,  -- Get course_id from commission
    'STUDENT'::enrollment_role AS role,
    CASE 
        WHEN e.status = 'active' THEN 'ACTIVE'::enrollment_status_new
        WHEN e.status = 'completed' THEN 'COMPLETED'::enrollment_status_new
        ELSE 'INACTIVE'::enrollment_status_new
    END AS status,
    e.enrolled_at
FROM enrollments_old e
JOIN commissions cm ON e.commission_id = cm.commission_id
ON CONFLICT (user_id, course_id) DO NOTHING;

-- ========================================
-- 5. VERIFY MIGRATION
-- ========================================
SELECT 
    'Old enrollments: ' || COUNT(*) AS info FROM enrollments_old
UNION ALL
SELECT 
    'New enrollments: ' || COUNT(*) AS info FROM enrollments;

-- ========================================
-- SUCCESS MESSAGE
-- ========================================
SELECT 'Enrollments table migrated successfully!' AS message;
