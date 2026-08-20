@echo off
title Workana Accelerator - Logs Docker
color 0B

echo.
echo ====================================================
echo    WORKANA ACCELERATOR - LOGS EM TEMPO REAL
echo ====================================================
echo.

cd /d "%~dp0"
docker compose logs -f
