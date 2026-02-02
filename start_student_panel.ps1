# Script para iniciar el panel de estudiantes

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Iniciando Panel de Estudiantes" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 1. Verificar que Docker Desktop está corriendo
Write-Host "`n[1/3] Verificando Docker..." -ForegroundColor Yellow
$dockerRunning = docker ps 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Docker no está corriendo. Inicia Docker Desktop primero." -ForegroundColor Red
    exit 1
}
Write-Host "✓ Docker corriendo" -ForegroundColor Green

# 2. Verificar que PostgreSQL está corriendo
Write-Host "`n[2/3] Verificando PostgreSQL..." -ForegroundColor Yellow
$pgContainer = docker ps --filter "name=ai_native_postgres" --format "{{.Names}}"
if (-not $pgContainer) {
    Write-Host "PostgreSQL no está corriendo. Iniciando..." -ForegroundColor Yellow
    docker start ai_native_postgres
    Start-Sleep -Seconds 5
}
Write-Host "✓ PostgreSQL corriendo en puerto 5433" -ForegroundColor Green

# 3. Iniciar Backend
Write-Host "`n[3/3] Iniciando servidores..." -ForegroundColor Yellow
Write-Host "Backend: http://localhost:8000" -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Cyan

# Crear datos de prueba para estudiante
Write-Host "`nCreando sesiones de prueba para estudiante alumno1@test.com..." -ForegroundColor Yellow
docker exec ai_native_postgres psql -U postgres -d ai_native -c "INSERT INTO sessions_v2 (session_id, user_id, activity_id, created_at) SELECT gen_random_uuid(), '70ed9d32-7bf5-4ae2-9aa9-d40ffeba4aea', activity_id, NOW() FROM activities WHERE activity_id NOT IN (SELECT activity_id FROM sessions_v2 WHERE user_id = '70ed9d32-7bf5-4ae2-9aa9-d40ffeba4aea') LIMIT 10 ON CONFLICT DO NOTHING;" 2>&1 | Out-Null

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Ambos servidores están corriendo!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Para acceder al panel de estudiantes:" -ForegroundColor Yellow
Write-Host "1. Abre: http://localhost:3000" -ForegroundColor White
Write-Host "2. Haz login con: alumno1@test.com / alumno1" -ForegroundColor White
Write-Host "3. Serás redirigido a /student/activities" -ForegroundColor White
Write-Host ""
Write-Host "Los logs del backend están en la otra terminal." -ForegroundColor Gray
Write-Host "Presiona CTRL+C en ambas terminales para detener los servidores." -ForegroundColor Gray
Write-Host ""
