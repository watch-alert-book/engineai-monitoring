"""rss_sources.py - Datenbeschaffung: RSS, Google News, Retry (Kapitel 7)."""

import logging
import time
from urllib.parse import quote

import feedparser
import requests


def fetch_with_retry(url, max_retries=3, timeout=10):
    """Holt einen Feed mit bis zu max_retries Versuchen und
    Exponential Backoff (Kapitel 7.3).

    Hinweis: feedparser.parse() selbst hat KEIN timeout-Argument (das war
    ein Bug in einer frueheren Buchfassung). Stattdessen holen wir den
    Feed-Inhalt ueber requests mit echtem Timeout und reichen die fertigen
    Bytes an feedparser.parse() weiter.
    """
    for attempt in range(max_retries):
        try:
            response = requests.get(
                url,
                timeout=timeout,
                headers={"User-Agent": "Mozilla/5.0 (compatible; EngineAI-Watcher/1.0)"},
            )
            response.raise_for_status()
            feed = feedparser.parse(response.content)
            if not feed.bozo and feed.entries:
                return feed
            logging.warning(f"Versuch {attempt + 1}: Feed leer oder bozo")
        except Exception as e:
            logging.error(f"Versuch {attempt + 1}: {e}")
        if attempt < max_retries - 1:
            wait = 2 ** attempt  # 1, 2, 4 Sekunden
            logging.info(f"Warte {wait}s vor nächstem Versuch")
            time.sleep(wait)
    logging.error(f"Feed nach {max_retries} Versuchen aufgegeben")
    return None


def build_google_news_url(query, language="de", country="DE"):
    """Baut die Google-News-RSS-URL für eine Suchanfrage (Kapitel 7.5)."""
    return (
        f"https://news.google.com/rss/search?"
        f"q={quote(query)}&hl={language}&gl={country}&ceid={country}:{language}"
    )


def fetch_all_sources(sources):
    """Holt Artikel von allen konfigurierten Quellen und gibt eine
    flache Liste zurück (Kapitel 7.6)."""
    all_articles = []
    for source in sources:
        feed = fetch_with_retry(source["url"])
        if feed is None:
            logging.warning(f"Quelle '{source['name']}' nicht erreichbar")
            continue
        for entry in feed.entries[:source.get("max_articles", 20)]:
            all_articles.append({
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "summary": entry.get("summary", ""),
                "source": source["name"],
                "published": entry.get("published", ""),
            })
    return all_articles
