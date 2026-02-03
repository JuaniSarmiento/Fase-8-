-- ===================================================================
-- MIGRACIÓN DEFINITIVA: ENUMS -> TEXTO
-- ===================================================================
-- Elimina la restricción estricta de tipos Enum de PostgreSQL
-- convirtiendo las columnas a VARCHAR. Esto evita errores de 
-- "LookupError" en lectura y "DatatypeMismatchError" en escritura.
-- ===================================================================

BEGIN;

-- 1. ACTIVITIES
-- Convertir status y difficulty_level
ALTER TABLE activities ALTER COLUMN status TYPE VARCHAR(50) USING status::text;
ALTER TABLE activities ALTER COLUMN difficulty_level TYPE VARCHAR(50) USING difficulty_level::text;

-- 2. SESSIONS_V2
-- Convertir status y mode
ALTER TABLE sessions_v2 ALTER COLUMN status TYPE VARCHAR(50) USING status::text;
ALTER TABLE sessions_v2 ALTER COLUMN mode TYPE VARCHAR(50) USING mode::text;

-- 3. EXERCISES_V2
-- Convertir difficulty y language
ALTER TABLE exercises_v2 ALTER COLUMN difficulty TYPE VARCHAR(50) USING difficulty::text;
ALTER TABLE exercises_v2 ALTER COLUMN language TYPE VARCHAR(50) USING language::text;

-- 4. COGNITIVE_TRACES_V2
-- Convertir trace_level e interaction_type
ALTER TABLE cognitive_traces_v2 ALTER COLUMN trace_level TYPE VARCHAR(50) USING trace_level::text;
ALTER TABLE cognitive_traces_v2 ALTER COLUMN interaction_type TYPE VARCHAR(50) USING interaction_type::text;


-- Opcional: Eliminar los tipos Enum si ya no se usan, para evitar confusión futura.
-- DROP TYPE IF EXISTS activitystatus;
-- DROP TYPE IF EXISTS difficultylevel;
-- DROP TYPE IF EXISTS sessionstatus;
-- etc.

COMMIT;
