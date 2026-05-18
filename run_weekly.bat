@echo off
REM run_weekly.bat — Digest settimanale: fetch RSS 7 giorni + Gemini API + Obsidian
REM Chiamato automaticamente da Task Scheduler ogni lunedi alle 07:00.

SET SCRIPT_DIR=%~dp0
SET LOG_FILE=%SCRIPT_DIR%weekly_run.log

echo [%date% %time%] Avvio digest settimanale >> "%LOG_FILE%"

REM ── Fetch RSS ultimi 7 giorni ────────────────────────────────────────────────
echo [1/2] Fetch RSS 7 giorni...
python "%SCRIPT_DIR%ingest.py" >> "%LOG_FILE%" 2>&1
if %ERRORLEVEL% neq 0 (
    echo [%date% %time%] ERRORE ingest >> "%LOG_FILE%"
    exit /b 1
)

REM ── Genera digest con Gemini ─────────────────────────────────────────────────
echo [2/2] Generazione digest settimanale...
python "%SCRIPT_DIR%digest.py" >> "%LOG_FILE%" 2>&1
if %ERRORLEVEL% neq 0 (
    echo [%date% %time%] ERRORE digest >> "%LOG_FILE%"
    exit /b 1
)

echo [%date% %time%] Completato >> "%LOG_FILE%"
