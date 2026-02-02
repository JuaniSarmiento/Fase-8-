-- Limpiar base de datos completa
-- Orden: primero las tablas que tienen dependencias, luego las principales

-- Limpiar trazas cognitivas
DELETE FROM cognitive_traces_v2;

-- Limpiar intentos de ejercicios
DELETE FROM exercise_attempts_v2;

-- Limpiar sesiones
DELETE FROM sessions_v2;

-- Limpiar ejercicios (si quieres conservarlos, comenta esta línea)
-- DELETE FROM exercises_v2;

-- Limpiar actividades (si quieres conservarlas, comenta esta línea)
-- DELETE FROM activities;

-- Limpiar usuarios de prueba (si existen en la tabla users)
-- DELETE FROM users WHERE email LIKE 'test-%@example.com';

-- Verificar que todo esté limpio
SELECT 'cognitive_traces_v2' as tabla, COUNT(*) as registros FROM cognitive_traces_v2
UNION ALL
SELECT 'exercise_attempts_v2', COUNT(*) FROM exercise_attempts_v2
UNION ALL
SELECT 'sessions_v2', COUNT(*) FROM sessions_v2;
