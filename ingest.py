"""
ingest.py — Fetcha RSS e salva articoli in articles_cache.json

Non richiede Claude, MCP, o browser. Solo Python puro.
Esegui questo script ogni giorno — salva gli articoli nuovi in cache
per digest.py che li processerà con Gemini API.

Uso:
  python ingest.py                     # usa feeds.yaml, lookback da config
  python ingest.py --lookback-days 1   # solo articoli delle ultime 24h
  python ingest.py --dry-run           # mostra cosa fetcherebbe senza salvare

Richiede:
  pip install feedparser pyyaml python-dateutil
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import feedparser
import yaml
from dateutil import parser as dateparser

CACHE_FILE = Path(__file__).parent / "articles_cache.json"


def strip_html(text: str) -> str:
    """Rimuove tag HTML e normalizza spazi."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def load_cache() -> list:
    if CACHE_FILE.exists():
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    return []


def save_cache(articles: list):
    # Mantieni al massimo 500 articoli — evita che il file cresca all'infinito
    articles = articles[:500]
    CACHE_FILE.write_text(
        json.dumps(articles, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def fetch_new_articles(feeds: list, max_per_feed: int, lookback_days: int, seen_urls: set) -> list:
    """Fetcha i feed RSS e ritorna articoli nuovi con metadati completi."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    new_articles = []

    for feed_cfg in feeds:
        url = feed_cfg["url"]
        name = feed_cfg.get("name", url)
        feed_max = feed_cfg.get("max_articles_per_feed", max_per_feed)
        print(f"  {name}...")

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
            if not article_url or article_url in seen_urls:
                continue

            # Data pubblicazione
            published = None
            for date_field in ["published_parsed", "updated_parsed"]:
                if hasattr(entry, date_field) and getattr(entry, date_field):
                    t = getattr(entry, date_field)
                    try:
                        published = datetime(*t[:6], tzinfo=timezone.utc)
                    except Exception:
                        pass
                    break

            if published and published < cutoff:
                continue

            # Descrizione dall'RSS (titolo + summary se disponibile)
            description = ""
            for field in ["summary", "description", "content"]:
                val = entry.get(field, "")
                if isinstance(val, list) and val:
                    val = val[0].get("value", "")
                if val:
                    description = strip_html(val)[:600]
                    break

            new_articles.append({
                "url": article_url,
                "title": strip_html(entry.get("title", "Senza titolo")),
                "source": name,
                "description": description,
                "published": published.isoformat() if published else datetime.now(timezone.utc).isoformat(),
                "added_at": datetime.now(timezone.utc).isoformat(),
            })
            seen_urls.add(article_url)
            count += 1

        if count > 0:
            print(f"    {count} nuovi articoli")

    return new_articles


def main():
    parser = argparse.ArgumentParser(description="Fetch RSS feeds -> articles_cache.json")
    parser.add_argument("--config", default=Path(__file__).parent / "feeds.yaml")
    parser.add_argument("--dry-run", action="store_true", help="Mostra cosa fetcherebbe senza salvare")
    parser.add_argument("--lookback-days", type=int, default=None)
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Config non trovata: {config_path}")
        sys.exit(1)

    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    max_per_feed = config.get("max_articles_per_feed", 2)
    lookback_days = args.lookback_days if args.lookback_days is not None else config.get("lookback_days", 7)
    feeds = config.get("feeds", [])

    print(f"=== Ingest RSS ===")
    print(f"Feed attivi: {len(feeds)} | Max per feed: {max_per_feed} | Lookback: {lookback_days}gg\n")

    # Carica cache esistente
    existing = load_cache()
    seen_urls = {a["url"] for a in existing}
    print(f"Articoli in cache: {len(existing)}\n")

    print("Fetching feed...")
    new_articles = fetch_new_articles(feeds, max_per_feed, lookback_days, seen_urls)

    print(f"\nNuovi articoli trovati: {len(new_articles)}")

    if args.dry_run:
        print("\n[DRY RUN] Nessuna modifica alla cache.")
        for a in new_articles:
            print(f"  - {a['title']} ({a['source']})")
        return

    if new_articles:
        # Nuovi articoli in cima, esistenti in fondo
        updated = new_articles + existing
        save_cache(updated)
        print(f"Cache aggiornata: {len(updated)} articoli totali.")
    else:
        print("Nessun articolo nuovo.")


if __name__ == "__main__":
    main()
