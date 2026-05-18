"""
digest.py — Genera briefing da articles_cache.json usando Gemini API
e salva direttamente in Obsidian.

Uso:
  python digest.py --daily       # briefing giornaliero (3 punti, ultimi 2 giorni)
  python digest.py               # digest settimanale (5 sezioni, ultimi 7 giorni)
  python digest.py --topic "agents"  # query su un tema specifico

Richiede:
  pip install google-generativeai pyyaml
  GEMINI_API_KEY in feeds.yaml o come variabile d'ambiente
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import yaml

CACHE_FILE = Path(__file__).parent / "articles_cache.json"
CONFIG_FILE = Path(__file__).parent / "feeds.yaml"


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        print(f"Config non trovata: {CONFIG_FILE}")
        sys.exit(1)
    return yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8"))


def load_articles(lookback_days: int) -> list:
    """Carica articoli dalla cache filtrati per data."""
    if not CACHE_FILE.exists():
        return []
    articles = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)

    filtered = []
    for a in articles:
        try:
            added = datetime.fromisoformat(a.get("added_at", "2000-01-01T00:00:00+00:00"))
            if added.tzinfo is None:
                added = added.replace(tzinfo=timezone.utc)
            if added >= cutoff:
                filtered.append(a)
        except Exception:
            filtered.append(a)

    return filtered


def format_articles_for_prompt(articles: list) -> str:
    lines = []
    for a in articles:
        lines.append(f"**{a['title']}** — {a['source']}")
        if a.get("description"):
            lines.append(a["description"][:400])
        lines.append(f"URL: {a['url']}")
        lines.append("")
    return "\n".join(lines)


def build_daily_prompt(articles: list) -> str:
    articles_text = format_articles_for_prompt(articles)
    today = datetime.now().strftime("%Y-%m-%d")
    return f"""Sei un assistente editoriale che crea briefing sull'AI per professionisti italiani.

Ecco gli articoli recenti raccolti dai principali feed sull'intelligenza artificiale:

{articles_text}

---

Crea un briefing giornaliero conciso con esattamente **3 punti chiave**.

Regole:
- Seleziona solo le notizie piu rilevanti e interessanti
- Ogni punto: titolo breve in grassetto + 2-3 righe di spiegazione
- Indica sempre la fonte tra parentesi
- Scrivi in italiano, tono diretto e professionale — niente hype inutile
- Aggiungi il link originale per ogni punto

Formato output (Markdown):

# Briefing AI — {today}

## 1. [Titolo punto]
[Spiegazione 2-3 righe]
*(Fonte: NomeFonte)* | [Leggi](<URL>)

## 2. [Titolo punto]
...

## 3. [Titolo punto]
...

---
*Generato da {len(articles)} articoli — {today}*
"""


def build_weekly_prompt(articles: list) -> str:
    articles_text = format_articles_for_prompt(articles)
    week = datetime.now().strftime("%Y-W%W")
    today = datetime.now().strftime("%Y-%m-%d")
    return f"""Sei un assistente editoriale che crea digest settimanali sull'AI per professionisti italiani.

Ecco tutti gli articoli della settimana raccolti dai principali feed sull'intelligenza artificiale:

{articles_text}

---

Crea un digest settimanale strutturato in **5 sezioni tematiche**.

Regole:
- Raggruppa le notizie per tema (es: Nuovi Modelli, Tool e Framework, Ricerca, Business AI, Community)
- Ogni sezione: 2-4 notizie sintetizzate in 1-2 righe ciascuna con fonte e link
- Scrivi in italiano, tono diretto e professionale
- Alla fine: sezione "Takeaway della settimana" con 2-3 insight chiave

Formato output (Markdown):

# Digest AI — {week}

## [Tema 1]
- **[Titolo]**: [Sintesi]. *(Fonte)* | [Link](<URL>)

## [Tema 2]
...

---
## Takeaway della settimana
- ...

---
*Generato da {len(articles)} articoli — {today}*
"""


def build_topic_prompt(articles: list, topic: str) -> str:
    articles_text = format_articles_for_prompt(articles)
    today = datetime.now().strftime("%Y-%m-%d")
    return f"""Sei un assistente di ricerca sull'AI.

