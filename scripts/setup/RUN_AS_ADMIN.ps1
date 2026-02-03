# Script launcher que se auto-eleva a Administrador
# Ejecutar este archivo para reconstruir la base de datos

$scriptPath = Join-Path $PSScriptRoot "rebuild_database.ps1"

# Verificar si ya corremos como Admin
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "============================================" -ForegroundColor Yellow
    Write-Host "Se requieren permisos de Administrador" -ForegroundColor Yellow
    Write-Host "============================================" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Relanzando con permisos elevados..." -ForegroundColor Cyan
    Write-Host ""
    
    # Relanzar como Administrador
    Start-Process powershell.exe -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`"" -Verb RunAs -Wait
    
    Write-Host ""
    Write-Host "Proceso completado. Presiona Enter para cerrar..." -ForegroundColor Green
    $null = Read-Host
    exit
}

# Si ya somos admin, ejecutar el script
& $scriptPath
