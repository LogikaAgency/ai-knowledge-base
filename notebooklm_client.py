"""
notebooklm_client.py — Playwright client per NotebookLM

Gestisce l'autenticazione con profilo browser persistente.
Prima esecuzione: apre browser visibile per login Google (una volta sola).
Esecuzioni successive: usa il profilo salvato, completamente automatico.

Test manuale:
  python notebooklm_client.py --notebook-url URL --urls-file pending.txt
  python notebooklm_client.py --notebook-url URL --urls-file pending.txt --show-browser
  python notebooklm_client.py --create-notebook "AI Weekly — 2026-W21"
"""

import asyncio
import argparse
import sys
from pathlib import Path

PROFILE_DIR = Path.home() / ".notebooklm-profile"
NOTEBOOKLM_BASE = "https://notebooklm.google.com"


async def wait_for_login(page):
    """Aspetta che l'utente completi il login Google (max 5 minuti)."""
    print("\n" + "="*50)
    print("PRIMA CONFIGURAZIONE — LOGIN GOOGLE")
    print("="*50)
    print("Si apre il browser. Accedi con il tuo account Google.")
    print("Dopo il login la finestra rimane aperta — non chiuderla.")
    print("Torna qui quando sei dentro NotebookLM.\n")

    await page.goto(NOTEBOOKLM_BASE)

    # Aspetta che compaia la homepage di NotebookLM (post-login)
    try:
        await page.wait_for_selector(
            'button:has-text("New notebook"), button:has-text("Nuovo notebook"), '
            'nb-notebook-list, [data-testid="new-notebook-button"]',
            timeout=300_000  # 5 minuti
        )
        print("Login completato. Profilo salvato in ~/.notebooklm-profile\n")
    except Exception:
        print("ERRORE: login non completato entro 5 minuti.")
        sys.exit(1)


async def add_source_url(page, url: str) -> bool:
    """Aggiunge un URL come fonte al notebook corrente."""
    try:
        # Apri dialog "Add source"
        add_btn = page.locator(
            'button:has-text("Add source"), button:has-text("Aggiungi fonte"), '
            'button:has-text("Add"), [aria-label*="Add source"], '
            '[data-testid="add-source-button"], button[mattooltip*="source"]'
        ).first
        await add_btn.click(timeout=10_000)
        await page.wait_for_timeout(800)

        # Seleziona opzione "Link" / "Website" / "URL"
        link_opt = page.locator(
            'text=Link, text=Website, text=Sito web, text=URL, '
            '[data-testid="source-type-link"], [data-testid="source-type-url"], '
            'button:has-text("Link"), mat-option:has-text("Link")'
        ).first
        await link_opt.click(timeout=8_000)
        await page.wait_for_timeout(500)

        # Inserisci URL nel campo input
        url_input = page.locator(
            'input[type="url"], input[placeholder*="http"], '
            'input[placeholder*="URL"], input[aria-label*="URL"], '
            'input[aria-label*="url"], textarea[placeholder*="http"]'
        ).first
        await url_input.fill(url, timeout=8_000)
        await page.wait_for_timeout(300)

        # Conferma
        confirm_btn = page.locator(
            'button:has-text("Insert"), button:has-text("Add"), '
            'button:has-text("Inserisci"), button:has-text("Aggiungi"), '
            '[data-testid="confirm-source"], button[type="submit"]'
        ).first
        await confirm_btn.click(timeout=8_000)

        await page.wait_for_timeout(2_000)
        return True

    except Exception as e:
        print(f"    ! Errore: {e}")
        # Prova a chiudere eventuale dialog aperto prima del prossimo URL
        try:
            await page.keyboard.press("Escape")
            await page.wait_for_timeout(500)
        except Exception:
            pass
        return False


