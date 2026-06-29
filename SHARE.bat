@echo off
title Workana Accelerator - Compartilhar Mobile
color 0B

echo.
echo ============================================
echo   COMPARTILHAR COM CELULAR
echo ============================================
echo.
echo Este script vai gerar um link publico para voce acessar
echo o app pelo celular (sem precisar de IP).
echo.
echo [1/3] Verificando conexao...
timeout /t 2 /nobreak > nul

echo [2/3] Tentando liberar porta 8080 no Firewall (pode pedir permissao)...
netsh advfirewall firewall add rule name="Workana 8080" dir=in action=allow protocol=TCP localport=8080 >nul 2>&1

echo [3/3] Iniciando Tunel...
echo.
echo --------------------------------------------------------
echo  INSTRUCOES:
echo  1. Aguarde aparecer o link abaixo (ex: https://xxx.loca.lt)
echo  2. Abra esse link no celular
echo  3. Se pedir senha/IP, eh o IP do seu computador ou clique "Continue"
echo --------------------------------------------------------
echo.

cd frontend
call npx -y localtunnel --port 8080

echo.
echo Tunel fechado.
pause
