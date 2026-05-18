#!/bin/bash
# run_weekly.sh — Script settimanale completo: ingest RSS + genera digest + audio
#
# Come usarlo su Mac/Linux con cron:
#   crontab -e
#   Aggiungi questa riga (ogni lunedì alle 07:00):
#   0 7 * * 1 /path/to/logika-automation/run_weekly.sh
#
# Oppure eseguilo manualmente:
#   chmod +x run_weekly.sh
#   ./run_weekly.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/weekly_run.log"

echo "=======================================" >> "$LOG_FILE"
echo "Avvio: $(date)" >> "$LOG_FILE"
echo "=======================================" >> "$LOG_FILE"

echo "[1/2] Fetching RSS e aggiornamento NotebookLM..."
python3 "$SCRIPT_DIR/ingest.py" >> "$LOG_FILE" 2>&1
if [ $? -ne 0 ]; then
    echo "ERRORE in ingest.py — controlla $LOG_FILE"
    exit 1
fi

# Aspetta 30 secondi che NotebookLM indicizzi le nuove fonti
echo "Attesa indicizzazione NotebookLM (30s)..."
sleep 30

echo "[2/2] Generazione digest settimanale + audio..."
python3 "$SCRIPT_DIR/digest.py" --audio >> "$LOG_FILE" 2>&1
if [ $? -ne 0 ]; then
    echo "ERRORE in digest.py — controlla $LOG_FILE"
    exit 1
fi

echo "Completato: $(date)" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

echo "=== Tutto fatto. Apri Obsidian per vedere il digest. ==="