async def create_notebook(page, name: str) -> str:
    """Crea un nuovo notebook e ritorna il suo URL."""
    await page.goto(NOTEBOOKLM_BASE)
    await page.wait_for_load_state("networkidle", timeout=30_000)

    new_btn = page.locator(
        'button:has-text("New notebook"), button:has-text("Nuovo notebook"), '
        '[data-testid="new-notebook-button"]'
    ).first
    await new_btn.click(timeout=10_000)
    await page.wait_for_timeout(1_000)

    # Campo nome notebook
    name_input = page.locator(
        'input[placeholder*="notebook"], input[aria-label*="notebook"], '
        'input[placeholder*="Untitled"], input[aria-label*="name"]'
    ).first
    await name_input.fill(name, timeout=8_000)
    await page.keyboard.press("Enter")

    # Aspetta navigazione al nuovo notebook
    await page.wait_for_url(f"{NOTEBOOKLM_BASE}/notebook/**", timeout=20_000)
    notebook_url = page.url
    print(f"Notebook creato: {name}")
    print(f"URL: {notebook_url}")
    return notebook_url


async def run_add_sources(notebook_url: str, urls: list, show_browser: bool = False) -> int:
    """
    Aggiunge una lista di URL come fonti al notebook.
    Prima esecuzione: browser visibile per login.
    Esecuzioni successive: headless automatico.
    """
    from playwright.async_api import async_playwright

    first_run = not PROFILE_DIR.exists()
    headless = not first_run and not show_browser

    if first_run:
        headless = False  # Sempre visibile per il primo login

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=headless,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"],
        )

        page = context.pages[0] if context.pages else await context.new_page()

        if first_run:
            await wait_for_login(page)

        # Naviga al notebook
        print(f"Apertura notebook...")
        await page.goto(notebook_url)
        await page.wait_for_load_state("networkidle", timeout=30_000)
        await page.wait_for_timeout(2_000)

        # Aggiungi fonti una alla volta
        added = 0
        for i, url in enumerate(urls, 1):
            short_url = url[:70] + "..." if len(url) > 70 else url
            print(f"  [{i}/{len(urls)}] {short_url}")
            ok = await add_source_url(page, url)
            if ok:
                added += 1
                print(f"    OK")
            await page.wait_for_timeout(1_500)

        await context.close()

    return added


async def run_create_notebook(name: str, show_browser: bool = False) -> str:
    """Crea un nuovo notebook NotebookLM e ritorna l'URL."""
    from playwright.async_api import async_playwright

    first_run = not PROFILE_DIR.exists()
    headless = not first_run and not show_browser

    if first_run:
        headless = False

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=headless,
            viewport={"width": 1280, "height": 900},
        )

        page = context.pages[0] if context.pages else await context.new_page()

        if first_run:
            await wait_for_login(page)

        url = await create_notebook(page, name)
        await context.close()

    return url


def main():
    parser = argparse.ArgumentParser(description="NotebookLM Playwright client")
    parser.add_argument("--notebook-url", help="URL del notebook NotebookLM")
    parser.add_argument("--urls-file", help="File con un URL per riga da aggiungere")
    parser.add_argument("--create-notebook", metavar="NOME", help="Crea un nuovo notebook con questo nome")
    parser.add_argument("--show-browser", action="store_true", help="Mostra il browser (debug)")
    args = parser.parse_args()

    if args.create_notebook:
        url = asyncio.run(run_create_notebook(args.create_notebook, args.show_browser))
        print(f"\nAggiungi questo URL a feeds.yaml come notebook_url:\n{url}")
        return

    if not args.notebook_url or not args.urls_file:
        parser.print_help()
        sys.exit(1)

    urls_path = Path(args.urls_file)
    if not urls_path.exists():
        print(f"File non trovato: {urls_path}")
        sys.exit(1)

    urls = [u.strip() for u in urls_path.read_text(encoding="utf-8").splitlines() if u.strip()]
    if not urls:
        print("Nessun URL nel file.")
        sys.exit(0)

    print(f"=== NotebookLM Client ===")
    print(f"Notebook: {args.notebook_url}")
    print(f"URL da aggiungere: {len(urls)}\n")

    added = asyncio.run(run_add_sources(args.notebook_url, urls, args.show_browser))
    print(f"\nFatto: {added}/{len(urls)} fonti aggiunte.")


if __name__ == "__main__":
    main()
