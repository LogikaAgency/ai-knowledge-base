@echo off
REM run_weekly.bat — Digest settimanale: fetch RSS 7 giorni + digest completo + audio
REM
REM Non eseguire manualmente — viene chiamato da Task Scheduler.
REM Per configurare il Task Scheduler esegui setup_windows.ps1 una volta sola.

SET SCRIPT_DIR=%~dp0
SET LOG_FILE=%SCRIPT_DIR%weekly_run.log

echo [%date% %time%] Avvio digest settimanale >> "%LOG_FILE%"

REM ── Avvia Obsidian se non e aperto ──────────────────────────────────────────
tasklist /FI "IMAGENAME eq Obsidian.exe" 2>NUL | find /I "Obsidian.exe" >NUL
if %ERRORLEVEL% neq 0 (
    echo [%date% %time%] Avvio Obsidian... >> "%LOG_FILE%"
    start "" "%LOCALAPPDATA%\Obsidian\Obsidian.exe"
    timeout /t 8 /nobreak > nul
) else (
    echo [%date% %time%] Obsidian gia aperto >> "%LOG_FILE%"
)

REM ── Fetch RSS ultimi 7 giorni ────────────────────────────────────────────────
echo [1/2] Fetch RSS ultimi 7 giorni...
python "%SCRIPT_DIR%ingest.py" >> "%LOG_FILE%" 2>&1
if %ERRORLEVEL% neq 0 (
    echo [%date% %time%] ERRORE ingest >> "%LOG_FILE%"
    exit /b 1
)

REM Attesa piu lunga per il settimanale: NotebookLM deve indicizzare tutto
timeout /t 30 /nobreak > nul

REM ── Genera digest + audio ────────────────────────────────────────────────────
echo [2/2] Generazione digest settimanale + audio...
python "%SCRIPT_DIR%digest.py" --audio >> "%LOG_FILE%" 2>&1
if %ERRORLEVEL% neq 0 (
    echo [%date% %time%] ERRORE digest >> "%LOG_FILE%"
    exit /b 1
)

echo [%date% %time%] Completato >> "%LOG_FILE%"
