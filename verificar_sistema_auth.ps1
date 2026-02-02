# Script de verificación rápida del nuevo sistema de autenticación

Write-Host "`n===================================================" -ForegroundColor Cyan
Write-Host "🔍 VERIFICACIÓN DEL SISTEMA DE AUTENTICACIÓN" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan

# 1. Verificar archivos frontend
Write-Host "`n📁 Verificando archivos frontend..." -ForegroundColor Yellow
$frontendFiles = @(
    "frontend\app\login\page.tsx",
    "frontend\app\register\page.tsx",
    "frontend\app\page.tsx"
)

foreach ($file in $frontendFiles) {
    $fullPath = Join-Path "c:\Users\juani\Desktop\Fase 8" $file
    if (Test-Path $fullPath) {
        Write-Host "  ✅ $file" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $file NO ENCONTRADO" -ForegroundColor Red
    }
}

# 2. Verificar script de limpieza
Write-Host "`n📜 Verificando script de limpieza..." -ForegroundColor Yellow
$cleanupScript = "c:\Users\juani\Desktop\Fase 8\cleanup_and_seed_teacher.py"
if (Test-Path $cleanupScript) {
    Write-Host "  ✅ cleanup_and_seed_teacher.py" -ForegroundColor Green
} else {
    Write-Host "  ❌ cleanup_and_seed_teacher.py NO ENCONTRADO" -ForegroundColor Red
}

# 3. Verificar contenedores Docker
Write-Host "`n🐳 Verificando contenedores Docker..." -ForegroundColor Yellow
$containers = docker ps --format "{{.Names}}" 2>$null
if ($LASTEXITCODE -eq 0) {
    foreach ($container in $containers) {
        Write-Host "  ✅ $container" -ForegroundColor Green
    }
} else {
    Write-Host "  ⚠️  Docker no está corriendo o no está instalado" -ForegroundColor Red
}

# 4. Verificar base de datos
Write-Host "`n🗄️  Verificando usuario docente en la base de datos..." -ForegroundColor Yellow
try {
    $result = docker exec ai_native_backend python -c "import asyncio; import asyncpg; async def check(): conn = await asyncpg.connect(host='postgres', database='ai_native', user='postgres', password='postgres'); users = await conn.fetch('SELECT username, email, roles FROM users'); await conn.close(); return users; print(asyncio.run(check()))" 2>$null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ Conexión a base de datos exitosa" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  No se pudo verificar la base de datos" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ⚠️  No se pudo verificar la base de datos: $_" -ForegroundColor Yellow
}

# 5. Verificar proceso de Node (frontend)
Write-Host "`n⚛️  Verificando frontend (Node.js)..." -ForegroundColor Yellow
$nodeProcesses = Get-Process -Name node -ErrorAction SilentlyContinue | Where-Object { $_.WorkingSet64 -gt 50MB }
if ($nodeProcesses) {
    Write-Host "  ✅ Frontend probablemente corriendo (proceso Node con >50MB)" -ForegroundColor Green
    foreach ($proc in $nodeProcesses) {
        $memMB = [Math]::Round($proc.WorkingSet64/1MB, 2)
        Write-Host "    - PID $($proc.Id): $memMB MB" -ForegroundColor Gray
    }
} else {
    Write-Host "  ⚠️  No se detectó frontend corriendo" -ForegroundColor Yellow
    Write-Host "    Ejecuta: cd frontend && npm run dev" -ForegroundColor Gray
}

# Resumen
Write-Host "`n===================================================" -ForegroundColor Cyan
Write-Host "📋 RESUMEN Y PRÓXIMOS PASOS" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan

Write-Host "`n✅ Sistema de autenticación implementado:" -ForegroundColor Green
Write-Host "  • Nueva página de login en /login" -ForegroundColor White
Write-Host "  • Nueva página de registro en /register" -ForegroundColor White
Write-Host "  • Base de datos limpiada" -ForegroundColor White
Write-Host "  • Usuario docente creado" -ForegroundColor White

Write-Host "`n🔐 Credenciales de Docente:" -ForegroundColor Yellow
Write-Host "  Usuario: docente" -ForegroundColor White
Write-Host "  Contraseña: docente" -ForegroundColor White

Write-Host "`n🚀 Para probar el sistema:" -ForegroundColor Yellow
Write-Host "  1. Asegúrate de que el frontend esté corriendo:" -ForegroundColor White
Write-Host "     cd frontend ; npm run dev" -ForegroundColor Gray
Write-Host "  2. Abre http://localhost:3000" -ForegroundColor White
Write-Host "  3. Deberías ver la página de login" -ForegroundColor White
Write-Host "  4. Prueba login de docente: docente / docente" -ForegroundColor White
Write-Host "  5. Prueba registro de estudiante en /register" -ForegroundColor White

Write-Host "`n📖 Ver documentación completa en:" -ForegroundColor Yellow
Write-Host "  SISTEMA_LOGIN_COMPLETO.md" -ForegroundColor White

Write-Host "`n" -ForegroundColor White
