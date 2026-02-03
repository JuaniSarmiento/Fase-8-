# Script para instalar dependencias del panel de estudiantes
# Ejecutar desde el directorio raíz del proyecto

Write-Host "🚀 Instalando dependencias para Panel de Estudiantes..." -ForegroundColor Cyan

# Ir al directorio frontend
Set-Location -Path "frontend"

Write-Host "`n📦 Instalando dependencias de npm..." -ForegroundColor Yellow

# Instalar dependencias principales si no están instaladas
$dependencies = @(
    "@radix-ui/react-scroll-area",
    "@radix-ui/react-separator",
    "react-syntax-highlighter"
)

$devDependencies = @(
    "@types/react-syntax-highlighter"
)

# Instalar dependencias
foreach ($dep in $dependencies) {
    Write-Host "  Installing $dep..." -ForegroundColor Gray
}

npm install @radix-ui/react-scroll-area @radix-ui/react-separator react-syntax-highlighter

# Instalar dev dependencies
foreach ($dep in $devDependencies) {
    Write-Host "  Installing $dep (dev)..." -ForegroundColor Gray
}

npm install --save-dev @types/react-syntax-highlighter

Write-Host "`n✅ Dependencias instaladas correctamente!" -ForegroundColor Green

# Volver al directorio raíz
Set-Location -Path ".."

Write-Host "`n📋 Próximos pasos:" -ForegroundColor Cyan
Write-Host "  1. Iniciar backend: cd backend && python -m uvicorn src_v3.main:app --reload" -ForegroundColor White
Write-Host "  2. Iniciar frontend: cd frontend && npm run dev" -ForegroundColor White
Write-Host "  3. Abrir navegador: http://localhost:3000" -ForegroundColor White
Write-Host "  4. Login como estudiante: juan.martinez@example.com / password123" -ForegroundColor White

Write-Host "`n🎉 ¡Listo para usar el panel de estudiantes!" -ForegroundColor Green
