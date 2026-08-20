@echo off
title Workana Accelerator - Parando Docker
color 0E

echo.
echo ====================================================
echo    WORKANA ACCELERATOR - PARANDO CONTAINERS
echo ====================================================
echo.

cd /d "%~dp0"
docker compose down

echo.
echo ====================================================
echo    CONTAINERS PARADOS COM SUCESSO!
echo ====================================================
echo.
pause
