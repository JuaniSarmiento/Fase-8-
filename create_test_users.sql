-- Crear usuarios de prueba con contraseña demo123
-- Hash generado con bcrypt: $2b$12$m8GQ1dc03FEyrEb1d.GkuOluAvPXXPRBq200uaju.Ypa4eCEniLLC.

-- Eliminar si existen
DELETE FROM users WHERE email IN ('docente@test.com', 'alumno@test.com');

-- Insertar docente
INSERT INTO users (id, email, username, hashed_password, full_name, roles, is_active)
VALUES (
    'docente-001',
    'docente@test.com',
    'docente',
    '$2b$12$m8GQ1dc03FEyrEb1d.GkuOluAvPXXPRBq200uaju.Ypa4eCEniLLC.',
    'Profesor Demo',
    '["teacher"]'::jsonb,
    true
);

-- Insertar alumno
INSERT INTO users (id, email, username, hashed_password, full_name, roles, is_active)
VALUES (
    'alumno-001',
    'alumno@test.com',
    'alumno',
    '$2b$12$m8GQ1dc03FEyrEb1d.GkuOluAvPXXPRBq200uaju.Ypa4eCEniLLC.',
    'Estudiante Demo',
    '["student"]'::jsonb,
    true
);

-- Inscribir alumno en el curso
INSERT INTO enrollments (enrollment_id, student_id, commission_id, status, enrollment_date)
VALUES ('enroll-alumno-001', 'alumno-001', 'commission-001', 'active', NOW())
ON CONFLICT DO NOTHING;

-- Verificar
SELECT id, email, full_name, roles FROM users WHERE email LIKE '%test.com';
