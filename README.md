# AI Knowledge Base — Automatica

Sistema che legge internet al posto tuo e ti fa trovare un briefing ogni mattina in Obsidian.

**Guarda il video**: [link al video]  
**Repo**: [github.com/LogikaAgency/ai-knowledge-base](https://github.com/LogikaAgency/ai-knowledge-base)

---

## Come funziona

```
RSS Feed, YouTube, Newsletter, Blog
            ↓ ogni giorno automatico
        NotebookLM
   (Gemini 2.5 elabora tutto — Google paga)
            ↓
          Claude
   (chiede, organizza, scrive)
            ↓
         Obsidian
   (nota pronta ogni mattina)
```

Il tuo PC fa tutto da solo alle 06:30. Tu apri Obsidian e leggi.

---

## Requisiti

- Windows 10/11
- Python 3.10 o superiore
- Node.js 18 o superiore
- [Claude Code](https://claude.ai/code)
- [Obsidian](https://obsidian.md)
- Un account Google (per NotebookLM)

---

## Installazione completa — passo per passo

### 1. Clona il repo

Apri il **Prompt dei comandi** (cmd) o **PowerShell** e incolla:

```bash
git clone https://github.com/LogikaAgency/ai-knowledge-base.git
cd ai-knowledge-base
```

> **Non hai git?** Scaricalo da [git-scm.com](https://git-scm.com/download/win) e installalo con le opzioni default.

---

### 2. Installa Python

Controlla se ce l'hai già:
```bash
python --version
```

Se vedi `Python 3.10` o superiore sei a posto. Se non lo hai:

1. Vai su [python.org/downloads](https://python.org/downloads)
2. Scarica l'ultima versione stabile
3. **IMPORTANTE**: durante l'installazione spunta **"Add Python to PATH"**
4. Riapri il terminale dopo l'installazione

Poi installa le dipendenze del progetto:
```bash
pip install feedparser pyyaml python-dateutil
```

Verifica che tutto sia installato:
```bash
pip show feedparser pyyaml python-dateutil
```
Devono comparire tutte e tre le librerie.

---

### 3. Installa Node.js

Controlla se ce l'hai già:
```bash
node --version
```

Se vedi `v18` o superiore sei a posto. Se non lo hai:

1. Vai su [nodejs.org](https://nodejs.org)
2. Scarica la versione **LTS** (quella consigliata)
3. Installa con le opzioni default
4. Riapri il terminale

---

### 4. Installa Claude Code

```bash
npm install -g @anthropic-ai/claude-code
```

Poi fai il login:
```bash
claude
```

Si apre il browser per autenticarti con il tuo account Anthropic. Segui le istruzioni e torna al terminale.

Verifica che funzioni:
```bash
claude --version
```

---

### 5. Configura il MCP per NotebookLM

Prima, crea un notebook su [notebooklm.google.com](https://notebooklm.google.com) e chiamalo **"AI Weekly"** (o cambia il nome in `feeds.yaml`).

Poi nel terminale:
```bash
npx notebooklm-mcp@latest
```

La prima volta ti chiede di autenticarti:
- Si apre una finestra Chrome
- Fai il login con Google
- Torna al terminale — vedrai `Auth successful. Server ready.`

Questa autenticazione rimane salvata. Non la rifai più.

Poi aggiungi il MCP a Claude:
```bash
claude mcp add notebooklm -- npx notebooklm-mcp@latest
```

---

### 6. Configura il MCP per Obsidian

Prima devi trovare il percorso del tuo vault Obsidian. Di solito è:
```
C:\Users\TuoNome\Documents\NomeVault
```

Per trovarlo: apri Obsidian → in basso a sinistra clicca sul nome del vault → **Manage vaults** → vedi il percorso completo.

Poi aggiungi il MCP a Claude (sostituisci il percorso con il tuo):
```bash
claude mcp add obsidian -- npx @bitbonsai/mcpvault C:\Users\TuoNome\Documents\NomeVault
```

---

### 7. Verifica che i MCP siano attivi

```bash
claude mcp list
```

Devono comparire sia `notebooklm` che `obsidian`. Se manca uno, ripeti il passaggio corrispondente.

Puoi anche chiedere a Claude direttamente:
```bash
claude -p "quali tool MCP hai a disposizione?"
```

Deve elencare i tool di entrambi i server.

---

### 8. Configura le tue fonti RSS

Apri `feeds.yaml` con qualsiasi editor di testo (anche il Blocco Note).

Il file ha già 40+ fonti organizzate per categoria. Tutto quello che **non** ha `#` davanti viene fetchato in automatico. Per disattivare una fonte metti `#` davanti alla riga `url`. Per attivarne una commentata togli il `#`.

Per aggiungere un nuovo feed:
```yaml
- url: https://esempio.com/feed.xml
  name: Nome che vuoi
```

Per aggiungere un canale YouTube (vedi come trovare il channel_id sotto):
```yaml
- url: https://www.youtube.com/feeds/videos.xml?channel_id=UCxxxxxxx
  name: Nome canale
```

---

### 9. Configura l'automazione su Windows

Apri **PowerShell come Amministratore** (tasto destro su PowerShell → Esegui come amministratore) e incolla:

```powershell
powershell -ExecutionPolicy Bypass -File ".\setup_windows.ps1"
```

Questo crea due task nel Task Scheduler:

| Task | Quando | Cosa fa |
|---|---|---|
| Logika AI Briefing Giornaliero | Ogni giorno alle 06:30 | 3 punti chiave del giorno in Obsidian |
| Logika AI Digest Settimanale | Ogni lunedì alle 07:00 | Digest completo + audio briefing |

Entrambi partono automaticamente appena accendi il PC se l'orario era già passato.

---

### 10. Testa che tutto funzioni

Prima di aspettare il mattino, prova subito:

```bash
# Test senza modificare niente — mostra cosa fetcherebbe
python ingest.py --dry-run

# Esegui per davvero
python ingest.py --lookback-days 1

# Genera il briefing
python digest.py --daily
```

Apri Obsidian — dopo 2-3 minuti trovi la nota nella cartella `Digest/`.

Oppure avvia il task manualmente da PowerShell:
```powershell
Start-ScheduledTask -TaskName "Logika AI Briefing Giornaliero"
```

---

## Come trovare il channel_id di un canale YouTube

1. Vai sulla pagina del canale YouTube
2. Vai su [commentpicker.com/youtube-channel-id.php](https://commentpicker.com/youtube-channel-id.php)
3. Incolla l'URL del canale
4. Copia il channel_id che appare
5. Aggiungi in `feeds.yaml`:
```yaml
- url: https://www.youtube.com/feeds/videos.xml?channel_id=UCxxxxxxx
  name: Nome canale
```

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
# Mostra cosa fetcherebbe senza fare niente
python ingest.py --dry-run

# Fetch manuale degli ultimi 3 giorni
python ingest.py --lookback-days 3

# Genera briefing giornaliero (3 punti)
python digest.py --daily

# Genera digest settimanale completo
python digest.py

# Genera digest settimanale + audio
python digest.py --audio

# Genera digest su un tema specifico
python digest.py --topic "modelli open source"
```

---

## FAQ

**Il PC deve essere sempre acceso?**
No. Il Task Scheduler ha `StartWhenAvailable` — se il PC era spento, il job parte appena lo accendi.

**Obsidian deve essere aperto?**
Il `.bat` lo avvia automaticamente se è chiuso, aspetta 8 secondi che il plugin si carichi e poi procede.

**Twitter e LinkedIn si possono automatizzare?**
No in modo affidabile. L'API X costa $100/mese, LinkedIn non ha API pubblica. Copia l'URL del post/thread e aggiungilo manualmente in NotebookLM — 10 secondi di lavoro.

**Una newsletter non ha RSS — come faccio?**
Usa [kill-the-newsletter.com](https://kill-the-newsletter.com): ti dà un indirizzo email e un link RSS. Iscriviti alla newsletter con quell'email e il feed RSS si aggiorna automaticamente.

**Quante fonti posso aggiungere?**
Non c'è un limite tecnico. Tieni presente che più fonti aggiungi, più tempo impiega l'ingest e più il notebook NotebookLM cresce. Con 20-30 fonti attive il sistema gira in meno di 5 minuti.

**Posso usarlo su Mac?**
Sì. Usa `run_daily.sh` al posto di `run_daily.bat` e configura cron con:
```bash
crontab -e
# Aggiungi:
30 6 * * * /percorso/completo/run_daily.sh
```

**I log dove sono?**
Nella stessa cartella del progetto: `daily_run.log` e `weekly_run.log`.

---

## Crediti

- [notebooklm-mcp](https://github.com/PleasePrompto/notebooklm-mcp) — MCP per NotebookLM
- [mcpvault](https://github.com/bitbonsai/mcpvault) — MCP per Obsidian
- [Claude Code](https://claude.ai/code) — orchestrazione

---

Fatto da [Logika](https://www.logika.agency)
