"""
digest.py — Genera briefing giornaliero o digest settimanale da NotebookLM → Obsidian

Uso:
  python digest.py                   # digest settimanale (5 punti)
  python digest.py --daily           # briefing giornaliero (3 punti, veloce)
  python digest.py --audio           # genera anche l'audio (solo settimanale)
  python digest.py --topic "agenti"  # focus su un tema specifico

Richiede:
  Claude Code installato e configurato con notebooklm MCP e obsidian MCP
"""

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_claude(prompt: str, label: str, timeout: int = 300) -> str:
    """Esegue un prompt Claude in modalità headless e ritorna l'output."""
    print(f"\n→ {label}...")
    result = subprocess.run(
        ["claude", "-p", prompt],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        print(f"ERRORE:\n{result.stderr}")
        sys.exit(1)
    return result.stdout.strip()


def generate_daily_briefing(notebook: str, obsidian_folder: str, topic: str | None):
    """Briefing giornaliero: 3 punti, veloce, niente audio."""
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    giorno = now.strftime("%A %d %B %Y")  # es. "Lunedi 18 Maggio 2026"
    topic_str = f" con focus su '{topic}'" if topic else ""
    note_title = f"Briefing — {today}"

    prompt = f"""Usa NotebookLM per generare il briefing giornaliero di oggi{topic_str}.

Passi da seguire:
1. Seleziona il notebook '{notebook}'
2. Chiedi: "Cosa c'e di nuovo e rilevante nelle ultime 24 ore? Dammi i 3 punti piu importanti con fonte."
3. Crea una nota in Obsidian nella cartella '{obsidian_folder}' con questo formato:

## Briefing — {giorno}

> [una frase che riassume il tono della giornata: attiva, calma, ricca di annunci, ecc.]

**1. [titolo]**
[2 righe di spiegazione]
Fonte: [nome fonte]

**2. [titolo]**
[2 righe]
Fonte: [nome fonte]

**3. [titolo]**
[2 righe]
Fonte: [nome fonte]

---
*Generato automaticamente — {today}*

Se non ci sono novita rilevanti nelle ultime 24 ore, scrivi comunque la nota con i punti piu recenti disponibili nel notebook.
"""
    run_claude(prompt, f"Briefing giornaliero '{note_title}'", timeout=180)
    print(f"✓ Nota salvata in Obsidian: {obsidian_folder}/{note_title}")
    return note_title


def generate_weekly_digest(notebook: str, obsidian_folder: str, topic: str | None):
    """Digest settimanale: 5 punti, piu dettagliato."""
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    week = now.strftime("settimana del %d %B %Y")
    topic_str = f" con focus su '{topic}'" if topic else ""
    note_title = f"Digest — {week}"
    if topic:
        note_title += f" — {topic}"

    prompt = f"""Usa NotebookLM per generare il digest settimanale{topic_str}.

Passi da seguire:
1. Seleziona il notebook '{notebook}'
2. Chiedi: "Quali sono i 5 sviluppi o notizie piu importanti di questa settimana? Per ognuno dai una spiegazione di 2-3 righe e cita la fonte."
3. Crea una nota in Obsidian nella cartella '{obsidian_folder}' con questo formato:

## {note_title}

[intro di 2 righe che riassume il tema della settimana]

### 1. [titolo sviluppo]
[spiegazione 2-3 righe]
Fonte: [nome fonte]

### 2. [titolo sviluppo]
[spiegazione 2-3 righe]
Fonte: [nome fonte]

### 3. [titolo sviluppo]
[spiegazione 2-3 righe]
Fonte: [nome fonte]

### 4. [titolo sviluppo]
[spiegazione 2-3 righe]
Fonte: [nome fonte]

### 5. [titolo sviluppo]
[spiegazione 2-3 righe]
Fonte: [nome fonte]

---
*Generato automaticamente da NotebookLM + Claude — {today}*
"""
    run_claude(prompt, f"Digest settimanale '{note_title}'")
    print(f"✓ Nota salvata in Obsidian: {obsidian_folder}/{note_title}")
    return note_title


def generate_audio(notebook: str, note_title: str, obsidian_folder: str):
    prompt = f"""Usa NotebookLM per generare un audio briefing dal notebook '{notebook}'.
Deve essere un riassunto parlato degli sviluppi piu importanti della settimana, durata 3-4 minuti.
Dopo che l'audio e stato generato, aggiungi il link all'audio in fondo alla nota '{note_title}'
in Obsidian nella cartella '{obsidian_folder}', in una sezione chiamata '## Audio briefing'."""

    run_claude(prompt, "Generazione audio briefing", timeout=600)
    print("✓ Audio generato e link salvato nella nota")


def main():
    parser = argparse.ArgumentParser(description="Genera briefing giornaliero o digest settimanale")
    parser.add_argument("--notebook", default="AI Weekly", help="Nome del notebook in NotebookLM")
    parser.add_argument("--folder", default="Digest", help="Cartella Obsidian dove salvare")
    parser.add_argument("--daily", action="store_true", help="Modalita giornaliera (3 punti, veloce)")
    parser.add_argument("--audio", action="store_true", help="Genera anche l'audio (solo settimanale)")
    parser.add_argument("--topic", default=None, help="Focus su un tema specifico")
    args = parser.parse_args()

    mode = "giornaliero" if args.daily else "settimanale"
    print(f"=== Digest {mode} — {datetime.now().strftime('%d %B %Y')} ===")
    print(f"Notebook: '{args.notebook}' | Cartella Obsidian: '{args.folder}'")

    if args.daily:
        generate_daily_briefing(args.notebook, args.folder, args.topic)
    else:
        note_title = generate_weekly_digest(args.notebook, args.folder, args.topic)
        if args.audio:
            generate_audio(args.notebook, note_title, args.folder)

    print("\n=== Completato ===")


if __name__ == "__main__":
    main()
