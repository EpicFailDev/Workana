# ============================================
# Workana Automation - Iniciar Sistema
# Execute: .\start.ps1
# ============================================

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " WORKANA AUTOMATION - INICIANDO" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$rootDir = $PSScriptRoot

# ----------------------------------------
# Iniciar Backend em nova janela
# ----------------------------------------
Write-Host "-> Iniciando Backend (FastAPI)..." -ForegroundColor Yellow

Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$rootDir\backend'; .\venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

Start-Sleep -Seconds 3

# ----------------------------------------
# Iniciar Frontend em nova janela
# ----------------------------------------
Write-Host "-> Iniciando Frontend (Next.js)..." -ForegroundColor Yellow

Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$rootDir\frontend'; npm run dev"

Start-Sleep -Seconds 5

# ----------------------------------------
# Mostrar status
# ----------------------------------------
Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host " SISTEMA INICIADO!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host " Frontend:     http://localhost:3000" -ForegroundColor White
Write-Host " API:          http://localhost:8000" -ForegroundColor White
Write-Host " Swagger:      http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "Feche as janelas do PowerShell para parar os servicos" -ForegroundColor Gray
Write-Host ""

# ----------------------------------------
# Abrir navegador automaticamente
# ----------------------------------------
Start-Sleep -Seconds 2
Start-Process "http://localhost:3000"
