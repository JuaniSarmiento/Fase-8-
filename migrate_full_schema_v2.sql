-- ===================================================================
-- MIGRACIÓN COMPLETA A ESQUEMA V2 (ORM Compatible)
-- ===================================================================
-- Este script alinea la BD existente (Legacy V1) con los modelos SQLAlchemy (V2)
-- ===================================================================

BEGIN;

-- 1. MIGRACIÓN SUBJECTS
-- 1.1. Renombrar tabla vieja para backup
ALTER TABLE subjects RENAME TO subjects_legacy;

-- 1.2. Crear tabla nueva según ORM
CREATE TABLE subjects (
    subject_id VARCHAR(36) PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    credits INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- 1.3. Migrar datos generando nuevos UUIDs
INSERT INTO subjects (subject_id, code, name, credits)
SELECT gen_random_uuid()::text, code, name, COALESCE(credits, 0)
FROM subjects_legacy;


-- 2. MIGRACIÓN COURSES
-- 2.1. Alinear columnas (renaming)
ALTER TABLE courses RENAME COLUMN academic_year TO year;
ALTER TABLE courses RENAME COLUMN academic_period TO semester;

-- 2.2. Agregar columna FK nueva
ALTER TABLE courses ADD COLUMN subject_id VARCHAR(36);

-- 2.3. Llenar subject_id basado en el código antiguo
UPDATE courses c
SET subject_id = s.subject_id
FROM subjects s
WHERE c.subject_code = s.code;

-- 2.4. Manejar cursos huérfanos (si existen codes que ya no están)
-- Asignar a un subject default o borrar. Asumimos borrado lógico o default.
-- (Opcional)

-- 2.5. Aplicar restricciones FK
ALTER TABLE courses ADD CONSTRAINT fk_courses_subject 
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id) ON DELETE CASCADE;

-- 2.6. Limpieza (opcional, mantener subject_code por ahora si se quiere, pero el ORM no lo tiene)
-- ALTER TABLE courses DROP COLUMN subject_code;


-- 3. MIGRACION EXERCISES_V2 (FKs)
-- 3.1. Asegurar columna subject_id (ya creada en script anterior, o crear si falla)
ALTER TABLE exercises_v2 ADD COLUMN IF NOT EXISTS subject_id VARCHAR(36);

-- 3.2. Asignar subject default a ejercicios huérfanos para poder poner FK
-- Tomamos el primer subject disponible como default
UPDATE exercises_v2 SET subject_id = (SELECT subject_id FROM subjects LIMIT 1) WHERE subject_id IS NULL;

-- 3.3. Crear FK
ALTER TABLE exercises_v2 ADD CONSTRAINT fk_exercises_v2_subject
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id) ON DELETE CASCADE;


-- 4. OTRAS TABLAS (Commissions, etc)
-- Si commissions tiene teacher_id, etc. verificar.
-- Commissions usa course_id, que es PK en courses (no cambió).

COMMIT;
