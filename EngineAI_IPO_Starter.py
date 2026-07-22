#!/usr/bin/env python3
"""EngineAI_IPO_Starter.py - Hauptskript des Referenzprojekts (Kapitel 3-13).

Verdrahtet die Bausteine aus den Modulen zu einem EngineAIMonitor, dem
"Dirigenten" aus Kapitel 3.2, der in run_check() alle anderen Klassen
orchestriert:

    RSSFeedMonitor/GoogleNewsMonitor  -> rss_sources.fetch_all_sources()
    Filter-Pipeline                  -> filters.filter_pipeline()
    LLM-Klassifikation               -> llm_client.LLMClient
    DatabaseManager                  -> database.DatabaseManager
    NotificationManager              -> notifications.send_alert()

Aufruf (siehe Kapitel 12):
    python EngineAI_IPO_Starter.py --check
"""

import argparse
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

import yaml
from dotenv import load_dotenv

from database import DatabaseManager
from filters import filter_pipeline
from llm_client import LLMClient
from notifications import send_alert
from rss_sources import fetch_all_sources


def load_config(path: str = "config.yaml") -> dict:
    """Lädt die YAML-Konfiguration (Kapitel 4)."""
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Konfig nicht gefunden: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def setup_logging(log_file: str, level: str = "INFO") -> logging.Logger:
    """Logging mit Rotation (Kapitel 13.2)."""
    logger = logging.getLogger("engineai")
    logger.setLevel(level)
    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


class EngineAIMonitor:
    """Der Dirigent (Kapitel 3.2): nimmt alle Bausteine im Konstruktor
    entgegen und orchestriert sie in run_check()."""

    def __init__(self, sources, llm_client: LLMClient, db: DatabaseManager,
                 config: dict, log: logging.Logger):
        self.sources = sources
        self.llm_client = llm_client
        self.db = db
        self.config = config
        self.log = log

    def run_check(self) -> int:
        """Ein vollständiger Durchlauf: holen, filtern, klassifizieren,
        benachrichtigen, speichern. Gibt die Anzahl gefundener Signale zurück."""
        max_age_days = self.config.get("scheduler", {}).get("max_age_days", 2)

        self.log.info(f"Hole Artikel von {len(self.sources)} Quellen...")
        articles = fetch_all_sources(self.sources)
        self.log.info(f"{len(articles)} Artikel roh geholt")

        signal_count = 0
        for article in articles:
            candidate = filter_pipeline(article, self.db, max_age_days)
            if not candidate:
                continue

            self.log.info(f"Kandidat: {candidate['title'][:60]}")
            content = f"{candidate.get('title', '')} {candidate.get('summary', '')}"
            result = self.llm_client.classify(content)

            self.db.mark_seen(candidate["link"], candidate["source"], candidate["title"])

            if not result.get("is_ipo_related"):
                continue

            signal = {
                "title": candidate["title"],
                "source": candidate["source"],
                "source_url": candidate["link"],
                "action_required": result.get("action_required", "watch"),
                "key_findings": result.get("key_findings", []),
            }
            self.db.save_article(
                candidate["title"], candidate["link"], candidate["source"],
                candidate.get("published", ""),
            )
            send_alert(signal, self.config.get("notifications", {}))
            signal_count += 1
            self.log.info(f"Signal gesendet: {candidate['title'][:60]}")

        self.log.info(f"=== Fertig: {signal_count} Signale ===")
        return signal_count


def build_sources(config: dict) -> list:
    """Baut die Quellenliste aus config.yaml (data_sources.rss_feeds)."""
    sources = []
    for feed in config.get("data_sources", {}).get("rss_feeds", []):
        if feed.get("enabled", True):
            sources.append({
                "name": feed["name"],
                "url": feed["url"],
                "max_articles": feed.get("max_articles", 20),
            })
    return sources


def main():
    parser = argparse.ArgumentParser(description="EngineAI IPO Monitor")
    parser.add_argument(
        "--check", action="store_true",
        help="Einen einzelnen Check-Durchlauf ausführen und beenden "
             "(so wird das Skript in Cron/systemd aufgerufen, Kapitel 12).",
    )
    args = parser.parse_args()

    load_dotenv()
    config = load_config("config.yaml")
    log = setup_logging(
        config.get("logging", {}).get("file", "logs/engineai.log"),
        config.get("logging", {}).get("level", "INFO"),
    )

    db = DatabaseManager(config.get("database", {}).get("path", "data/watcher.db"))
    llm_client = LLMClient(
        provider=os.environ.get("LLM_PROVIDER", "openai"),
        api_key=os.environ.get("LLM_API_KEY", ""),
        base_url=os.environ.get("LLM_BASE_URL", ""),
        model=os.environ.get("LLM_MODEL", ""),
    )

    notification_config = {
        "telegram": {
            "enabled": config.get("notifications", {}).get("telegram", {}).get("enabled", False),
            "bot_token": os.environ.get("TELEGRAM_BOT_TOKEN", ""),
            "chat_id": os.environ.get("TELEGRAM_CHAT_ID", ""),
        },
        "ntfy": {
            "enabled": config.get("notifications", {}).get("ntfy", {}).get("enabled", False),
            "topic": os.environ.get("NTFY_TOPIC", ""),
        },
        "email": {
            "enabled": config.get("notifications", {}).get("email", {}).get("enabled", False),
        },
    }
    config["notifications"] = notification_config

    sources = build_sources(config)
    monitor = EngineAIMonitor(sources, llm_client, db, config, log)

    log.info("=== EngineAI IPO Monitor Start ===")
    monitor.run_check()


if __name__ == "__main__":
    main()
