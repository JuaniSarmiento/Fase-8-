-- ============================================================================
-- INDICES CRÍTICOS PARA PERFORMANCE
-- AI-Native MVP V3
-- ============================================================================
-- Ejecutar con: psql -U postgres -d ai_native -f add_critical_indexes.sql
-- O desde Docker: docker exec -i ai_native_postgres psql -U postgres -d ai_native < add_critical_indexes.sql
-- ============================================================================

\echo '🔍 Creando índices críticos...'

-- ============================================================================
-- USERS (búsquedas frecuentes)
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- ============================================================================
-- SESSIONS_V2 (queries más frecuentes del sistema)
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions_v2(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_activity_id ON sessions_v2(activity_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions_v2(status);
CREATE INDEX IF NOT EXISTS idx_sessions_start_time ON sessions_v2(start_time DESC);
-- Índice compuesto para búsquedas combinadas
CREATE INDEX IF NOT EXISTS idx_sessions_user_activity ON sessions_v2(user_id, activity_id);

-- ============================================================================
-- COGNITIVE_TRACES_V2 (mucha lectura en trazabilidad)
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_traces_session_id ON cognitive_traces_v2(session_id);
CREATE INDEX IF NOT EXISTS idx_traces_activity_id ON cognitive_traces_v2(activity_id);
CREATE INDEX IF NOT EXISTS idx_traces_interaction_type ON cognitive_traces_v2(interaction_type);
CREATE INDEX IF NOT EXISTS idx_traces_timestamp ON cognitive_traces_v2(timestamp DESC);
-- Índice compuesto para queries comunes
CREATE INDEX IF NOT EXISTS idx_traces_session_type ON cognitive_traces_v2(session_id, interaction_type);

-- ============================================================================
-- EXERCISE_ATTEMPTS_V2 (evaluaciones y estadísticas)
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_attempts_session_id ON exercise_attempts_v2(session_id);
CREATE INDEX IF NOT EXISTS idx_attempts_exercise_id ON exercise_attempts_v2(exercise_id);
CREATE INDEX IF NOT EXISTS idx_attempts_student_id ON exercise_attempts_v2(student_id);
CREATE INDEX IF NOT EXISTS idx_attempts_submitted_at ON exercise_attempts_v2(submitted_at DESC);
CREATE INDEX IF NOT EXISTS idx_attempts_passed ON exercise_attempts_v2(passed);
-- Índice compuesto para obtener último intento
CREATE INDEX IF NOT EXISTS idx_attempts_student_exercise ON exercise_attempts_v2(student_id, exercise_id, submitted_at DESC);

-- ============================================================================
-- SUBMISSIONS (entregas finales)
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_submissions_student_id ON submissions(student_id);
CREATE INDEX IF NOT EXISTS idx_submissions_activity_id ON submissions(activity_id);
CREATE INDEX IF NOT EXISTS idx_submissions_submitted_at ON submissions(submitted_at DESC);
-- Índice compuesto para búsquedas de entregas
CREATE INDEX IF NOT EXISTS idx_submissions_student_activity ON submissions(student_id, activity_id);

-- ============================================================================
-- RISKS_V2 (análisis de riesgo)
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_risks_session_id ON risks_v2(session_id);
CREATE INDEX IF NOT EXISTS idx_risks_activity_id ON risks_v2(activity_id);
CREATE INDEX IF NOT EXISTS idx_risks_level ON risks_v2(risk_level);
CREATE INDEX IF NOT EXISTS idx_risks_created_at ON risks_v2(created_at DESC);

-- ============================================================================
-- EXERCISES_V2 (búsquedas por actividad)
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_exercises_activity_id ON exercises_v2(activity_id);
CREATE INDEX IF NOT EXISTS idx_exercises_difficulty ON exercises_v2(difficulty_level);

-- ============================================================================
-- ACTIVITIES (búsquedas por profesor y estado)
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_activities_teacher_id ON activities(teacher_id);
CREATE INDEX IF NOT EXISTS idx_activities_status ON activities(status);
CREATE INDEX IF NOT EXISTS idx_activities_created_at ON activities(created_at DESC);

-- ============================================================================
-- JSONB INDEXES (para búsquedas en campos JSON)
-- ============================================================================
-- Índice GIN para búsquedas en datos JSON de traces
CREATE INDEX IF NOT EXISTS idx_traces_interactional_data ON cognitive_traces_v2 USING GIN (interactional_data);
CREATE INDEX IF NOT EXISTS idx_traces_cognitive_reasoning ON cognitive_traces_v2 USING GIN (cognitive_reasoning);

-- Índice para buscar contenido de mensajes (usado en risk analysis)
CREATE INDEX IF NOT EXISTS idx_traces_content ON cognitive_traces_v2 ((interactional_data->>'content'));

\echo '✅ Índices creados exitosamente'

-- ============================================================================
-- ANÁLISIS DE PERFORMANCE
-- ============================================================================
\echo ''
\echo '📊 Analizando tablas...'
ANALYZE users;
ANALYZE sessions_v2;
ANALYZE cognitive_traces_v2;
ANALYZE exercise_attempts_v2;
ANALYZE submissions;
ANALYZE risks_v2;
ANALYZE exercises_v2;
ANALYZE activities;

\echo '✅ Análisis completado'

-- ============================================================================
-- VERIFICAR ÍNDICES CREADOS
-- ============================================================================
\echo ''
\echo '📋 Índices en sessions_v2:'
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'sessions_v2' 
ORDER BY indexname;

\echo ''
\echo '📋 Índices en cognitive_traces_v2:'
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'cognitive_traces_v2' 
ORDER BY indexname;

\echo ''
\echo '📋 Índices en exercise_attempts_v2:'
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'exercise_attempts_v2' 
ORDER BY indexname;

\echo ''
\echo '🎉 ÍNDICES CRÍTICOS INSTALADOS - Performance mejorado significativamente'
