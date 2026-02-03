-- ========================================
-- LMS Hierarchical Architecture Migration
-- ========================================
-- Creates: Modules, Enrollments, UserGamification tables
-- Updates: Activities with module_id, Exercises with grading fields

-- ========================================
-- 1. CREATE MODULES TABLE
-- ========================================
CREATE TABLE IF NOT EXISTS modules (
    module_id VARCHAR(36) PRIMARY KEY,
    course_id VARCHAR(36) NOT NULL REFERENCES courses(course_id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    order_index INTEGER NOT NULL DEFAULT 0,
    is_published BOOLEAN NOT NULL DEFAULT FALSE,
    metadata_json JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for modules
CREATE INDEX IF NOT EXISTS idx_modules_course ON modules(course_id);
CREATE INDEX IF NOT EXISTS idx_modules_course_order ON modules(course_id, order_index);
CREATE INDEX IF NOT EXISTS idx_modules_published ON modules(is_published);

COMMENT ON TABLE modules IS 'Course modules for hierarchical content organization';

-- ========================================
-- 2. CREATE ENROLLMENT TYPES
-- ========================================
DO $$ BEGIN
    CREATE TYPE enrollment_role AS ENUM ('STUDENT', 'TEACHER', 'TA', 'OBSERVER');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE enrollment_status AS ENUM ('ACTIVE', 'INACTIVE', 'COMPLETED', 'DROPPED');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- ========================================
-- 3. CREATE ENROLLMENTS TABLE
-- ========================================
CREATE TABLE IF NOT EXISTS enrollments (
    enrollment_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id VARCHAR(36) NOT NULL REFERENCES courses(course_id) ON DELETE CASCADE,
    role enrollment_role NOT NULL DEFAULT 'STUDENT',
    status enrollment_status NOT NULL DEFAULT 'ACTIVE',
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
CREATE INDEX IF NOT EXISTS idx_enrollments_status ON enrollments(status);
CREATE INDEX IF NOT EXISTS idx_enrollments_role ON enrollments(role);

COMMENT ON TABLE enrollments IS 'Many-to-Many enrollment relationship between users and courses';

-- ========================================
-- 4. CREATE USER GAMIFICATION TABLE
-- ========================================
CREATE TABLE IF NOT EXISTS user_gamification (
    user_id VARCHAR(36) PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    xp INTEGER NOT NULL DEFAULT 0,
    level INTEGER NOT NULL DEFAULT 1,
    streak_days INTEGER NOT NULL DEFAULT 0,
    last_activity_date DATE,
    longest_streak INTEGER NOT NULL DEFAULT 0,
    achievements JSONB DEFAULT '[]',
    badges JSONB DEFAULT '[]',
    total_exercises_completed INTEGER NOT NULL DEFAULT 0,
    total_activities_completed INTEGER NOT NULL DEFAULT 0,
    total_hints_used INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for gamification
CREATE INDEX IF NOT EXISTS idx_gamification_user ON user_gamification(user_id);
CREATE INDEX IF NOT EXISTS idx_gamification_level ON user_gamification(level);
CREATE INDEX IF NOT EXISTS idx_gamification_xp ON user_gamification(xp);

COMMENT ON TABLE user_gamification IS 'User gamification metrics (XP, levels, streaks)';

-- ========================================
-- 5. UPDATE ACTIVITIES TABLE
-- ========================================
-- Add module_id and order_index to activities (if not exists)
DO $$ BEGIN
    ALTER TABLE activities ADD COLUMN module_id VARCHAR(36) REFERENCES modules(module_id) ON DELETE CASCADE;
    ALTER TABLE activities ADD COLUMN order_index INTEGER NOT NULL DEFAULT 0;
EXCEPTION
    WHEN duplicate_column THEN null;
END $$;

-- Create index for module_id
CREATE INDEX IF NOT EXISTS idx_activities_module ON activities(module_id);
CREATE INDEX IF NOT EXISTS idx_activities_module_order ON activities(module_id, order_index);

COMMENT ON COLUMN activities.module_id IS 'Parent module for hierarchical organization';
COMMENT ON COLUMN activities.order_index IS 'Display order within module';

-- ========================================
-- 6. UPDATE EXERCISES TABLE (V2)
-- ========================================
-- Add reference_solution and grading_config to exercises_v2 (if not exists)
DO $$ BEGIN
    ALTER TABLE exercises_v2 ADD COLUMN reference_solution TEXT;
    ALTER TABLE exercises_v2 ADD COLUMN grading_config JSONB DEFAULT '{}';
EXCEPTION
    WHEN duplicate_column THEN null;
END $$;

COMMENT ON COLUMN exercises_v2.reference_solution IS 'Detailed reference solution for AI grading';
COMMENT ON COLUMN exercises_v2.grading_config IS 'AI grading configuration (weights, rubrics)';

-- ========================================
-- 7. DATA MIGRATION - Create default enrollments from user_profiles
-- ========================================
-- Migrate existing course_id relationships to enrollments
INSERT INTO enrollments (enrollment_id, user_id, course_id, role, status, enrolled_at)
SELECT 
    gen_random_uuid()::text AS enrollment_id,
    up.user_id,
    up.course_id,
    CASE 
        WHEN u.role = 'TEACHER' THEN 'TEACHER'::enrollment_role
        ELSE 'STUDENT'::enrollment_role
    END AS role,
    'ACTIVE'::enrollment_status AS status,
    up.created_at AS enrolled_at
FROM user_profiles up
JOIN users u ON up.user_id = u.id
WHERE up.course_id IS NOT NULL
ON CONFLICT (user_id, course_id) DO NOTHING;

-- ========================================
-- 8. INITIALIZE GAMIFICATION FOR EXISTING USERS
-- ========================================
-- Create gamification records for all existing users
INSERT INTO user_gamification (user_id)
SELECT id FROM users
WHERE id NOT IN (SELECT user_id FROM user_gamification)
ON CONFLICT (user_id) DO NOTHING;

-- ========================================
-- 9. REMOVE DEPRECATED COLUMNS (OPTIONAL - COMMENT OUT IF NEEDED)
-- ========================================
-- WARNING: Only run this after verifying enrollment migration worked
-- ALTER TABLE user_profiles DROP COLUMN IF EXISTS course_id;
-- ALTER TABLE user_profiles DROP COLUMN IF EXISTS commission_id;

-- For now, leave them as deprecated but not dropped for backward compatibility

-- ========================================
-- 10. VERIFICATION QUERIES
-- ========================================
-- Check module count
SELECT COUNT(*) AS module_count FROM modules;

-- Check enrollment count
SELECT COUNT(*) AS enrollment_count FROM enrollments;

-- Check gamification count
SELECT COUNT(*) AS gamification_count FROM user_gamification;

-- Check activities with modules
SELECT COUNT(*) AS activities_with_modules FROM activities WHERE module_id IS NOT NULL;

-- Check enrollment distribution
SELECT role, status, COUNT(*) 
FROM enrollments 
GROUP BY role, status 
ORDER BY role, status;

-- ========================================
-- SUCCESS MESSAGE
-- ========================================
SELECT 'LMS Hierarchical Architecture Migration Complete!' AS message;
