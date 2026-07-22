"""database.py - Kapselt alle SQLite-Operationen (Kapitel 8, Listing 8.9)."""

import hashlib
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path


class DatabaseManager:
    """Kapselt alle SQLite-Operationen für den Watcher."""

    def __init__(self, db_path="data/watcher.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    link TEXT UNIQUE NOT NULL,
                    source TEXT,
                    published TEXT,
                    first_seen TEXT NOT NULL,
                    notified INTEGER DEFAULT 0
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS seen_articles (
                    url_hash TEXT PRIMARY KEY,
                    source TEXT,
                    title TEXT,
                    first_seen TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_seen_first_seen
                    ON seen_articles(first_seen)
            """)

    def save_article(self, title, link, source, published):
        """Speichert einen Artikel. Gibt True zurueck, wenn er neu war."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO articles
                (title, link, source, published, first_seen)
                VALUES (?, ?, ?, ?, ?)
            """, (title, link, source, published, datetime.now().isoformat()))
            conn.commit()
            return cursor.rowcount > 0

    def is_seen(self, link):
        """True, wenn diese URL bereits klassifiziert/verarbeitet wurde."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT 1 FROM seen_articles WHERE url_hash = ? LIMIT 1",
                (self._url_hash(link),)
            ).fetchone()
            return row is not None

    def mark_seen(self, link, source, title):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR IGNORE INTO seen_articles
                (url_hash, source, title, first_seen)
                VALUES (?, ?, ?, ?)
            """, (
                self._url_hash(link), source, title[:200],
                datetime.now().isoformat(),
            ))
            conn.commit()

    @staticmethod
    def _url_hash(url):
        return hashlib.sha1((url or "").encode("utf-8")).hexdigest()[:16]

    def prune_seen(self, max_age_days=7):
        """Loescht alte Eintraege aus seen_articles. Gibt die Anzahl zurueck."""
        cutoff = (datetime.now() - timedelta(days=max_age_days)).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM seen_articles WHERE first_seen < ?",
                (cutoff,)
            )
            conn.commit()
            return cursor.rowcount
