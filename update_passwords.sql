-- Script para actualizar passwords de usuarios
-- Hash bcrypt para password: admin123

UPDATE users 
SET hashed_password = '$2b$12$hWeK0VYBoY28EJCKlr71TO6fFf5Yp5bDR6Lx/Uhs028vpFebfaesy'
WHERE email IN ('admin@ainative.dev', 'teacher@ainative.dev', 'student@ainative.dev');

-- Verificar
SELECT email, LEFT(hashed_password, 20) || '...' as password_hash FROM users;
