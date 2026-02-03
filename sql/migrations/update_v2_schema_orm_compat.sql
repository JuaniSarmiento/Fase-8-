-- ===================================================================
-- Esquema V2 Fase 2: Compatibilidad ORM (simple_models.py)
-- ===================================================================

-- 1. Agregar columnas faltantes a exercises_v2
ALTER TABLE exercises_v2 ADD COLUMN IF NOT EXISTS subject_id VARCHAR(36); -- FK opcional por ahora si no existe tabla subjects
ALTER TABLE exercises_v2 ADD COLUMN IF NOT EXISTS unit_number INTEGER DEFAULT 1;
ALTER TABLE exercises_v2 ADD COLUMN IF NOT EXISTS tags JSONB DEFAULT '[]'::jsonb;
ALTER TABLE exercises_v2 ADD COLUMN IF NOT EXISTS estimated_time_minutes INTEGER DEFAULT 30;
ALTER TABLE exercises_v2 ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE exercises_v2 ADD COLUMN IF NOT EXISTS order_index INTEGER DEFAULT 0;

-- 2. Asegurar columnas de activity (ActivityModel)
-- Ya agregamos 'subject'. Verificamos otras.
ALTER TABLE activities ADD COLUMN IF NOT EXISTS difficulty_level VARCHAR(50);
ALTER TABLE activities ADD COLUMN IF NOT EXISTS policies JSONB DEFAULT '{}'::jsonb;
ALTER TABLE activities ADD COLUMN IF NOT EXISTS start_date TIMESTAMP WITH TIME ZONE;
ALTER TABLE activities ADD COLUMN IF NOT EXISTS end_date TIMESTAMP WITH TIME ZONE;
ALTER TABLE activities ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE activities ADD COLUMN IF NOT EXISTS unit_id VARCHAR(50) DEFAULT '1';

-- 3. Crear tabla subjects si no existe (referenciada por FK subject_id)
CREATE TABLE IF NOT EXISTS subjects (
    subject_id VARCHAR(36) PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    credits INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Insertar un subject default si está vacía
INSERT INTO subjects (subject_id, code, name, credits)
VALUES ('sub-001', 'PROG1', 'Programación 1', 6)
ON CONFLICT (subject_id) DO NOTHING;

-- 4. Actualizar activities existentes con unit_id (not null en modelo)
UPDATE activities SET unit_id = '1' WHERE unit_id IS NULL;
