"""
ingest.py — Fetcha RSS e aggiunge nuovi articoli a NotebookLM via Claude

Crea automaticamente un notebook per settimana (es. "AI Weekly — 2026-W21").
Limite NotebookLM: 50 fonti per notebook. Con max_articles_per_feed: 2
e ~25 feed attivi si rimane dentro il limite.

Uso:
  python ingest.py                           # usa feeds.yaml, lookback da config
  python ingest.py --lookback-days 1         # solo articoli delle ultime 24h
  python ingest.py --dry-run                 # mostra cosa aggiungerebbe senza farlo

Richiede:
  pip install feedparser pyyaml python-dateutil
  Claude Code installato e configurato con notebooklm MCP
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import feedparser
import yaml
from dateutil import parser as dateparser

# File locale che tiene traccia degli URL già aggiunti (evita duplicati)
SEEN_FILE = Path(__file__).parent / ".seen_urls.json"


def get_weekly_notebook_name(prefix: str) -> str:
    """Ritorna il nome del notebook per la settimana corrente.
    Es: "AI Weekly — 2026-W21"
    """
    now = datetime.now()
    week = now.strftime("%Y-W%W")
    return f"{prefix} — {week}"


def load_seen_urls() -> set:
    if SEEN_FILE.exists():
        return set(json.loads(SEEN_FILE.read_text()))
    return set()


def save_seen_urls(urls: set):
    SEEN_FILE.write_text(json.dumps(list(urls), indent=2))


def fetch_new_articles(feeds: list, max_per_feed: int, lookback_days: int, seen: set) -> list:
    """Ritorna lista di dict {url, title, source} con articoli nuovi e recenti."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    new_articles = []

    for feed_cfg in feeds:
        url = feed_cfg["url"]
        name = feed_cfg.get("name", url)
        feed_max = feed_cfg.get("max_articles_per_feed", max_per_feed)
        print(f"  Fetching {name}...")

        try:
            feed = feedparser.parse(url)
        except Exception as e:
            print(f"    ERRORE: {e}")
            continue

        count = 0
        for entry in feed.entries:
            if count >= feed_max:
                break

            article_url = entry.get("link", "")
            if not article_url or article_url in seen:
                continue

            # Controlla data pubblicazione
            published = None
            for date_field in ["published_parsed", "updated_parsed"]:
                if hasattr(entry, date_field) and getattr(entry, date_field):
                    t = getattr(entry, date_field)
                    published = datetime(*t[:6], tzinfo=timezone.utc)
                    break

            if published and published < cutoff:
                continue

            new_articles.append({
                "url": article_url,
                "title": entry.get("title", "Senza titolo"),
                "source": name,
            })
            seen.add(article_url)
            count += 1

        print(f"    {count} nuovi articoli trovati")

    return new_articles


def add_to_notebooklm(articles: list, notebook: str, dry_run: bool = False):
    """Usa claude -p per creare il notebook se non esiste e aggiungere gli URL."""
    if not articles:
        print("\nNessun articolo nuovo da aggiungere.")
        return

    titles = [f"- {a['title']} ({a['source']})" for a in articles]
    print(f"\nAggiungo {len(articles)} articoli al notebook '{notebook}':")
    for t in titles:
        print(f"  {t}")

    # Avviso se si rischia di superare il limite
    if len(articles) > 45:
        print(f"\n⚠ ATTENZIONE: {len(articles)} articoli si avvicinano al limite di 50 fonti per notebook.")
        print("  Considera di ridurre max_articles_per_feed o il numero di feed attivi in feeds.yaml.")

    if dry_run:
        print("\n[DRY RUN] Nessuna modifica effettuata.")
        return

    url_list = "\n".join(a["url"] for a in articles)
    prompt = (
        f"Usa il tool list_notebooks per verificare se esiste già un notebook chiamato '{notebook}'.\n"
        f"Se non esiste, crealo su NotebookLM con add_notebook.\n"
        f"Poi aggiungi questi URL come fonti con add_source, uno alla volta.\n"
        f"Se un URL non è raggiungibile o dà errore, saltalo e continua.\n\n"
        f"URL da aggiungere:\n{url_list}"
    )

    print("\nChiamando Claude...")
    result = subprocess.run(
        ["claude", "-p", prompt],
        capture_output=True,
        text=True,
        timeout=300,
    )

    if result.returncode != 0:
        print(f"ERRORE Claude:\n{result.stderr}")
        sys.exit(1)

    print("Fatto.\n")
    if result.stdout.strip():
        print(result.stdout.strip())


def main():
    parser = argparse.ArgumentParser(description="Ingest RSS feeds in NotebookLM")
    parser.add_argument("--config", default=Path(__file__).parent / "feeds.yaml")
    parser.add_argument("--dry-run", action="store_true", help="Mostra cosa farebbe senza eseguire")
    parser.add_argument("--lookback-days", type=int, default=None, help="Override lookback_days da config")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Config non trovata: {config_path}")
        sys.exit(1)

    config = yaml.safe_load(config_path.read_text())

    # Nome notebook con settimana automatica
    prefix = config.get("notebook_prefix", config.get("notebook", "AI Weekly"))
    notebook = get_weekly_notebook_name(prefix)

    max_per_feed = config.get("max_articles_per_feed", 2)
    lookback_days = args.lookback_days if args.lookback_days is not None else config.get("lookback_days", 7)
    feeds = config.get("feeds", [])

    print(f"=== Ingest RSS -> NotebookLM ===")
    print(f"Notebook: '{notebook}'")
    print(f"Feed attivi: {len(feeds)} | Max per feed: {max_per_feed} | Lookback: {lookback_days}gg")
    print(f"Massimo articoli stimato: {len(feeds) * max_per_feed} (limite notebook: 50)\n")

    seen = load_seen_urls()
    print(f"URL già in archivio: {len(seen)}\n")

    print("Fetching feed...")
    new_articles = fetch_new_articles(feeds, max_per_feed, lookback_days, seen)

    add_to_notebooklm(new_articles, notebook, dry_run=args.dry_run)

    if not args.dry_run:
        save_seen_urls(seen)
        print(f"Archivio aggiornato: {len(seen)} URL totali.")


if __name__ == "__main__":
    main()
