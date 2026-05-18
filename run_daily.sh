#!/bin/bash
# run_daily.sh — Briefing giornaliero: fetch RSS ultime 24h + nota in Obsidian
#
# SETUP SU MAC con cron:
#   crontab -e
#   Aggiungi (ogni giorno alle 06:30):
#   30 6 * * * /percorso/completo/logika-automation/run_daily.sh
#
# SETUP SU MAC con launchd (piu affidabile di cron su Mac):
#   Vedi run_daily.plist nella stessa cartella
#
# NOTA: Obsidian deve essere aperto per ricevere le note via API.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/daily_run.log"

echo "[$(date)] Avvio briefing giornaliero" >> "$LOG_FILE"

echo "[1/2] Fetch RSS ultime 24h..."
python3 "$SCRIPT_DIR/ingest.py" --lookback-days 1 >> "$LOG_FILE" 2>&1
if [ $? -ne 0 ]; then
    echo "[$(date)] ERRORE ingest" >> "$LOG_FILE"
    exit 1
fi

sleep 15

echo "[2/2] Generazione briefing giornaliero..."
python3 "$SCRIPT_DIR/digest.py" --daily >> "$LOG_FILE" 2>&1
if [ $? -ne 0 ]; then
    echo "[$(date)] ERRORE digest" >> "$LOG_FILE"
    exit 1
fi

echo "[$(date)] Completato" >> "$LOG_FILE"
