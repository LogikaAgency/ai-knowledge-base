# setup_windows.ps1 — Configura i task automatici su Windows Task Scheduler
#
# COME USARLO (una volta sola):
#   1. Apri PowerShell come Amministratore
#   2. Esegui: powershell -ExecutionPolicy Bypass -File "percorso\setup_windows.ps1"
#
# Crea due task:
#   - "Logika AI Briefing Giornaliero" → ogni giorno alle 06:30
#   - "Logika AI Digest Settimanale"   → ogni lunedi alle 07:00
#
# Entrambi partono appena il PC si accende se l'orario e gia passato.

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$DailyBat  = Join-Path $ScriptDir "run_daily.bat"
$WeeklyBat = Join-Path $ScriptDir "run_weekly.bat"

# Verifica che i file esistano
if (-not (Test-Path $DailyBat)) {
    Write-Error "run_daily.bat non trovato in $ScriptDir"
    exit 1
}
if (-not (Test-Path $WeeklyBat)) {
    Write-Error "run_weekly.bat non trovato in $ScriptDir"
    exit 1
}

Write-Host ""
Write-Host "=== Setup Logika AI Automation ===" -ForegroundColor Cyan
Write-Host "Cartella script: $ScriptDir"
Write-Host ""

# ── TASK GIORNALIERO ──────────────────────────────────────────────────────────

$dailyAction = New-ScheduledTaskAction `
    -Execute "cmd.exe" `
    -Argument "/c `"$DailyBat`""

$dailyTrigger = New-ScheduledTaskTrigger `
    -Daily `
    -At "06:30"

$dailySettings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30) `
    -MultipleInstances IgnoreNew `
    -WakeToRun $false

# Rimuovi se esiste gia
Unregister-ScheduledTask -TaskName "Logika AI Briefing Giornaliero" -Confirm:$false -ErrorAction SilentlyContinue

Register-ScheduledTask `
    -TaskName "Logika AI Briefing Giornaliero" `
    -Description "Fetch RSS ultime 24h + briefing giornaliero in Obsidian" `
    -Action $dailyAction `
    -Trigger $dailyTrigger `
    -Settings $dailySettings `
    -RunLevel Highest `
    -Force | Out-Null

Write-Host "[OK] Task giornaliero creato — ogni giorno alle 06:30" -ForegroundColor Green
Write-Host "     Se il PC era spento, parte appena si accende."

# ── TASK SETTIMANALE ──────────────────────────────────────────────────────────

$weeklyAction = New-ScheduledTaskAction `
    -Execute "cmd.exe" `
    -Argument "/c `"$WeeklyBat`""

$weeklyTrigger = New-ScheduledTaskTrigger `
    -Weekly `
    -DaysOfWeek Monday `
    -At "07:00"

$weeklySettings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
    -MultipleInstances IgnoreNew `
    -WakeToRun $false

Unregister-ScheduledTask -TaskName "Logika AI Digest Settimanale" -Confirm:$false -ErrorAction SilentlyContinue

Register-ScheduledTask `
    -TaskName "Logika AI Digest Settimanale" `
    -Description "Digest settimanale + audio briefing in Obsidian (ogni lunedi)" `
    -Action $weeklyAction `
    -Trigger $weeklyTrigger `
    -Settings $weeklySettings `
    -RunLevel Highest `
    -Force | Out-Null

Write-Host "[OK] Task settimanale creato — ogni lunedi alle 07:00" -ForegroundColor Green
Write-Host "     Se il PC era spento, parte appena si accende."

# ── RIEPILOGO ─────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "=== Riepilogo task creati ===" -ForegroundColor Cyan
Get-ScheduledTask | Where-Object { $_.TaskName -like "Logika AI*" } | ForEach-Object {
    $info = $_ | Get-ScheduledTaskInfo
    Write-Host ("  {0,-40} Prossima esecuzione: {1}" -f $_.TaskName, $info.NextRunTime)
}

Write-Host ""
Write-Host "IMPORTANTE: Obsidian deve essere aperto per ricevere le note." -ForegroundColor Yellow
Write-Host "Aggiungilo all'avvio di Windows se vuoi che parta in automatico:"
Write-Host "  Win+R → shell:startup → crea collegamento a Obsidian.exe"
Write-Host ""
Write-Host "Per testare subito il briefing giornaliero:" -ForegroundColor Cyan
Write-Host "  Start-ScheduledTask -TaskName 'Logika AI Briefing Giornaliero'"
Write-Host ""
