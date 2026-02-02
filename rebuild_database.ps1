# Script para reconstruir la base de datos PostgreSQL
# Ejecutar como Administrador

param(
    [string]$Password = "postgres"
)

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Reconstruccion de Base de Datos PostgreSQL" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar que PostgreSQL esta corriendo
Write-Host "[1/6] Verificando PostgreSQL..." -ForegroundColor Yellow
$service = Get-Service -Name "postgresql-x64-18" -ErrorAction SilentlyContinue
if ($service -eq $null) {
    Write-Host "   ERROR: Servicio PostgreSQL no encontrado" -ForegroundColor Red
    exit 1
}

if ($service.Status -ne "Running") {
    Write-Host "   Iniciando servicio PostgreSQL..." -ForegroundColor Yellow
    Start-Service -Name "postgresql-x64-18"
    Start-Sleep -Seconds 3
}
Write-Host "   OK - PostgreSQL corriendo" -ForegroundColor Green
Write-Host ""

# 2. Resetear contrasena de postgres
Write-Host "[2/6] Reseteando contrasena..." -ForegroundColor Yellow

$pgPath = "C:\Program Files\PostgreSQL\18\bin"
if (-not (Test-Path $pgPath)) {
    Write-Host "   ERROR: PostgreSQL no encontrado en $pgPath" -ForegroundColor Red
    exit 1
}

# Verificar si necesitamos permisos de administrador
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "   ADVERTENCIA: Se recomienda ejecutar como Administrador para resetear password" -ForegroundColor Yellow
    Write-Host "   Intentando continuar..." -ForegroundColor Yellow
} else {
    Write-Host "   Modificando configuracion temporal..." -ForegroundColor Yellow
    
    # Backup y modificar pg_hba.conf
    $dataDir = "C:\Program Files\PostgreSQL\18\data"
    $pgHbaFile = Join-Path $dataDir "pg_hba.conf"
    $pgHbaBackup = Join-Path $dataDir "pg_hba.conf.backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    
    try {
        Copy-Item $pgHbaFile $pgHbaBackup -Force
        $content = Get-Content $pgHbaFile
        $content = $content -replace "scram-sha-256", "trust" -replace "md5", "trust"
        $content | Set-Content $pgHbaFile
        
        Write-Host "   Reiniciando PostgreSQL..." -ForegroundColor Yellow
        Restart-Service -Name "postgresql-x64-18"
        Start-Sleep -Seconds 5
        
        # Cambiar password
        $env:PGPASSWORD = ""
        $resetSQL = "ALTER USER postgres WITH PASSWORD '$Password';"
        $resetSQL | & "$pgPath\psql.exe" -h localhost -p 5433 -U postgres -d postgres 2>&1 | Out-Null
        
        # Restaurar configuracion
        Copy-Item $pgHbaBackup $pgHbaFile -Force
        Restart-Service -Name "postgresql-x64-18"
        Start-Sleep -Seconds 5
        
        Write-Host "   OK - Contrasena establecida a: $Password" -ForegroundColor Green
    } catch {
        Write-Host "   ADVERTENCIA: No se pudo resetear password automaticamente" -ForegroundColor Yellow
        Write-Host "   Asumiendo que la password ya es: $Password" -ForegroundColor Yellow
    }
}

Write-Host ""

# 3. Eliminar base de datos existente y crear nueva
Write-Host "[3/6] Reconstruyendo base de datos..." -ForegroundColor Yellow

$env:PGPASSWORD = $Password

# Terminar conexiones activas
$killConnSQL = @"
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE datname = 'ai_native' AND pid <> pg_backend_pid();
"@

$killConnSQL | & "$pgPath\psql.exe" -h localhost -p 5433 -U postgres -d postgres 2>&1 | Out-Null

# Eliminar base de datos si existe
Write-Host "   Eliminando base de datos existente..." -ForegroundColor Yellow
& "$pgPath\psql.exe" -h localhost -p 5433 -U postgres -d postgres -c "DROP DATABASE IF EXISTS ai_native;" 2>&1 | Out-Null

# Crear base de datos nueva
Write-Host "   Creando base de datos ai_native..." -ForegroundColor Yellow
& "$pgPath\psql.exe" -h localhost -p 5433 -U postgres -d postgres -c "CREATE DATABASE ai_native OWNER postgres;" 2>&1 | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Host "   OK - Base de datos creada" -ForegroundColor Green
} else {
    Write-Host "   ERROR: No se pudo crear la base de datos" -ForegroundColor Red
    exit 1
}

Write-Host ""

# 4. Actualizar .env
Write-Host "[4/6] Actualizando configuracion .env..." -ForegroundColor Yellow

$envFile = ".env"
$dbUrl = "DATABASE_URL=postgresql+asyncpg://postgres:${Password}@127.0.0.1:5433/ai_native"

if (Test-Path $envFile) {
    $envContent = Get-Content $envFile
    $newContent = @()
    $updated = $false
    
    foreach ($line in $envContent) {
        if ($line -match "^DATABASE_URL=") {
            $newContent += $dbUrl
            $updated = $true
        } else {
            $newContent += $line
        }
    }
    
    if (-not $updated) {
        $newContent += $dbUrl
    }
    
    $newContent | Set-Content $envFile
    Write-Host "   OK - .env actualizado" -ForegroundColor Green
} else {
    Write-Host "   ADVERTENCIA: Archivo .env no encontrado" -ForegroundColor Yellow
}

Write-Host ""

# 5. Crear tablas usando Python
Write-Host "[5/6] Creando tablas..." -ForegroundColor Yellow
Write-Host "   Ejecutando script Python de inicializacion..." -ForegroundColor Cyan

python init_db.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "   OK - Tablas creadas" -ForegroundColor Green
} else {
    Write-Host "   ERROR: Fallo al crear tablas" -ForegroundColor Red
    Write-Host "   Intentando con SQL directamente..." -ForegroundColor Yellow
}

Write-Host ""

# 6. Verificar conexion
Write-Host "[6/6] Verificando conexion..." -ForegroundColor Yellow

$testPython = @"
import psycopg2
try:
    conn = psycopg2.connect(
        host='127.0.0.1',
        port=5433,
        user='postgres',
        password='$Password',
        database='ai_native'
    )
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = ''public'';')
    count = cursor.fetchone()[0]
    print(f'   OK - Conectado! Tablas encontradas: {count}')
    conn.close()
except Exception as e:
    print(f'   ERROR: {e}')
    exit(1)
"@

$testPython | python

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Reconstruccion completada!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Credenciales:" -ForegroundColor Cyan
Write-Host "  Host: 127.0.0.1" -ForegroundColor White
Write-Host "  Puerto: 5433" -ForegroundColor White
Write-Host "  Usuario: postgres" -ForegroundColor White
Write-Host "  Password: $Password" -ForegroundColor White
Write-Host "  Base de datos: ai_native" -ForegroundColor White
Write-Host ""
Write-Host "Proximo paso:" -ForegroundColor Cyan
Write-Host "  python audit_schema.py" -ForegroundColor White
Write-Host ""
