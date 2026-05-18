@echo off
REM run_daily.bat — Briefing giornaliero: fetch RSS + Gemini API + Obsidian
REM Chiamato automaticamente da Task Scheduler ogni mattina alle 06:30.

SET SCRIPT_DIR=%~dp0
SET LOG_FILE=%SCRIPT_DIR%daily_run.log

echo [%date% %time%] Avvio briefing giornaliero >> "%LOG_FILE%"

REM ── Fetch RSS ultime 24h ──────────────────────────────────────────────────────
echo [1/2] Fetch RSS...
python "%SCRIPT_DIR%ingest.py" --lookback-days 1 >> "%LOG_FILE%" 2>&1
if %ERRORLEVEL% neq 0 (
    echo [%date% %time%] ERRORE ingest >> "%LOG_FILE%"
    exit /b 1
)

REM ── Genera briefing con Gemini ────────────────────────────────────────────────
echo [2/2] Generazione briefing...
python "%SCRIPT_DIR%digest.py" --daily >> "%LOG_FILE%" 2>&1
if %ERRORLEVEL% neq 0 (
    echo [%date% %time%] ERRORE digest >> "%LOG_FILE%"
    exit /b 1
)

echo [%date% %time%] Completato >> "%LOG_FILE%"
