# ===================================================================
# SCRIPT DE DIAGNÓSTICO - Backend AI-Native V3
# ===================================================================
# Verifica el estado de la base de datos y los servicios
#
# Uso: .\diagnostico.ps1
# ===================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   DIAGNÓSTICO AI-NATIVE BACKEND V3" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Estado de contenedores
Write-Host "📦 ESTADO DE CONTENEDORES:" -ForegroundColor Yellow
docker-compose ps
Write-Host ""

# 2. Verificar conectividad con PostgreSQL
Write-Host "🔌 CONECTIVIDAD A POSTGRESQL:" -ForegroundColor Yellow
docker exec ai_native_postgres pg_isready -U postgres
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ PostgreSQL está accesible" -ForegroundColor Green
} else {
    Write-Host "❌ PostgreSQL no responde" -ForegroundColor Red
}
Write-Host ""

# 3. Listar tablas en la base de datos
Write-Host "📋 TABLAS EN LA BASE DE DATOS:" -ForegroundColor Yellow
docker exec ai_native_postgres psql -U postgres -d ai_native -c "\dt"
Write-Host ""

# 4. Verificar tablas críticas
Write-Host "🔍 VERIFICANDO TABLAS CRÍTICAS:" -ForegroundColor Yellow
$tables = @("activities", "exercises_v2", "users", "submissions", "grade_audits")

foreach ($table in $tables) {
    $result = docker exec ai_native_postgres psql -U postgres -d ai_native -c "\d $table" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ $table existe" -ForegroundColor Green
    } else {
        Write-Host "   ❌ $table NO existe" -ForegroundColor Red
    }
}
Write-Host ""

# 5. Verificar usuario y conexión
Write-Host "👤 USUARIO Y BASE DE DATOS:" -ForegroundColor Yellow
docker exec ai_native_postgres psql -U postgres -d ai_native -c "SELECT current_user, current_database();"
Write-Host ""

# 6. Contar registros en tablas principales
Write-Host "📊 CONTEO DE REGISTROS:" -ForegroundColor Yellow
Write-Host "   Contando registros en activities..." -ForegroundColor Gray
docker exec ai_native_postgres psql -U postgres -d ai_native -c "SELECT COUNT(*) as activities FROM activities;"
Write-Host "   Contando registros en users..." -ForegroundColor Gray
docker exec ai_native_postgres psql -U postgres -d ai_native -c "SELECT COUNT(*) as users FROM users;"
Write-Host "   Contando registros en exercises..." -ForegroundColor Gray
docker exec ai_native_postgres psql -U postgres -d ai_native -c "SELECT COUNT(*) as exercises FROM exercises;"
Write-Host ""

# 7. Verificar variable de entorno DATABASE_URL
Write-Host "🔐 VARIABLE DE ENTORNO DATABASE_URL:" -ForegroundColor Yellow
if (Test-Path .env) {
    $dbUrl = Get-Content .env | Select-String -Pattern "DATABASE_URL"
    if ($dbUrl) {
        Write-Host "   $dbUrl" -ForegroundColor White
    } else {
        Write-Host "   ⚠️  DATABASE_URL no encontrada en .env" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ❌ Archivo .env no encontrado" -ForegroundColor Red
}
Write-Host ""

# 8. Últimas 10 líneas de logs del backend
Write-Host "📝 ÚLTIMOS LOGS DEL BACKEND:" -ForegroundColor Yellow
docker logs ai_native_backend --tail 10 2>&1
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   DIAGNÓSTICO COMPLETADO" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