Ecco gli articoli recenti raccolti dai principali feed sull'intelligenza artificiale:

{articles_text}

---

Analizza gli articoli e rispondi a questa domanda:
**"{topic}"**

- Usa solo le informazioni presenti negli articoli forniti
- Cita le fonti per ogni affermazione con link
- Scrivi in italiano, tono diretto e professionale
- Se non ci sono informazioni rilevanti, dillo chiaramente

Formato: Markdown con titolo, sezioni tematiche e citazioni.
"""


def call_gemini(prompt: str, api_key: str, model: str = "gemini-2.0-flash") -> str:
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    client = genai.GenerativeModel(model)
    response = client.generate_content(prompt)
    return response.text


def write_to_obsidian(content: str, title: str, vault_path: str, folder: str = "AI Digest") -> str:
    vault = Path(vault_path)
    if not vault.exists():
        print(f"ERRORE: vault Obsidian non trovato: {vault_path}")
        print("Controlla 'obsidian_vault' in feeds.yaml")
        sys.exit(1)

    digest_folder = vault / folder
    digest_folder.mkdir(exist_ok=True)

    safe_title = title.replace(":", "-").replace("/", "-").replace("\\", "-")
    note_path = digest_folder / f"{safe_title}.md"
    note_path.write_text(content, encoding="utf-8")
    return str(note_path)


def main():
    parser = argparse.ArgumentParser(description="Genera briefing AI con Gemini API")
    parser.add_argument("--daily", action="store_true", help="Briefing giornaliero (3 punti)")
    parser.add_argument("--topic", type=str, help="Query su un tema specifico")
    parser.add_argument("--lookback-days", type=int, default=None)
    parser.add_argument("--model", default=None, help="Modello Gemini (default: gemini-2.0-flash)")
    args = parser.parse_args()

    config = load_config()

    # API key: env var ha priorita su feeds.yaml
    api_key = os.environ.get("GEMINI_API_KEY") or config.get("gemini_api_key", "")
    if not api_key:
        print("ERRORE: GEMINI_API_KEY non configurata.")
        print("  Aggiungila a feeds.yaml: gemini_api_key: AIza...")
        print("  oppure: set GEMINI_API_KEY=AIza...")
        sys.exit(1)

    vault_path = config.get("obsidian_vault", "")
    model = args.model or config.get("gemini_model", "gemini-2.0-flash")

    if args.lookback_days is not None:
        lookback = args.lookback_days
    elif args.daily:
        lookback = 2
    else:
        lookback = config.get("lookback_days", 7)

    articles = load_articles(lookback)
    if not articles:
        print("Nessun articolo in cache. Esegui prima: python ingest.py")
        sys.exit(1)

    print(f"=== Digest AI ===")
    print(f"Articoli (ultimi {lookback}gg): {len(articles)} | Modello: {model}\n")

    if args.topic:
        mode = f"query: {args.topic}"
        title = f"Query — {args.topic[:40]} — {datetime.now().strftime('%Y-%m-%d')}"
        prompt = build_topic_prompt(articles, args.topic)
    elif args.daily:
        mode = "briefing giornaliero"
        title = f"Briefing — {datetime.now().strftime('%Y-%m-%d')}"
        prompt = build_daily_prompt(articles)
    else:
        mode = "digest settimanale"
        title = f"Digest — {datetime.now().strftime('%Y-W%W')}"
        prompt = build_weekly_prompt(articles)

    print(f"Generando {mode}...")
    try:
        content = call_gemini(prompt, api_key, model)
    except Exception as e:
        print(f"ERRORE Gemini API: {e}")
        sys.exit(1)

    if vault_path:
        path = write_to_obsidian(content, title, vault_path)
        print(f"Salvato in Obsidian: {path}")
    else:
        print(content)
        print("\n(Aggiungi 'obsidian_vault' in feeds.yaml per salvare in Obsidian)")


if __name__ == "__main__":
    main()
