"""test_database.py - Testet DatabaseManager mit einer temporaeren Datei
(Kapitel 14.5)."""

import pytest

from database import DatabaseManager


@pytest.fixture
def db(tmp_path):
    db_path = tmp_path / "test_watcher.db"
    return DatabaseManager(str(db_path))


def test_save_article_neu(db):
    ist_neu = db.save_article("Titel", "https://example.com/1", "Heise", "2026-07-21")
    assert ist_neu is True


def test_save_article_duplikat(db):
    db.save_article("Titel", "https://example.com/1", "Heise", "2026-07-21")
    ist_neu = db.save_article("Titel", "https://example.com/1", "Heise", "2026-07-21")
    assert ist_neu is False


def test_is_seen_nach_mark_seen(db):
    link = "https://example.com/2"
    assert db.is_seen(link) is False
    db.mark_seen(link, "Heise", "Titel")
    assert db.is_seen(link) is True
