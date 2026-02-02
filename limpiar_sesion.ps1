# Script para limpiar el navegador y forzar logout

Write-Host "`n======================================" -ForegroundColor Cyan
Write-Host "🔄 LIMPIEZA DE SESIÓN DEL NAVEGADOR" -ForegroundColor Cyan
Write-Host "======================================`n" -ForegroundColor Cyan

Write-Host "Para limpiar la sesión guardada y poder ver el login:" -ForegroundColor Yellow
Write-Host ""
Write-Host "Opción 1 - Desde el navegador (MÁS FÁCIL):" -ForegroundColor Green
Write-Host "  1. Abre http://localhost:3000" -ForegroundColor White
Write-Host "  2. Presiona F12 para abrir DevTools" -ForegroundColor White
Write-Host "  3. Ve a la pestaña 'Console'" -ForegroundColor White
Write-Host "  4. Escribe y ejecuta:" -ForegroundColor White
Write-Host "     localStorage.clear(); location.reload();" -ForegroundColor Cyan
Write-Host ""
Write-Host "Opción 2 - Modo incógnito:" -ForegroundColor Green
Write-Host "  1. Abre una ventana de incógnito (Ctrl+Shift+N)" -ForegroundColor White
Write-Host "  2. Ve a http://localhost:3000" -ForegroundColor White
Write-Host "  3. No tendrá sesión guardada" -ForegroundColor White
Write-Host ""
Write-Host "Opción 3 - Desde DevTools Application:" -ForegroundColor Green
Write-Host "  1. F12 → Pestaña 'Application'" -ForegroundColor White
Write-Host "  2. Sidebar izquierdo → 'Local Storage' → http://localhost:3000" -ForegroundColor White
Write-Host "  3. Click derecho → 'Clear'" -ForegroundColor White
Write-Host "  4. Recargar página (F5)" -ForegroundColor White
Write-Host ""

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "El error de gamification (404) es porque:" -ForegroundColor Yellow
Write-Host "  - Estás logueado con una sesión vieja" -ForegroundColor White
Write-Host "  - El endpoint /gamification no existe" -ForegroundColor White
Write-Host "  - Al limpiar localStorage, te redirigirá al login" -ForegroundColor White
Write-Host "======================================`n" -ForegroundColor Cyan
