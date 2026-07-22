"""test_notifications.py - Telegram-Versand mit Mock testen (Kapitel 14.4)."""

import notifications


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self.ok = status_code == 200
        self._payload = payload or {"ok": True}

    def json(self):
        return self._payload

    def raise_for_status(self):
        if not self.ok:
            raise Exception(f"HTTP {self.status_code}")


def test_send_telegram_erfolg(monkeypatch):
    def fake_post(url, json, timeout):
        return FakeResponse(200, {"ok": True})

    monkeypatch.setattr(notifications.requests, "post", fake_post)
    result = notifications.send_telegram("TOKEN", "CHAT_ID", "Testnachricht")
    assert result["ok"] is True


def test_build_alert_message_escaped():
    signal = {
        "title": "EngineAI <script> Test",
        "source": "Heise",
        "key_findings": ["Fund 1"],
        "action_required": "watch",
        "source_url": "https://example.com",
    }
    message = notifications.build_alert_message(signal)
    assert "<script>" not in message
    assert "&lt;script&gt;" in message
