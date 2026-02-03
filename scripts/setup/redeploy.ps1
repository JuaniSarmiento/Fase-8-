# ===================================================================
# SCRIPT DE REDEPLOY Y DIAGNÓSTICO - Backend AI-Native V3
# ===================================================================
# Este script reinicia todos los contenedores Docker y ejecuta
# las migraciones de base de datos desde cero.
#
# Uso: .\redeploy.ps1
# ===================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   REDEPLOY AI-NATIVE BACKEND V3" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Paso 1: Detener y eliminar contenedores + volúmenes
Write-Host "[1/5] Deteniendo contenedores y eliminando volúmenes..." -ForegroundColor Yellow
docker-compose down -v

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error al detener contenedores" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Contenedores detenidos y volúmenes eliminados" -ForegroundColor Green
Write-Host ""

# Paso 2: Levantar contenedores
Write-Host "[2/5] Levantando contenedores..." -ForegroundColor Yellow
docker-compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error al levantar contenedores" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Contenedores levantados" -ForegroundColor Green
Write-Host ""

# Paso 3: Esperar a que PostgreSQL esté listo
Write-Host "[3/5] Esperando a que PostgreSQL esté listo..." -ForegroundColor Yellow
$maxAttempts = 30
$attempt = 0

while ($attempt -lt $maxAttempts) {
    $attempt++
    $status = docker exec ai_native_postgres pg_isready -U postgres 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ PostgreSQL está listo" -ForegroundColor Green
        break
    }
    
    Write-Host "   Intento $attempt/$maxAttempts - Esperando..." -ForegroundColor Gray
    Start-Sleep -Seconds 2
}

if ($attempt -eq $maxAttempts) {
    Write-Host "❌ PostgreSQL no respondió después de $maxAttempts intentos" -ForegroundColor Red
    Write-Host "Mostrando logs de PostgreSQL:" -ForegroundColor Yellow
    docker logs ai_native_postgres --tail 50
    exit 1
}

Write-Host ""

# Paso 4: Ejecutar migraciones de base de datos
Write-Host "[4/5] Ejecutando migraciones de base de datos..." -ForegroundColor Yellow

# Verificar que las tablas base existan
Write-Host "   Verificando esquema base..." -ForegroundColor Gray
docker exec ai_native_postgres psql -U postgres -d ai_native -c "\dt" | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Base de datos vacía - necesita migración inicial" -ForegroundColor Yellow
}

# Crear tablas de submissions y grade_audits
Write-Host "   Creando tablas de grading..." -ForegroundColor Gray
python -m backend.src_v3.scripts.create_grading_tables

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Advertencia: No se pudieron crear algunas tablas" -ForegroundColor Yellow
    Write-Host "   Esto es normal si ya existen o si falta el esquema base" -ForegroundColor Gray
} else {
    Write-Host "✅ Migraciones ejecutadas correctamente" -ForegroundColor Green
}

Write-Host ""

# Paso 5: Verificar estado de la base de datos
Write-Host "[5/5] Verificando estado de la base de datos..." -ForegroundColor Yellow
docker exec ai_native_postgres psql -U postgres -d ai_native -c "\dt" | Select-String -Pattern "activities|exercises|submissions|grade_audits"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   REDEPLOY COMPLETADO" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 Comandos útiles:" -ForegroundColor Cyan
Write-Host "   Ver logs del backend:  docker-compose logs -f backend" -ForegroundColor White
Write-Host "   Ver logs de postgres:  docker logs ai_native_postgres" -ForegroundColor White
Write-Host "   Verificar salud:       docker-compose ps" -ForegroundColor White
Write-Host "   Conectar a DB:         docker exec -it ai_native_postgres psql -U postgres -d ai_native" -ForegroundColor White
Write-Host ""

# Opcional: Mostrar logs del backend en tiempo real
$showLogs = Read-Host "¿Quieres ver los logs del backend en tiempo real? (s/n)"
if ($showLogs -eq "s" -or $showLogs -eq "S") {
    Write-Host ""
    Write-Host "Mostrando logs del backend (Ctrl+C para salir)..." -ForegroundColor Yellow
    Write-Host ""
    docker-compose logs -f backend
}
