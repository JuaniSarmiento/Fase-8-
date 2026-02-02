-- Migración: Agregar module_id a enrollments para comisiones
-- Fecha: 2026-02-01
-- Descripción: Permite asociar estudiantes a módulos específicos (comisiones)

-- 1. Agregar columna module_id
ALTER TABLE enrollments 
ADD COLUMN IF NOT EXISTS module_id VARCHAR(36);

-- 2. Agregar foreign key a modules
ALTER TABLE enrollments
ADD CONSTRAINT fk_enrollments_module 
FOREIGN KEY (module_id) REFERENCES modules(module_id) 
ON DELETE SET NULL;

-- 3. Crear índices
CREATE INDEX IF NOT EXISTS idx_enrollments_module ON enrollments(module_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_user_module ON enrollments(user_id, module_id);

-- 4. Eliminar índice unique de user_course (un usuario puede estar en múltiples módulos del mismo curso)
DROP INDEX IF EXISTS idx_enrollments_user_course;

-- 5. Crear nuevo índice no-único
CREATE INDEX IF NOT EXISTS idx_enrollments_user_course_nonunique ON enrollments(user_id, course_id);

COMMENT ON COLUMN enrollments.module_id IS 'Módulo/comisión específica del curso donde está inscrito el estudiante';
