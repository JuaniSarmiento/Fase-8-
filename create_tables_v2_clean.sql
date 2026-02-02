-- ===================================================================
-- Esquema V2: Sincronización con Backend src_v3
-- ===================================================================

-- 1. Tabla exercises_v2
CREATE TABLE IF NOT EXISTS exercises_v2 (
    exercise_id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    activity_id VARCHAR(36) REFERENCES activities(activity_id) ON DELETE CASCADE,
    session_id VARCHAR(36), -- Opcional, para ejercicios generados en sesión
    
    title VARCHAR(255),       -- Mapeado a 'topic' en insert
    description TEXT,
    topic VARCHAR(255),
    difficulty VARCHAR(50),
    language VARCHAR(50) DEFAULT 'python',
    
    mission_markdown TEXT,    -- Mapeado a 'problem_statement' en insert
    problem_statement TEXT,
    
    starter_code TEXT,
    solution_code TEXT,       -- Mapeado a 'solution_template'
    solution_template TEXT,
    
    test_cases JSONB DEFAULT '[]'::jsonb,
    hints JSONB DEFAULT '[]'::jsonb,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_exercises_v2_activity ON exercises_v2(activity_id);

-- 2. Tabla exercise_attempts_v2
CREATE TABLE IF NOT EXISTS exercise_attempts_v2 (
    attempt_id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    exercise_id VARCHAR(36) REFERENCES exercises_v2(exercise_id) ON DELETE CASCADE,
    user_id VARCHAR(36) REFERENCES users(id) ON DELETE CASCADE,
    
    code_submitted TEXT,
    passed BOOLEAN DEFAULT FALSE,
    execution_output JSONB,
    
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_attempts_v2_user_exercise ON exercise_attempts_v2(user_id, exercise_id);

-- 3. Actualizar tabla activities (agregar columna subject faltante si es necesaria)
-- El backend intenta leer 'subject', así que la agregamos para evitar errores, aunque sea null.
ALTER TABLE activities ADD COLUMN IF NOT EXISTS subject VARCHAR(255);

-- 4. Migrar datos básicos (opcional, para no perder ejercicios existentes)
-- INSERT INTO exercises_v2 (exercise_id, activity_id, title, description, difficulty, language, starter_code)
-- SELECT exercise_id, activity_id, title, description, difficulty, language, template_code 
-- FROM exercises
-- ON CONFLICT DO NOTHING;
