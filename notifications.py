"""notifications.py - Telegram, ntfy.sh, E-Mail und Multi-Channel-Versand
(Kapitel 11)."""

import html
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests


def escape_html(text):
    """Escapt HTML-Steuerzeichen in einem Text (Kapitel 11.3)."""
    return html.escape(str(text), quote=True)


def build_alert_message(signal):
    """Baut eine formatierte Alert-Nachricht (Kapitel 11.4)."""
    title = escape_html(signal.get("title", ""))
    source = escape_html(signal.get("source", "unbekannt"))

    findings = signal.get("key_findings", [])
    findings_html = "".join(
        f"  - {escape_html(f)}\n" for f in findings[:5]
    )

    action = signal.get("action_required", "watch")
    action_label = action.upper()

    return (
        f"<b>{action_label}: {title}</b>\n"
        f"\n"
        f"<i>Quelle: {source}</i>\n"
        f"\n"
        f"<b>Erkenntnisse:</b>\n{findings_html}\n"
        f"\n"
        f"<a href='{signal.get('source_url', '')}'>Artikel öffnen</a>"
    )


def send_telegram(token, chat_id, message, parse_mode=None):
    """Schickt eine Nachricht per Telegram (Kapitel 11.2/11.3).

    parse_mode="HTML" ist noetig, damit <b>/<i>/<a>-Tags aus
    build_alert_message() auch tatsaechlich als Formatierung ankommen.
    """
    payload = {"chat_id": chat_id, "text": message}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    response = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json=payload,
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def send_ntfy(topic, message, server="https://ntfy.sh", title=None, priority=3):
    """Schickt eine Push-Nachricht via ntfy.sh (Kapitel 11.5).

    Hinweis: Falls ntfy.sh bei dir nicht erreichbar ist, ist das haeufig
    ein DNS-Filter (AdGuard DNS/Pi-hole/NextDNS), nicht ein Ausfall des
    Dienstes - siehe Kapitel 11.5 im Buch.
    """
    headers = {"Priority": str(priority)}
    if title:
        headers["Title"] = title
    response = requests.post(
        f"{server}/{topic}",
        data=message.encode("utf-8"),
        headers=headers,
        timeout=10,
    )
    response.raise_for_status()
    return response.status_code == 200


def send_email(smtp_server, smtp_port, username, password,
               from_addr, to_addrs, subject, body):
    """Verschickt eine E-Mail über SMTP mit STARTTLS (Kapitel 11.6).

    Fuer Gmail: username/password sind NICHT dein normales Passwort,
    sondern ein App-Passwort (siehe Kapitel 11.6 im Buch).
    """
    msg = MIMEMultipart()
    msg["From"] = from_addr
    msg["To"] = ", ".join(to_addrs)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(username, password)
        server.send_message(msg)


def send_alert(signal, config):
    """Sendet eine Benachrichtigung über alle aktivierten Kanäle
    (Kapitel 11.7): Telegram primär, ntfy als Fallback, E-Mail parallel."""
    telegram_ok = False

    if config.get("telegram", {}).get("enabled"):
        try:
            send_telegram(
                token=config["telegram"]["bot_token"],
                chat_id=config["telegram"]["chat_id"],
                message=build_alert_message(signal),
                parse_mode="HTML",
            )
            telegram_ok = True
        except Exception as e:
            logging.error(f"Telegram fehlgeschlagen: {e}")

    if not telegram_ok and config.get("ntfy", {}).get("enabled"):
        try:
            send_ntfy(
                topic=config["ntfy"]["topic"],
                message=build_alert_message(signal),  # Plain Text/HTML-Tags sichtbar
                title=f"{signal.get('title', 'Alert')[:60]}",
                priority=5,
            )
        except Exception as e:
            logging.error(f"ntfy fehlgeschlagen: {e}")

    if config.get("email", {}).get("enabled"):
        try:
            email_cfg = config["email"]
            send_email(
                smtp_server=email_cfg["smtp_server"],
                smtp_port=email_cfg["smtp_port"],
                username=email_cfg["username"],
                password=email_cfg["password"],
                from_addr=email_cfg["from_addr"],
                to_addrs=email_cfg["to_addrs"],
                subject=f"[IPO-Watch] {signal.get('title', '')[:60]}",
                body=build_alert_message(signal),
            )
        except Exception as e:
            logging.error(f"E-Mail fehlgeschlagen: {e}")

    return telegram_ok
