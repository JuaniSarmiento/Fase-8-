# PostgreSQL Password Reset Script
# Run this script as Administrator if you need to reset the postgres password

param(
    [string]$NewPassword = "postgres"
)

Write-Host "🔧 PostgreSQL Password Reset Utility" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "❌ This script requires Administrator privileges!" -ForegroundColor Red
    Write-Host "   Please right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

# Find PostgreSQL installation
$pgPath = "C:\Program Files\PostgreSQL\18\bin"
if (-not (Test-Path $pgPath)) {
    Write-Host "❌ PostgreSQL not found at: $pgPath" -ForegroundColor Red
    Write-Host "   Please adjust the path in this script" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Found PostgreSQL at: $pgPath" -ForegroundColor Green
Write-Host ""

# Stop PostgreSQL service
Write-Host "🛑 Stopping PostgreSQL service..." -ForegroundColor Yellow
Stop-Service -Name "postgresql-x64-18" -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Modify pg_hba.conf to allow trust authentication temporarily
$dataDir = "C:\Program Files\PostgreSQL\18\data"
$pgHbaFile = Join-Path $dataDir "pg_hba.conf"
$pgHbaBackup = Join-Path $dataDir "pg_hba.conf.backup"

Write-Host "📝 Backing up pg_hba.conf..." -ForegroundColor Yellow
Copy-Item $pgHbaFile $pgHbaBackup -Force

Write-Host "🔓 Temporarily allowing trust authentication..." -ForegroundColor Yellow
$content = Get-Content $pgHbaFile
$content = $content -replace "md5", "trust"
$content = $content -replace "scram-sha-256", "trust"
$content | Set-Content $pgHbaFile

# Start PostgreSQL service
Write-Host "▶️  Starting PostgreSQL service..." -ForegroundColor Yellow
Start-Service -Name "postgresql-x64-18"
Start-Sleep -Seconds 3

# Reset password using psql
Write-Host "🔑 Resetting password for user 'postgres'..." -ForegroundColor Yellow
$env:PGPASSWORD = ""
$resetSQL = "ALTER USER postgres WITH PASSWORD '$NewPassword';"

& "$pgPath\psql.exe" -h localhost -p 5433 -U postgres -d postgres -c $resetSQL

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Password reset successful!" -ForegroundColor Green
} else {
    Write-Host "❌ Password reset failed!" -ForegroundColor Red
}

# Restore pg_hba.conf
Write-Host "📝 Restoring pg_hba.conf..." -ForegroundColor Yellow
Copy-Item $pgHbaBackup $pgHbaFile -Force
Remove-Item $pgHbaBackup

# Restart PostgreSQL service
Write-Host "🔄 Restarting PostgreSQL service..." -ForegroundColor Yellow
Restart-Service -Name "postgresql-x64-18"
Start-Sleep -Seconds 3

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "✅ DONE!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 New password: $NewPassword" -ForegroundColor Yellow
Write-Host ""
Write-Host "💡 Update your .env file with:" -ForegroundColor Cyan
Write-Host "DATABASE_URL=postgresql+asyncpg://postgres:$NewPassword@127.0.0.1:5433/ai_native" -ForegroundColor White
Write-Host ""
Write-Host "🧪 Test connection with:" -ForegroundColor Cyan
Write-Host "python find_db_password.py" -ForegroundColor White
Write-Host ""
