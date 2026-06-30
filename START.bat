@echo off
title Workana Accelerator - Iniciando...
color 0A

echo.
echo ============================================
echo    WORKANA ACCELERATOR - INICIANDO
echo ============================================
echo.

cd /d "%~dp0"

echo [0/2] Limpando processos anteriores (Portas 8000 e 8080)...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8080" ^| find "LISTENING"') do taskkill /f /pid %%a >nul 2>&1

echo [1/3] Iniciando Backend (FastAPI)...
start "Workana Backend" cmd /k "cd backend && python run.py"

timeout /t 2 /nobreak > nul

echo [2/3] Iniciando Worker de Automação...
start "Workana Worker" cmd /k "cd backend && python run_worker.py"

timeout /t 2 /nobreak > nul

echo [3/3] Iniciando Frontend (Vite)...
start "Workana Frontend" cmd /k "cd frontend && npm run dev"

timeout /t 5 /nobreak > nul

echo.
echo ============================================
echo    SISTEMA INICIADO COM SUCESSO!
echo ============================================
echo.
echo  Frontend:  http://localhost:8080
echo  API:       http://localhost:8000
echo  Swagger:   http://localhost:8000/docs (Apenas em DEBUG=true)
echo.
echo  Feche as janelas CMD para parar.
echo ============================================
echo.

:: Abrir navegador automaticamente
start http://localhost:8080

echo Pressione qualquer tecla para fechar esta janela...
pause > nul
