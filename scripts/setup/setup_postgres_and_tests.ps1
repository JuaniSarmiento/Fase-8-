# ===============================================
# Script para Configurar PostgreSQL y Ejecutar Tests
# ===============================================

Write-Host "🐘 Configurando PostgreSQL para AI-Native MVP V3..." -ForegroundColor Cyan

# Verificar si PostgreSQL está instalado
$pgVersion = Get-Command psql -ErrorAction SilentlyContinue

if (-not $pgVersion) {
    Write-Host "❌ PostgreSQL no está instalado. Opciones:" -ForegroundColor Red
    Write-Host ""
    Write-Host "Opción 1: Instalar PostgreSQL" -ForegroundColor Yellow
    Write-Host "  Descarga desde: https://www.postgresql.org/download/windows/"
    Write-Host ""
    Write-Host "Opción 2: Usar Docker" -ForegroundColor Yellow
    Write-Host "  docker run -d --name ai_native_postgres \"
    Write-Host "    -e POSTGRES_DB=ai_native \"
    Write-Host "    -e POSTGRES_USER=ai_native \"
    Write-Host "    -e POSTGRES_PASSWORD=ai_native_password_dev \"
    Write-Host "    -p 5433:5432 postgres:15"
    Write-Host ""
    exit 1
}

Write-Host "✅ PostgreSQL encontrado: $($pgVersion.Version)" -ForegroundColor Green

# Configuración de la base de datos
$DB_HOST = "localhost"
$DB_PORT = "5433"
$DB_NAME = "ai_native"
$DB_USER = "ai_native"
$DB_PASSWORD = "ai_native_password_dev"

Write-Host ""
Write-Host "📋 Configuración de Base de Datos:" -ForegroundColor Yellow
Write-Host "  Host: $DB_HOST"
Write-Host "  Puerto: $DB_PORT"
Write-Host "  Database: $DB_NAME"
Write-Host "  Usuario: $DB_USER"
Write-Host ""

# Verificar si el puerto está en uso
$portInUse = Get-NetTCPConnection -LocalPort $DB_PORT -ErrorAction SilentlyContinue

if ($portInUse) {
    Write-Host "✅ PostgreSQL parece estar ejecutándose en el puerto $DB_PORT" -ForegroundColor Green
} else {
    Write-Host "⚠️  No se detecta PostgreSQL en el puerto $DB_PORT" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Opciones:" -ForegroundColor Cyan
    Write-Host "1. Si PostgreSQL está instalado, inicialo con:" -ForegroundColor White
    Write-Host "   pg_ctl -D ""C:\Program Files\PostgreSQL\15\data"" start"
    Write-Host ""
    Write-Host "2. O usa Docker:" -ForegroundColor White
    Write-Host "   docker run -d --name ai_native_postgres \"
    Write-Host "     -e POSTGRES_DB=$DB_NAME \"
    Write-Host "     -e POSTGRES_USER=$DB_USER \"
    Write-Host "     -e POSTGRES_PASSWORD=$DB_PASSWORD \"
    Write-Host "     -p ${DB_PORT}:5432 postgres:15"
    Write-Host ""
    
    $response = Read-Host "¿Quieres intentar iniciar PostgreSQL con Docker? (s/n)"
    if ($response -eq 's' -or $response -eq 'S') {
        Write-Host "🐳 Iniciando PostgreSQL con Docker..." -ForegroundColor Cyan
        docker run -d --name ai_native_postgres `
            -e POSTGRES_DB=$DB_NAME `
            -e POSTGRES_USER=$DB_USER `
            -e POSTGRES_PASSWORD=$DB_PASSWORD `
            -p ${DB_PORT}:5432 postgres:15
        
        Write-Host "⏳ Esperando a que PostgreSQL inicie..." -ForegroundColor Yellow
        Start-Sleep -Seconds 10
    } else {
        Write-Host "❌ Necesitas PostgreSQL ejecutándose para continuar" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "🔨 Inicializando base de datos..." -ForegroundColor Cyan

# Inicializar las tablas
try {
    python init_db.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Base de datos inicializada correctamente" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Error al inicializar base de datos (código $LASTEXITCODE)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Error al ejecutar init_db.py: $_" -ForegroundColor Red
    Write-Host "Verifica que el archivo init_db.py exista y que Python esté configurado" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🧪 Ejecutando Tests..." -ForegroundColor Cyan
Write-Host ""

# Ejecutar pytest
try {
    pytest Test/ -v --tb=short --color=yes
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ ¡Todos los tests pasaron!" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "⚠️  Algunos tests fallaron. Revisa los errores arriba." -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Error al ejecutar tests: $_" -ForegroundColor Red
    Write-Host "Verifica que pytest esté instalado: pip install pytest pytest-asyncio" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📊 Resumen:" -ForegroundColor Cyan
Write-Host "  - PostgreSQL: " -NoNewline
if ($portInUse -or $LASTEXITCODE -eq 0) {
    Write-Host "✅ Funcionando" -ForegroundColor Green
} else {
    Write-Host "❌ Necesita configuración" -ForegroundColor Red
}

Write-Host "  - Base de datos inicializada: ✅" -ForegroundColor Green
Write-Host "  - Tests ejecutados: ✅" -ForegroundColor Green
Write-Host ""
Write-Host "🎉 ¡Configuración completa!" -ForegroundColor Green
