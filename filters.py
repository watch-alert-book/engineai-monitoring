"""filters.py - Filter-Pipeline: Brand-Check, Keywords, Zeit, Dedup
(Kapitel 7 und 10)."""

import re
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime


def brand_present(article, brands=("engineai", "engine ai", "engineai robotics")):
    """True, wenn mindestens eine Marken-Variante im Titel/Summary vorkommt.

    Deckt Schreibvarianten wie 'Engine AI' ab, die eine einzelne
    Zeichenkette wie 'engineai' verpassen wuerde (siehe Kapitel 7.4).
    """
    blob = f"{article.get('title', '')} {article.get('summary', '')}".lower()
    return any(b.lower() in blob for b in brands)


def keyword_match(text, keyword):
    """True, wenn keyword als GANZES Wort in text vorkommt (Kapitel 10.4)."""
    pattern = r"\b" + re.escape(keyword.lower()) + r"\b"
    return bool(re.search(pattern, text.lower()))


def keyword_score(content):
    """Berechnet einen einfachen IPO-Relevanz-Score (Kapitel 10.3)."""
    content_lower = content.lower()

    buy_kw = ["ticker symbol", "shares available", "now trading",
              "aktien handelbar", "börsenstart"]
    update_kw = ["filed for", "ipo filing", "submitted prospectus",
                 "listing application", "go public"]
    watch_kw = ["ipo plans", "considering ipo", "exploring ipo",
                "möglicher börsengang"]

    buy_score = sum(1 for kw in buy_kw if kw in content_lower)
    update_score = sum(1 for kw in update_kw if kw in content_lower)
    watch_score = sum(1 for kw in watch_kw if kw in content_lower)

    if buy_score > 0:
        return "buy", max(buy_score, 1)
    if update_score > 0:
        return "update", max(update_score, 1)
    if watch_score > 0:
        return "watch", max(watch_score, 1)
    return "none", 0


def is_fresh(article, max_age_days=2):
    """True, wenn der Artikel juenger als max_age_days Tage ist (Kapitel 10.5)."""
    published = article.get("published", "")
    if not published:
        return True  # Kein Datum = nicht aussortieren

    try:
        pub_dt = parsedate_to_datetime(published)
    except (TypeError, ValueError):
        return True  # Datum unparsbar = nicht aussortieren

    age = datetime.now(pub_dt.tzinfo) - pub_dt
    return age <= timedelta(days=max_age_days)


def filter_pipeline(article, db, max_age_days=2):
    """Filtert einen Artikel durch alle Stufen (Kapitel 10.7).

    Gibt den (angereicherten) Artikel zurueck, oder None, wenn er
    rausgefiltert wurde. `db` ist eine database.DatabaseManager-Instanz.
    """
    # Stufe 1: Brand-Present-Check
    if not brand_present(article):
        return None

    # Stufe 2: Zeit-Filter
    if not is_fresh(article, max_age_days):
        return None

    # Stufe 3: URL-Deduplizierung
    link = article.get("link", "")
    if not link or db.is_seen(link):
        return None

    # Stufe 4: Keyword-Heuristik
    content = f"{article.get('title', '')} {article.get('summary', '')}"
    action, kw_score = keyword_score(content)
    if action == "none":
        return None

    # Alles bestanden - Artikel ist ein Kandidat für die LLM-Klassifikation
    article["_heuristic_action"] = action
    article["_heuristic_score"] = kw_score
    return article
