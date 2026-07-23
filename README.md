# EngineAI Monitoring

**Watch & Alert** — Automatisierte Nachrichten- und Marktüberwachung mit Python.
Referenzprojekt von Stephan Paul.

Beobachtet RSS-Feeds und Google News, klassifiziert Artikel-Relevanz per LLM,
speichert den Zustand in SQLite und verschickt Alerts über Telegram, ntfy.sh
oder E-Mail. Die mitgelieferte Konfiguration beobachtet Nachrichten rund um
den Börsengang von "EngineAI Robotics" — jede Quelle, jedes Stichwort und
jeder Kanal ist frei konfigurierbar.

## 📖 Das Buch

Dieses Repository ist das vollständige, lauffähige Referenzprojekt zum Buch
*Watch & Alert*. Das Buch erklärt das **Warum** hinter jeder
Architekturentscheidung, vergleicht Alternativen (SQLite vs. PostgreSQL,
Cron vs. systemd-Timer, Cloud-LLM vs. lokales Ollama) und geht den Code über
15 Kapitel hinweg durch. Dieses Repo ist der Code, das Buch ist das Handbuch.

## ✨ Features

- 🔄 **Datenbeschaffung** — RSS-Feeds und Google News RSS, mit Timeout,
  Retry und Exponential Backoff (Kapitel 7).
- 🧠 **LLM-Klassifikation** — OpenAI-kompatible Cloud-Provider oder lokales
  Ollama, mit Keyword-Fallback, falls das LLM nicht erreichbar ist
  (Kapitel 9).
- 🎯 **Mehrstufige Filter-Pipeline** — Brand-Präsenz (inkl. Schreibvarianten),
  Zeit-Filter, URL-Deduplizierung, Keyword-Heuristik (Kapitel 7 und 10).
- 💾 **SQLite-Persistenz** — Deduplizierung per URL-Hash, aufräumbare
  `seen_articles`-Tabelle (Kapitel 8).
- 📬 **Multi-Channel-Benachrichtigung** — Telegram (primär, HTML-formatiert),
  ntfy.sh (Fallback), E-Mail (Digest) (Kapitel 11).
- ⏰ **Scheduler-agnostisch** — Cron, anacron oder systemd-Timer, deine Wahl
  (Kapitel 12).
- 🛡️ **Security by Default** — Geheimnisse ausschließlich über `.env`,
  Dateirechte, Token-Rotation, Troubleshooting-Checkliste (Kapitel 4, 5, 13).
- 🧪 **Getestet mit pytest** — Reine Funktionstests, gemockte externe
  Aufrufe, isolierte Testdatenbank pro Testlauf (Kapitel 14).
- 🐳 **Container-fertig** — Dockerfile inklusive (Kapitel 15).

## 🏗️ Architektur

```
Cron / systemd-Timer
        │
        ▼
RSS / Google News  ──▶  Filter-Pipeline  ──▶  LLM-Klassifikation
                                                     │
                                                     ▼
                        SQLite (Zustand,      Telegram / ntfy / E-Mail
                        Dedup, Historie)  ◀──────────┘
```

Jede Schicht ist austauschbar. RSS gegen Web-Scraping tauschen, Telegram
gegen einen anderen Kanal, SQLite gegen PostgreSQL — der Rest der Pipeline
merkt es nicht. Details dazu in Kapitel 3 des Buchs.

## 🚀 Quick Start

### Voraussetzungen

