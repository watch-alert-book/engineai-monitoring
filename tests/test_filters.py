"""test_filters.py - Unit-Tests fuer die Filterfunktionen (Kapitel 14.3)."""

from filters import brand_present, keyword_match


def test_brand_present_treffer():
    article = {"title": "EngineAI eröffnet neue Fabrik", "summary": ""}
    assert brand_present(article) is True


def test_brand_present_schreibvariante_mit_leerzeichen():
    article = {"title": "Engine AI eröffnet neue Fabrik", "summary": ""}
    assert brand_present(article) is True


def test_brand_present_kein_treffer():
    article = {"title": "Ein Artikel über etwas anderes", "summary": ""}
    assert brand_present(article) is False


def test_keyword_match_wortgrenze():
    assert keyword_match("KI überrascht die Branche", "ki") is True
    assert keyword_match("KITA eröffnet neue Stellen", "ki") is False
