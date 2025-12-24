# ============================================
# Workana Automation - Setup Completo
# Execute: .\setup.ps1
# ============================================

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " WORKANA AUTOMATION - INSTALACAO" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$rootDir = $PSScriptRoot

# ----------------------------------------
# PASSO 1: Configurar Backend
# ----------------------------------------
Write-Host "[1/5] Configurando Backend..." -ForegroundColor Yellow

Set-Location "$rootDir\backend"

# Criar ambiente virtual se nao existir
if (-not (Test-Path "venv")) {
    Write-Host "   -> Criando ambiente virtual Python..." -ForegroundColor Gray
    python -m venv venv
}

# Ativar ambiente virtual
Write-Host "   -> Ativando ambiente virtual..." -ForegroundColor Gray
& ".\venv\Scripts\Activate.ps1"

# Instalar dependencias
Write-Host "   -> Instalando dependencias Python..." -ForegroundColor Gray
pip install -r requirements.txt --quiet

Write-Host "   OK Backend configurado!" -ForegroundColor Green

# ----------------------------------------
# PASSO 2: Instalar Playwright
# ----------------------------------------
Write-Host "[2/5] Instalando Playwright..." -ForegroundColor Yellow
playwright install chromium
Write-Host "   OK Playwright instalado!" -ForegroundColor Green

# ----------------------------------------
# PASSO 3: Criar arquivo .env
# ----------------------------------------
Write-Host "[3/5] Configurando variaveis de ambiente..." -ForegroundColor Yellow

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "   OK Arquivo .env criado!" -ForegroundColor Green
}
else {
    Write-Host "   -> Arquivo .env ja existe (mantido)" -ForegroundColor Gray
}

# ----------------------------------------
# PASSO 4: Configurar Frontend
# ----------------------------------------
Write-Host "[4/5] Configurando Frontend..." -ForegroundColor Yellow

Set-Location "$rootDir\frontend"

Write-Host "   -> Instalando dependencias Node.js..." -ForegroundColor Gray
npm install

Write-Host "   OK Frontend configurado!" -ForegroundColor Green

# ----------------------------------------
# PASSO 5: Finalizacao
# ----------------------------------------
Write-Host "[5/5] Finalizando instalacao..." -ForegroundColor Yellow

Set-Location $rootDir

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host " INSTALACAO CONCLUIDA COM SUCESSO!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Para iniciar o sistema, execute:" -ForegroundColor Cyan
Write-Host ""
Write-Host "   .\start.ps1" -ForegroundColor White
Write-Host ""
