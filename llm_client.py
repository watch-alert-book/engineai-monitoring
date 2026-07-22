"""llm_client.py - LLM-Klassifikation mit Fallback (Kapitel 9)."""

import json
import logging
import re

import requests

SYSTEM_PROMPT = """Du bist ein präziser Klassifikations-Assistent. Antworte
AUSSCHLIESSLICH mit gültigem JSON, ohne Markdown, ohne Codeblöcke, ohne
Erklärungen ausserhalb des JSON. Wenn du unsicher bist, setze confidence
auf 0.0 und is_ipo_related auf false."""


def parse_json_response(text):
    """Extrahiert JSON aus einer LLM-Antwort, robust gegen Markdown-Wrapper
    und Prosa drumherum (Kapitel 9.3)."""
    # Versuch 1: Direkt parsen
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Versuch 2: Markdown-Codeblöcke entfernen
    cleaned = re.sub(r"```json\s*", "", text)
    cleaned = re.sub(r"```\s*", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Versuch 3: Erstes {...}-Objekt extrahieren
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    # Versuch 4: Aufgeben
    raise ValueError(f"Konnte kein JSON extrahieren aus: {text[:200]}")


def call_openai_compatible(api_key, base_url, model, prompt, system=None):
    """Ruft ein OpenAI-kompatibles Chat-API auf (Kapitel 9.4).

    api_key / base_url / model kommen vom LLM-Provider deiner Wahl - siehe
    dessen Dashboard/Doku (Kapitel 9.4 erklaert, wo du sie findest).
    """
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = requests.post(
        f"{base_url.rstrip('/')}/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 500,
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def call_ollama(model, prompt, system=None, base_url="http://localhost:11434"):
    """Ruft einen lokalen Ollama-Server auf (Kapitel 9.5)."""
    full_prompt = (system + "\n\n" if system else "") + prompt
    response = requests.post(
        f"{base_url}/api/generate",
        json={
            "model": model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": 500,
            },
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["response"]


def fallback_keyword_analysis(content):
    """Fallback: einfache Keyword-Heuristik ohne LLM (Kapitel 9.6)."""
    content_lower = content.lower()

    if "engineai" not in content_lower and "engine ai" not in content_lower:
        return {
            "is_ipo_related": False,
            "confidence": 0.0,
            "key_findings": [],
            "action_required": "none",
            "notes": "Marke nicht erwähnt",
        }

    buy_kw = ["ticker symbol", "shares available", "now trading",
              "aktien handelbar", "börsenstart"]
    update_kw = ["filed for", "ipo filing", "submitted prospectus",
                 "börsenantrag", "going public"]
    watch_kw = ["ipo plans", "considering ipo", "exploring ipo",
                "möglicher börsengang"]

    if any(kw in content_lower for kw in buy_kw):
        action = "buy"
    elif any(kw in content_lower for kw in update_kw):
        action = "update"
    elif any(kw in content_lower for kw in watch_kw):
        action = "watch"
    else:
        action = "none"

    return {
        "is_ipo_related": action != "none",
        "confidence": 0.7 if action != "none" else 0.0,
        "key_findings": ["Keyword-Heuristik (LLM-Fallback)"],
        "action_required": action,
        "notes": "Erkennung ohne LLM",
    }


class LLMClient:
    """Universeller LLM-Client mit Fallback (Kapitel 9.7)."""

    def __init__(self, provider="openai", api_key="", model="",
                 base_url="", timeout=30):
        self.provider = provider
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.timeout = timeout

    def classify(self, content: str) -> dict:
        """Klassifiziert einen Artikel. Nutzt LLM, fällt sonst auf Keywords zurück."""
        if self.provider == "none":
            return fallback_keyword_analysis(content)

        try:
            text = self._call_llm(content)
            result = parse_json_response(text)
            if not isinstance(result, dict):
                raise ValueError("Antwort ist kein Dict")
            if "is_ipo_related" not in result:
                raise ValueError("Pflichtfeld fehlt")
            return result
        except Exception as e:
            logging.error(f"LLM-Aufruf fehlgeschlagen: {e}, nutze Fallback")
            return fallback_keyword_analysis(content)

    def _call_llm(self, content):
        if self.provider == "ollama":
            return call_ollama(self.model, content,
                                system=SYSTEM_PROMPT,
                                base_url=self.base_url)
        elif self.provider == "openai":
            return call_openai_compatible(
                self.api_key, self.base_url, self.model,
                content, system=SYSTEM_PROMPT,
            )
        raise ValueError(f"Unbekannter Provider: {self.provider}")
