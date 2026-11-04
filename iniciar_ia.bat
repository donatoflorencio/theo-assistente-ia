@echo off
title Minha IA Local

cd /d C:\IA_LOCAL

call ambiente\Scripts\activate.bat

echo Inicializando sua IA...

start "" /B python app.py

:AGUARDAR
timeout /t 2 /nobreak >nul

powershell -NoProfile -Command "try { $r = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:5000' -TimeoutSec 2; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }"

if errorlevel 1 goto AGUARDAR

start "" http://127.0.0.1:5000

echo IA pronta!
pause

