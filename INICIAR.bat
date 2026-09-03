@echo off
title Workana Accelerator - Painel de Controle
color 0B

cd /d "%~dp0"

:: Suporte a argumentos de linha de comando: INICIAR.bat [start|stop|logs|login|duckdns|hosts|dev]
if /i "%1"=="start" goto opt_docker_start
if /i "%1"=="stop" goto opt_docker_stop
if /i "%1"=="logs" goto opt_docker_logs
if /i "%1"=="login" goto opt_workana_login
if /i "%1"=="duckdns" goto opt_duckdns
if /i "%1"=="hosts" goto opt_hosts
if /i "%1"=="dev" goto opt_local_start

:menu
cls
echo.
echo =======================================================
echo              WORKANA ACCELERATOR - PAINEL
echo =======================================================
echo.
echo   [1] Iniciar Sistema (Docker - Recomendado)
echo   [2] Parar Sistema
echo   [3] Ver Logs em Tempo Real
echo   [4] Login no Workana (Exportar Sessao/Cookies)
echo   [5] Atualizar IP no Duck DNS
echo   [6] Corrigir Acesso Local ao Dominio (Hosts)
echo   [7] Iniciar Sem Docker (Modo Dev: Python + Vite)
echo   [0] Sair
echo.
echo =======================================================
set /p opt="Escolha uma opcao [0-7]: "

if "%opt%"=="1" goto opt_docker_start
if "%opt%"=="2" goto opt_docker_stop
if "%opt%"=="3" goto opt_docker_logs
if "%opt%"=="4" goto opt_workana_login
if "%opt%"=="5" goto opt_duckdns
if "%opt%"=="6" goto opt_hosts
if "%opt%"=="7" goto opt_local_start
if "%opt%"=="0" exit /b
echo Opcao invalida!
timeout /t 2 >nul
goto menu

:opt_docker_start
cls
color 0A
echo.
echo =======================================================
echo    INICIALIZANDO WORKANA ACCELERATOR (DOCKER)
echo =======================================================
echo.
echo [1/3] Verificando Docker Engine...
docker info >nul 2>&1
if %ERRORLEVEL% neq 0 (
    color 0C
    echo [ERRO] O Docker nao parece estar rodando! Abra o Docker Desktop.
    echo.
    pause
    goto menu
)

echo [2/3] Subindo os containers (Frontend, API, Worker, Caddy)...
docker compose up -d --build --remove-orphans
if %ERRORLEVEL% neq 0 (
    color 0C
    echo [ERRO] Falha ao iniciar containers do Docker.
    echo.
    pause
    goto menu
)

set "APP_URL=localhost"
if exist ".env" (
    for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
        if "%%A"=="APP_DOMAIN" set "APP_URL=%%B"
    )
)

echo.
echo [3/3] Servicos iniciados com sucesso!
docker compose ps
echo.
echo =======================================================
echo   SISTEMA NO AR: http://%APP_URL% (ou http://localhost)
echo =======================================================
start http://%APP_URL%
echo.
pause
goto menu

:opt_docker_stop
cls
color 0E
echo.
echo =======================================================
echo    PARANDO SERVICOS DOCKER
echo =======================================================
echo.
docker compose down
echo.
echo [OK] Todos os servicos foram encerrados.
echo.
pause
goto menu

:opt_docker_logs
cls
color 0F
echo =======================================================
echo    LOGS EM TEMPO REAL (Pressione Ctrl+C para voltar)
echo =======================================================
echo.
docker compose logs -f --tail=100
pause
goto menu

:opt_workana_login
cls
color 0B
echo.
echo =======================================================
echo    LOGIN WORKANA / EXPORTAR SESSAO
echo =======================================================
echo.
set "PY_EXE=python"
if exist "backend\venv\Scripts\python.exe" set "PY_EXE=backend\venv\Scripts\python.exe"
"%PY_EXE%" backend\scripts\export_workana_session.py
echo.
pause
goto menu

:opt_duckdns
cls
color 0B
echo.
echo =======================================================
echo    ATUALIZANDO IP NO DUCK DNS
echo =======================================================
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\update-duckdns.ps1"
echo.
pause
goto menu

:opt_hosts
cls
color 0A
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Solicitando permissoes de Administrador...
    powershell -Command "Start-Process '%~f0' -ArgumentList 'hosts' -Verb RunAs"
    exit /b
)
echo.
echo =======================================================
echo    CONFIGURANDO REDE, FIREWALL E CERTIFICADO SSL
echo =======================================================
echo.
echo [1/4] Instalando Certificado SSL Raiz no Windows...
if exist "%~dp0caddy-root-ca.crt" (
    certutil -addstore -f "ROOT" "%~dp0caddy-root-ca.crt" >nul 2>&1
    echo [SUCESSO] Certificado SSL instalado como Confiavel no Windows!
) else (
    echo [ALERTA] Arquivo caddy-root-ca.crt nao encontrado na raiz.
)

echo.
echo [2/4] Configurando arquivo hosts para acesso local...
findstr /i "workana.duckdns.org" "C:\Windows\System32\drivers\etc\hosts" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] O dominio workana.duckdns.org ja esta no hosts.
) else (
    echo 127.0.0.1 workana.duckdns.org>>"C:\Windows\System32\drivers\etc\hosts"
    echo [SUCESSO] workana.duckdns.org adicionado ao hosts com sucesso!
)

echo.
echo [3/4] Liberando portas 80 e 443 no Firewall do Windows...
netsh advfirewall firewall delete rule name="Workana-Web-80" >nul 2>&1
netsh advfirewall firewall add rule name="Workana-Web-80" dir=in action=allow protocol=TCP localport=80 >nul 2>&1
netsh advfirewall firewall delete rule name="Workana-SSL-443" >nul 2>&1
netsh advfirewall firewall add rule name="Workana-SSL-443" dir=in action=allow protocol=TCP localport=443 >nul 2>&1
echo [OK] Portas 80 e 443 liberadas no Firewall do Windows!

echo.
echo [4/4] Limpando cache DNS...
ipconfig /flushdns >nul
echo [OK] Cache DNS limpo!
echo.
echo =======================================================
echo  TUDO CONFIGURADO E CONFIADO!
echo  Abra no seu navegador: https://workana.duckdns.org
echo  (ou http://workana.duckdns.org)
echo =======================================================
echo.
pause
goto menu

:opt_local_start
cls
color 0A
echo.
echo =======================================================
echo    INICIANDO MODO DEV LOCAL (SEM DOCKER)
echo =======================================================
echo.
set "PY_EXE=python"
if exist "backend\venv\Scripts\python.exe" set "PY_EXE=backend\venv\Scripts\python.exe"

start "Workana API" cmd /k "cd /d %~dp0backend && %PY_EXE% -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
start "Workana Worker" cmd /k "cd /d %~dp0backend && %PY_EXE% run_worker.py"
start "Workana Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo [OK] Servidores iniciados em janelas separadas!
echo   - Backend:  http://localhost:8000/docs
echo   - Frontend: http://localhost:5173
echo.
pause
goto menu
