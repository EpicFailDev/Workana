@echo off
title Workana Automation - Instalacao
color 0B

echo.
echo ============================================
echo    WORKANA AUTOMATION - INSTALACAO
echo ============================================
echo.

cd /d "%~dp0"

echo [1/5] Criando ambiente virtual Python...
cd backend
if not exist "venv" (
    python -m venv venv
)

echo [2/5] Ativando ambiente virtual...
call .\venv\Scripts\activate

echo [3/5] Instalando dependencias Python...
pip install -r requirements.txt --quiet

echo [4/5] Instalando Playwright...
playwright install chromium

echo [5/5] Configurando arquivo .env...
if not exist ".env" (
    copy .env.example .env
)

cd ..

echo.
echo [6/6] Instalando dependencias do Frontend...
cd frontend
call npm install

cd ..

echo.
echo ============================================
echo    INSTALACAO CONCLUIDA!
echo ============================================
echo.
echo  Execute o arquivo START.bat para iniciar.
echo ============================================
echo.
pause
