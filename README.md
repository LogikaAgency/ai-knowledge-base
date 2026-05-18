# AI Knowledge Base — Automatica

Sistema che legge internet al posto tuo e ti fa trovare un briefing ogni mattina in Obsidian.

**Guarda il video**: [link al video]

---

## Come funziona

```
RSS Feed, YouTube, Newsletter
          ↓ (ogni giorno automatico)
      NotebookLM
    (Google elabora tutto — gratis)
          ↓
        Claude
    (chiede, organizza, scrive)
          ↓
       Obsidian
  (nota pronta ogni mattina)
```

Il tuo PC fa tutto da solo. Tu apri Obsidian e leggi.

---

## Requisiti

- Windows 10/11
- [Claude Code](https://claude.ai/code) installato
- [Obsidian](https://obsidian.md) installato
- Python 3.10+

---

## Setup (10 minuti)

### 1. Clona il repo

```bash
git clone https://github.com/LogikaAgency/ai-knowledge-base.git
cd ai-knowledge-base
```

### 2. Installa le dipendenze Python

```bash
pip install feedparser pyyaml python-dateutil
```

### 3. Configura il MCP NotebookLM

```bash
npx notebooklm-mcp@latest
```

Segui il prompt per il login Google (si apre Chrome, lo fai una volta sola).

### 4. Aggiungi i MCP a Claude Code

```bash
claude mcp add notebooklm -- npx notebooklm-mcp@latest
```

Per Obsidian, passa il percorso del tuo vault:

```bash
claude mcp add obsidian -- npx @bitbonsai/mcpvault C:\Users\tuonome\Documents\ObsidianVault
```

Verifica: `claude mcp list` — devono comparire entrambi.

### 6. Crea il notebook in NotebookLM

Vai su [notebooklm.google.com](https://notebooklm.google.com) e crea un notebook chiamato **"AI Weekly"** (o cambia il nome in `feeds.yaml`).

### 7. Configura le tue fonti RSS

Apri `feeds.yaml` e aggiungi/rimuovi i feed che vuoi seguire. Quelli di default coprono i principali blog AI e newsletter.

### 8. Configura Task Scheduler (una volta sola)

Apri PowerShell come Amministratore:

```powershell
powershell -ExecutionPolicy Bypass -File ".\setup_windows.ps1"
```

Questo crea due task automatici:
- **Ogni giorno alle 06:30** → briefing giornaliero (3 punti chiave)
- **Ogni lunedì alle 07:00** → digest settimanale completo + audio

Se il PC era spento all'orario, parte appena lo accendi.

### 9. Testa subito

```powershell
Start-ScheduledTask -TaskName "Logika AI Briefing Giornaliero"
```

Apri Obsidian — dopo 2-3 minuti trovi la nota nella cartella `Digest/`.

---

## Struttura file

```
ai-knowledge-base/
├── feeds.yaml          ← le tue fonti RSS (modifica qui)
├── ingest.py           ← fetcha RSS → aggiunge a NotebookLM
├── digest.py           ← genera briefing → salva in Obsidian
├── run_daily.bat       ← script giornaliero (chiamato da Task Scheduler)
├── run_weekly.bat      ← script settimanale (chiamato da Task Scheduler)
└── setup_windows.ps1   ← configura Task Scheduler (esegui una volta)
```

---

## Comandi utili

```bash
# Test ingest senza modificare niente
python ingest.py --dry-run

# Genera briefing giornaliero manualmente
python digest.py --daily

# Genera digest settimanale + audio
python digest.py --audio

# Aggiungi un feed specifico al test
python ingest.py --lookback-days 3
```

---

## FAQ

**Il PC deve essere sempre acceso?**
No. Il Task Scheduler ha `StartWhenAvailable` — se il PC era spento, il job parte appena lo accendi.

**Obsidian deve essere aperto?**
Il `.bat` lo avvia automaticamente se è chiuso. Assicurati che il percorso di installazione sia quello standard (`%LOCALAPPDATA%\Obsidian\Obsidian.exe`).

**Twitter e LinkedIn si possono automatizzare?**
No in modo affidabile. L'API X costa $100/mese, LinkedIn non ha API pubblica. Per queste fonti: copia l'URL del post/thread e aggiungilo manualmente in NotebookLM. 10 secondi di lavoro.

**Posso aggiungere canali YouTube?**
Sì, YouTube ha RSS nativo gratuito. Cerca il `channel_id` del canale e aggiungi in `feeds.yaml`:
```yaml
- url: https://www.youtube.com/feeds/videos.xml?channel_id=UCxxxxxxx
  name: Nome canale
```

**Come trovo il channel_id di un canale YouTube?**
Vai sulla pagina del canale → tasto destro → Visualizza sorgente pagina → cerca `channelId`. Oppure usa [commentpicker.com/youtube-channel-id.php](https://commentpicker.com/youtube-channel-id.php).

---

## Crediti

- [notebooklm-mcp](https://github.com/PleasePrompto/notebooklm-mcp) — MCP per NotebookLM
- [mcpvault](https://github.com/bitbonsai/mcpvault) — MCP per Obsidian
- [Claude Code](https://claude.ai/code) — orchestrazione

---

Fatto da [Logika](https://www.logika.agency)
