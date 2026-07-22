EngineAI-Monitoring
Watch & Alert — A production-grade news & market monitoring system in Python. Reference project for the book "Watch & Alert — Automatisierte Nachrichten- und Marktüberwachung mit Python" by Stephan Paul.






Watches RSS feeds & Google News, classifies article relevance with an LLM, persists state in SQLite, and sends instant alerts via Telegram, ntfy.sh, or email. The default configuration watches for news about EngineAI Robotics going public, but every input — feeds, keywords, channels — is configurable.

📖 The Book
This repository is the complete, runnable reference project for the German-language book Watch & Alert. The book explains the why behind every architectural decision, compares alternatives (SQLite vs. Postgres, Cron vs. systemd-Timer, OpenAI vs. local Ollama), and walks through the code in 15 chapters. This repo is the code; the book is the manual.

📘 Buy the book on Amazon · 📚 Read the table of contents

✨ Features
🔄 Multi-source data acquisition — RSS feeds, Google News RSS, with configurable timeouts, retries, and exponential backoff.
🧠 LLM-powered classification — Plug in OpenAI, Anthropic, or any OpenAI-compatible provider. Local LLM via Ollama works too.
🎯 Brand-presence + keyword filtering — Multi-stage pipeline that drops noise before the LLM ever sees it.
💾 SQLite persistence — Deduplication by URL hash, cleanup routines, prepared statements.
📬 Multi-channel notifications — Telegram (formatted Markdown/HTML), ntfy.sh (priority levels), email digests. Telegram with ntfy fallback built in.
⏰ Pluggable scheduling — Cron, systemd-timer, or anacron — your choice. The system is scheduler-agnostic.
🛡️ Security by default — Secrets in .env, file permissions, token rotation guide, audit checklist.
🧪 Tested with pytest — Pure-function tests, mocked external calls, temporary test databases.
🐳 Container-ready — Dockerfile and docker-compose included.
📖 Open source (MIT) — Fork it, ship it, learn from it.
🏗️ Architecture
text

Copy
   ┌─────────────┐    ┌──────────────┐    ┌──────────┐    ┌─────────┐

   │ Cron / Timer│───▶│ RSS / News   │───▶│ Filter   │───▶│   LLM   │

   └─────────────┘    └──────────────┘    └──────────┘    └────┬────┘

                                                                │

                                                                 ▼

                          ┌──────────────┐    ┌─────────────────────┐

                          │  Telegram /  │◀───│  SQLite (state,     │

                          │  ntfy / Mail │    │  dedup, history)    │

                          └──────────────┘    └─────────────────────┘
Every layer is replaceable. Swap RSS for web scraping, swap Telegram for Discord, swap SQLite for Postgres — the rest of the pipeline doesn't care.

For the full architectural deep-dive, see Chapter 3 of the book.

🚀 Quick Start
Prerequisites
Python 3.10 or higher (install guide)
pip (usually ships with Python)
A Telegram bot token (talk to @BotFather) and your chat ID
Optional: an OpenAI API key or a local Ollama install
1. Clone & install
bash

Copy
git clone https://github.com/watch-alert-book/engineai-monitoring.git

cd engineai-monitoring

python3 -m venv .venv

source .venv/bin/activate

pip install -r requirements.txt
2. Configure secrets
bash

Copy
cp .env.example .env
Open .env and fill in your values:

dotenv

Copy
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...your-token-here

TELEGRAM_CHAT_ID=987654321


# Choose ONE: cloud LLM (OpenAI-compatible) or local Ollama

OPENAI_API_KEY=sk-...

OPENAI_BASE_URL=https://api.openai.com/v1

OPENAI_MODEL=gpt-4o-mini


# Or for local:

# OLLAMA_MODEL=llama3.2
⚠️ Never commit .env to git. The repo's .gitignore is set up to prevent this — but double-check after your first git add.

3. Configure the watcher
Edit config.yaml to set your feeds, keywords, and notification preferences:

yaml

Copy
feeds:

  - name: "EngineAI Search (Google News)"

    url: "https://news.google.com/rss/search?q=engineai+robotics&hl=en-US"

  - name: "Reuters Technology"

    url: "https://www.reuters.com/technology/feed/"


brand:

  - "engineai"

  - "engine ai"

  - "engineai robotics"


keywords:

  buy:    ["ipo", "börsengang", "shares available", "is now public"]

  watch:  ["listing", "going public", "s-1", "pre-ipo"]


scheduler:

  interval_hours: 1

  quiet_hours:    []  # e.g. ["23:00-07:00"] to suppress non-critical alerts at night


notifier:

  primary:  telegram

  fallback: ntfy

  ntfy_topic: "engineai-ipo-alerts"
4. Run once (test)
bash

Copy
python -m src.watcher --once --verbose
You should see the watcher fetch feeds, filter articles, and (if it finds anything) send a Telegram message. If you don't have a real match in the feeds, set dry_run: true in config.yaml to skip the actual notification.

5. Schedule (production)
Pick one of these:

Cron (simplest):

bash

Copy
crontab -e

# Add this line — runs every hour

0 * * * * cd /path/to/engineai-monitoring && .venv/bin/python -m src.watcher >> watcher.log 2>&1
systemd-timer (modern, recommended):

bash

Copy
sudo cp systemd/engineai-monitoring.service /etc/systemd/system/

sudo cp systemd/engineai-monitoring.timer /etc/systemd/system/

