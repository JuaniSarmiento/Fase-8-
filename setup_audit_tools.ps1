# Setup Script for Schema Audit Tools
# Run this to install required dependencies

Write-Host "🔧 Setting up Schema Audit Tools..." -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Check Python installation
Write-Host "🐍 Checking Python installation..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "   ❌ Python not found!" -ForegroundColor Red
    Write-Host "   Please install Python 3.11+ from https://www.python.org/" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Install required packages
Write-Host "📦 Installing required packages..." -ForegroundColor Yellow
$requiredPackages = @("colorama", "sqlalchemy", "psycopg2-binary", "python-dotenv")

foreach ($package in $requiredPackages) {
    Write-Host "   Installing $package..." -ForegroundColor Cyan
    pip install $package --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ $package installed" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Failed to install $package" -ForegroundColor Yellow
    }
}

Write-Host ""

# Test imports
Write-Host "🧪 Testing imports..." -ForegroundColor Yellow
$testScript = @"
import colorama
import sqlalchemy
import psycopg2
import dotenv
print('✅ All imports successful!')
"@

$testScript | python 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ All dependencies working!" -ForegroundColor Green
} else {
    Write-Host "   ❌ Import test failed" -ForegroundColor Red
}

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "🎯 Next steps:" -ForegroundColor Cyan
Write-Host "   1. Ensure PostgreSQL is running:" -ForegroundColor White
Write-Host "      Get-Service | Where-Object { `$_.Name -like '*postgres*' }" -ForegroundColor Gray
Write-Host ""
Write-Host "   2. Find database password:" -ForegroundColor White
Write-Host "      python find_db_password.py" -ForegroundColor Gray
Write-Host ""
Write-Host "   3. Run schema audit:" -ForegroundColor White
Write-Host "      python audit_schema.py --dry-run  # Without DB connection" -ForegroundColor Gray
Write-Host "      python audit_schema.py            # With DB connection" -ForegroundColor Gray
Write-Host ""
Write-Host "[Documentation] SCHEMA_AUDIT_GUIDE.md" -ForegroundColor Cyan
Write-Host ""
