@echo off
title Workana Accelerator - Docker Local
color 0A

echo.
echo ====================================================
echo    WORKANA ACCELERATOR - INICIALIZANDO DOCKER
echo ====================================================
echo.

cd /d "%~dp0"

echo [1/3] Verificando se o Docker Engine esta ativo...
docker info >nul 2>&1
if %ERRORLEVEL% neq 0 (
    color 0C
    echo [ERRO] O Docker nao parece estar rodando!
    echo Abra o Docker Desktop e tente novamente.
    echo.
    pause
    exit /b 1
)

echo [2/3] Subindo os containers (Frontend, API, Worker, Caddy)...
docker compose up -d --remove-orphans

if %ERRORLEVEL% neq 0 (
    color 0C
    echo.
    echo [ERRO] Falha ao iniciar os containers do Docker.
    echo Verifique se a porta 80/443 esta disponivel ou configure HTTP_PORT no .env.
    echo.
    pause
    exit /b 1
)

echo.
echo [3/3] Verificando status dos servicos...
docker compose ps

echo.
echo ====================================================
echo    SISTEMA RODANDO COM SUCESSO EM DOCKER!
echo ====================================================
echo.
echo  Aplicacao (SPA + API):  http://localhost
echo  Logs em tempo real:     Execute DOCKER-LOGS.bat
echo  Parar os containers:    Execute DOCKER-STOP.bat
echo.
echo ====================================================
echo.

:: Abrir navegador automaticamente
start http://localhost

echo Pressione qualquer tecla para fechar esta janela...
pause > nul
