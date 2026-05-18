@echo off
REM run_daily.bat — Briefing giornaliero: fetch RSS ultime 24h + nota in Obsidian
REM
REM Non eseguire manualmente — viene chiamato da Task Scheduler.
REM Per configurare il Task Scheduler esegui setup_windows.ps1 una volta sola.

SET SCRIPT_DIR=%~dp0
SET LOG_FILE=%SCRIPT_DIR%daily_run.log

echo [%date% %time%] Avvio briefing giornaliero >> "%LOG_FILE%"

REM ── Avvia Obsidian se non e aperto ──────────────────────────────────────────
tasklist /FI "IMAGENAME eq Obsidian.exe" 2>NUL | find /I "Obsidian.exe" >NUL
if %ERRORLEVEL% neq 0 (
    echo [%date% %time%] Avvio Obsidian... >> "%LOG_FILE%"
    start "" "%LOCALAPPDATA%\Obsidian\Obsidian.exe"
    REM Aspetta 8 secondi che Obsidian carichi il vault e il plugin REST API
    timeout /t 8 /nobreak > nul
) else (
    echo [%date% %time%] Obsidian gia aperto >> "%LOG_FILE%"
)

REM ── Fetch RSS ultime 24h ─────────────────────────────────────────────────────
echo [1/2] Fetch RSS ultime 24h...
python "%SCRIPT_DIR%ingest.py" --lookback-days 1 >> "%LOG_FILE%" 2>&1
if %ERRORLEVEL% neq 0 (
    echo [%date% %time%] ERRORE ingest >> "%LOG_FILE%"
    exit /b 1
)

timeout /t 15 /nobreak > nul

REM ── Genera briefing ──────────────────────────────────────────────────────────
echo [2/2] Generazione briefing giornaliero...
python "%SCRIPT_DIR%digest.py" --daily >> "%LOG_FILE%" 2>&1
if %ERRORLEVEL% neq 0 (
    echo [%date% %time%] ERRORE digest >> "%LOG_FILE%"
    exit /b 1
)

echo [%date% %time%] Completato >> "%LOG_FILE%"