- Python 3.10 oder neuer
- Ein Telegram-Bot-Token (via [@BotFather](https://t.me/BotFather)) und
  deine Chat-ID — siehe Kapitel 11.2 im Buch
- Optional: ein API-Key eines OpenAI-kompatiblen LLM-Providers, oder eine
  lokale [Ollama](https://ollama.com)-Installation

### 1. Klonen und Abhängigkeiten installieren

```bash
git clone https://github.com/watch-alert-book/engineai-monitoring.git
cd engineai-monitoring
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Geheimnisse konfigurieren

```bash
cp .env.example .env
```

Öffne `.env` und trage deine echten Werte ein:

```dotenv
TELEGRAM_BOT_TOKEN=<TELEGRAM_BOT_TOKEN>
TELEGRAM_CHAT_ID=<TELEGRAM_CHAT_ID>

LLM_PROVIDER=openai
LLM_API_KEY=<LLM_API_KEY>
LLM_BASE_URL=<LLM_BASE_URL>
LLM_MODEL=<LLM_MODEL>

NTFY_TOPIC=<NTFY_TOPIC>
```

⚠️ **`.env` niemals committen.** Die mitgelieferte `.gitignore` schließt sie
aus — prüfe das trotzdem nach deinem ersten `git add`.

### 3. Watcher konfigurieren

`config.yaml` enthält Quellen, Marken-Varianten und Kanäle:

```yaml
target_company:
  name: "EngineAI Robotics"
  aliases: ["EngineAI", "Engine AI", "EngineAI Robotics"]

data_sources:
  rss_feeds:
    - name: "TechCrunch"
      url: "https://techcrunch.com/feed/"
      enabled: true

notifications:
  telegram:
    enabled: true
  ntfy:
    enabled: true
```

### 4. Einmal testen

```bash
python EngineAI_IPO_Starter.py --check
```

Das Skript holt die Feeds, filtert, klassifiziert und verschickt (bei einem
echten Treffer) eine Telegram-Nachricht.

### 5. Automatisieren (Produktivbetrieb)

**Cron (einfachste Variante):**

```bash
crontab -e
# Direkt die venv-Python-Binary aufrufen, kein "source activate":
0 * * * * cd /pfad/zu/engineai-monitoring && .venv/bin/python EngineAI_IPO_Starter.py --check >> logs/cron.log 2>&1
```

**systemd-Timer** oder **Docker** — siehe Kapitel 12 und 15 im Buch für
vollständige Anleitungen inklusive Fallstricken.

## 🧰 Projektstruktur

```
engineai-monitoring/
├── .env.example              ← Vorlage, keine echten Geheimnisse
├── .gitignore
├── config.yaml                ← Quellen, Marken, Kanäle
├── requirements.txt
├── EngineAI_IPO_Starter.py    ← Haupteinstiegspunkt, orchestriert den Lauf
├── database.py                ← SQLite-Manager (Schema, Dedup, Cleanup)
├── filters.py                 ← Filter-Pipeline (Brand, Zeit, Keywords)
├── llm_client.py               ← LLM-Client (OpenAI-kompatibel/Ollama) mit Fallback
├── notifications.py           ← Telegram, ntfy, E-Mail, Multi-Channel-Versand
├── rss_sources.py             ← RSS- und Google-News-Beschaffung mit Retry
├── tests/
│   ├── test_filters.py
│   ├── test_database.py
│   └── test_notifications.py
├── .github/workflows/tests.yml
└── Dockerfile
```

## 🧪 Testen

```bash
pip install pytest
pytest
```

Der Test-Stack: reine Funktionstests für die Filter-Pipeline, gemockte
HTTP-Aufrufe für Benachrichtigungen (`unittest.mock`/`monkeypatch`), sowie
eine isolierte SQLite-Testdatenbank pro Testlauf (`tmp_path`-Fixture).
Details in Kapitel 14 im Buch.

## 🐛 Troubleshooting

| Symptom | Wahrscheinliche Ursache | Lösung |
|---|---|---|
| `ModuleNotFoundError` | venv nicht aktiviert | `source .venv/bin/activate` |
| Telegram-Nachrichten kommen nicht an | Token/Chat-ID falsch oder abgelaufen | Bei @BotFather `/revoke`, neue Chat-ID via `getUpdates` ermitteln |
| ntfy.sh nicht erreichbar | Häufig ein DNS-Filter (AdGuard, Pi-hole) | Anderen DNS-Resolver testen oder mobile Daten |
| LLM antwortet mit kaputtem JSON | Modell hält sich nicht ans Format | `parse_json_response()` fängt die üblichen Fälle ab (Kapitel 9.3) |
| Cron läuft nicht | Minimale PATH-Umgebung in Cron | Absoluten Pfad zur venv-Python-Binary verwenden (Kapitel 6.5/12) |

Ausführliche Troubleshooting-Checkliste: Anhang A.3 im Buch.

## 📜 Lizenz

**Code:** MIT — siehe `LICENSE`. Nutzung, Veränderung und Weitergabe
(auch kommerziell) sind erlaubt.

**Buch:** *"Watch & Alert"* von Stephan Paul — Text und Aufbau des Buchs
sind urheberrechtlich geschützt. Dieses Repository enthält nur den
begleitenden Code, nicht den Buchtext selbst.

## 🔗 Links

- 📂 Dieses Repository: https://github.com/watch-alert-book/engineai-monitoring
- 🐛 Issues: https://github.com/watch-alert-book/engineai-monitoring/issues
- 👤 Autor: Stephan Paul
