@echo off
title AgentColony
cd /d "%~dp0"
echo ============================================================
echo    AgentColony - avvio in corso...
echo    Lascia questa finestra APERTA mentre lo usi.
echo    Il browser si aprira' da solo tra pochi secondi.
echo ============================================================
echo.

REM --- trova Python (python oppure py) ---
set PYCMD=python
where python >nul 2>nul
if errorlevel 1 set PYCMD=py
where %PYCMD% >nul 2>nul
if errorlevel 1 (
  echo [X] Python non trovato.
  echo     Installalo da https://python.org e spunta "Add Python to PATH", poi riprova.
  echo.
  pause
  exit /b
)

REM --- installa ccxt per i prezzi reali (se manca); la demo funziona comunque ---
%PYCMD% -m pip install --quiet --disable-pip-version-check ccxt >nul 2>nul

REM --- avvia il sito e apre il browser da solo ---
%PYCMD% server.py --open

echo.
echo Il programma si e' chiuso. Premi un tasto per uscire.
pause >nul