sudo systemctl daemon-reload

sudo systemctl enable --now engineai-monitoring.timer

sudo systemctl list-timers engineai-monitoring
Docker:

bash

Copy
docker compose up -d

docker compose logs -f
🧰 Project Structure
text

Copy
engineai-monitoring/

├── README.md

├── LICENSE                         ← MIT

├── CHANGELOG.md

├── requirements.txt

├── pyproject.toml                  ← modern packaging

├── .env.example                    ← template, no real secrets

├── .gitignore

├── config.yaml                     ← your feed + keyword config

│

├── src/

│   ├── __init__.py

│   ├── watcher.py                  ← main entry point, orchestrates the loop

│   ├── feeds.py                    ← RSS + Google News fetching

│   ├── database.py                 ← SQLite manager (schema, dedup, cleanup)

│   ├── llm_client.py               ← OpenAI / Ollama wrapper with retry

│   ├── pipeline.py                 ← filter pipeline (brand + keyword + time)

│   ├── notifier.py                 ← Telegram + ntfy + email dispatch

│   └── config.py                   ← config + .env loader

│

├── tests/

│   ├── conftest.py                 ← shared fixtures (temp DB, mock fetches)

│   ├── test_feeds.py

│   ├── test_pipeline.py

│   ├── test_database.py

│   └── test_notifier.py

│

├── systemd/                        ← production deployment

│   ├── engineai-monitoring.service

│   └── engineai-monitoring.timer

│

├── docker/

│   ├── Dockerfile

│   └── docker-compose.yml

│

└── docs/

    ├── ARCHITECTURE.md

    ├── TROUBLESHOOTING.md

    ├── SECURITY.md

    └── book-mapping.md             ← which chapter explains which file
⚙️ Configuration Reference
See config.yaml for a fully-commented example. Quick reference:

Key	Type	Default	Description
feeds[].url	string	—	RSS or Google News URL
feeds[].enabled	bool	true	Disable without deleting
brand[]	list of strings	[]	Brand names to look for (case-insensitive)
keywords.buy[]	list	[]	Words that trigger a "buy now" alert
keywords.watch[]	list	[]	Words that trigger a "watch" alert
scheduler.interval_hours	int	1	Run frequency
scheduler.quiet_hours	list	[]	Suppress non-critical alerts in these windows
notifier.primary	string	telegram	One of: telegram, ntfy, email
notifier.fallback	string	ntfy	Used if primary fails
llm.provider	string	openai	openai or ollama
llm.temperature	float	0.3	Lower = more deterministic
llm.max_tokens	int	500	Cap on response size
🧪 Testing
bash

Copy
# Run the full suite

pytest


# With coverage

pytest --cov=src --cov-report=term-missing


# Only fast unit tests (skip integration)

pytest -m "not integration"
The test suite uses:

pytest for the framework
pytest-cov for coverage
responses for mocking HTTP calls
freezegun for time-dependent tests
A temporary SQLite file per test for database isolation
🐛 Troubleshooting
Symptom	Likely cause	Fix
ModuleNotFoundError	venv not activated	source .venv/bin/activate
401 Unauthorized (Telegram)	Wrong or rotated token	Re-issue token via @BotFather /revoke
400 Bad Request (Telegram)	Markdown parse error	Switch parse_mode from Markdown to HTML
LLM returns broken JSON	Model hallucinating brackets	The book shows a robust regex-based parser in Ch. 9
ntfy not delivered	DNS block (AdGuard, Pi-hole)	Try a different DNS resolver or mobile data
Nothing found in feeds	Brand name doesn't match	Check brand[] list — add variants
Cron doesn't run	PATH issue in cron	Cron uses a minimal PATH; set it explicitly in your crontab
Full troubleshooting matrix: docs/TROUBLESHOOTING.md

🤝 Contributing
Pull requests welcome. For substantial changes, please open an issue first to discuss what you'd like to change.

🐛 Bug reports: open an issue with the bug label
💡 Feature ideas: open an issue with the enhancement label
📖 Docs fixes: directly edit and PR — typos are loved
🔒 Security issues: see SECURITY.md — please don't open a public issue
📜 License
Code: MIT — see LICENSE. You can use this in commercial and private projects, modify it, and redistribute it. Attribution appreciated but not required.

Book: "Watch & Alert" by Stephan Paul — the prose and the book's structure are copyrighted. This repo only contains the code that accompanies the book, not the book content itself.

🙏 Acknowledgments
📘 The book Watch & Alert by Stephan Paul (Stephan Paul, 2026) — the project structure, architecture decisions, and best practices in this repo all follow the patterns taught in the book.
🤖 feedparser by Kurt McKee — the de-facto RSS parser for Python.
📡 python-telegram-bot — best-in-class Telegram bot library.
🧠 OpenAI / Anthropic / Ollama — for the LLM layer.
🐧 The Linux & open-source community — the foundation this whole thing is built on.
🔗 Links
📘 Book on Amazon: https://www.amazon.de/ (search for "Watch & Alert — Stephan Paul")
📂 This repository: https://github.com/watch-alert-book/engineai-monitoring
🐛 Issue tracker: https://github.com/watch-alert-book/engineai-monitoring/issues
💬 Discussions: https://github.com/watch-alert-book/engineai-monitoring/discussions
👤 Author: Stephan Paul
📚 More from the book series: coming soon
Built with ☕ and Python · Made for people who don't want to miss the next big thing.
