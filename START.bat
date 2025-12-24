@echo off
title Workana Automation - Iniciando...
color 0A

echo.
echo ============================================
echo    WORKANA AUTOMATION - INICIANDO
echo ============================================
echo.

cd /d "%~dp0"

echo [0/2] Limpando processos anteriores (Porta 8000)...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do taskkill /f /pid %%a >nul 2>&1

echo [1/2] Iniciando Backend (FastAPI)...
start "Workana Backend" cmd /k "cd backend && .\venv\Scripts\activate && python run.py"

timeout /t 3 /nobreak > nul

echo [2/2] Iniciando Frontend (Next.js)...
start "Workana Frontend" cmd /k "cd frontend && npm run dev"

timeout /t 5 /nobreak > nul

echo.
echo ============================================
echo    SISTEMA INICIADO COM SUCESSO!
echo ============================================
echo.
echo  Frontend:  http://localhost:3000
echo  API:       http://localhost:8000
echo  Swagger:   http://localhost:8000/docs
echo.
echo  Feche as janelas CMD para parar.
echo ============================================
echo.

:: Abrir navegador automaticamente
start http://localhost:3000

echo Pressione qualquer tecla para fechar esta janela...
pause > nul
