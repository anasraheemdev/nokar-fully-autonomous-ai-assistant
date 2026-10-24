"""
actions/email_manager.py — Autonomous Email Management via SMTP, IMAP & POP3.

Features:
  • Send emails via SMTP (supports SSL port 465 and STARTTLS port 587/25)
  • Read and search emails via IMAP (SSL port 993) or POP3 (SSL port 995)
  • Zero external pip dependencies — uses Python's standard library (smtplib, imaplib, poplib, email)
  • Auto-detects email provider settings (Gmail, Outlook/Hotmail, Yahoo, iCloud, custom)
  • Auto-discovered at startup by core.action_loader as part of JARVIS's core capability set.
"""

from __future__ import annotations

import email
import email.header
import email.utils
import imaplib
import json
import mimetypes
import os
import poplib
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"

PROVIDER_PRESETS = {
    "gmail.com": {
        "smtp_host": "smtp.gmail.com", "smtp_port": 587, "smtp_ssl": False,
        "imap_host": "imap.gmail.com", "imap_port": 993, "imap_ssl": True,
        "pop_host": "pop.gmail.com",   "pop_port": 995,  "pop_ssl": True,
    },
    "googlemail.com": {
        "smtp_host": "smtp.gmail.com", "smtp_port": 587, "smtp_ssl": False,
        "imap_host": "imap.gmail.com", "imap_port": 993, "imap_ssl": True,
        "pop_host": "pop.gmail.com",   "pop_port": 995,  "pop_ssl": True,
    },
    "outlook.com": {
        "smtp_host": "smtp.office365.com", "smtp_port": 587, "smtp_ssl": False,
        "imap_host": "outlook.office365.com", "imap_port": 993, "imap_ssl": True,
        "pop_host": "outlook.office365.com",  "pop_port": 995,  "pop_ssl": True,
    },
    "hotmail.com": {
        "smtp_host": "smtp.office365.com", "smtp_port": 587, "smtp_ssl": False,
        "imap_host": "outlook.office365.com", "imap_port": 993, "imap_ssl": True,
        "pop_host": "outlook.office365.com",  "pop_port": 995,  "pop_ssl": True,
    },
    "live.com": {
        "smtp_host": "smtp.office365.com", "smtp_port": 587, "smtp_ssl": False,
        "imap_host": "outlook.office365.com", "imap_port": 993, "imap_ssl": True,
        "pop_host": "outlook.office365.com",  "pop_port": 995,  "pop_ssl": True,
    },
    "yahoo.com": {
        "smtp_host": "smtp.mail.yahoo.com", "smtp_port": 465, "smtp_ssl": True,
        "imap_host": "imap.mail.yahoo.com", "imap_port": 993, "imap_ssl": True,
        "pop_host": "pop.mail.yahoo.com",  "pop_port": 995,  "pop_ssl": True,
    },
    "icloud.com": {
        "smtp_host": "smtp.mail.me.com", "smtp_port": 587, "smtp_ssl": False,
        "imap_host": "imap.mail.me.com", "imap_port": 993, "imap_ssl": True,
        "pop_host": "pop.mail.me.com",   "pop_port": 995,  "pop_ssl": True,
    },
}


def _load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        return data.get("email", {})
    except Exception:
        return {}


def _save_config(email_cfg: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    all_cfg = {}
    if CONFIG_PATH.exists():
        try:
            all_cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            all_cfg = {}
    current = all_cfg.get("email", {})
    current.update(email_cfg)
    all_cfg["email"] = current
    CONFIG_PATH.write_text(json.dumps(all_cfg, indent=4), encoding="utf-8")


def _get_provider_config(address: str, cfg: dict) -> dict:
    domain = address.split("@")[-1].lower() if "@" in address else ""
    preset = PROVIDER_PRESETS.get(domain, {})
    return {
        "address": address or cfg.get("address", ""),
        "password": cfg.get("password", ""),
        "smtp_host": cfg.get("smtp_host") or preset.get("smtp_host", f"smtp.{domain}"),
        "smtp_port": int(cfg.get("smtp_port") or preset.get("smtp_port", 587)),
        "smtp_ssl": cfg.get("smtp_ssl", preset.get("smtp_ssl", False)),
        "imap_host": cfg.get("imap_host") or preset.get("imap_host", f"imap.{domain}"),
        "imap_port": int(cfg.get("imap_port") or preset.get("imap_port", 993)),
        "imap_ssl": cfg.get("imap_ssl", preset.get("imap_ssl", True)),
        "pop_host": cfg.get("pop_host") or preset.get("pop_host", f"pop.{domain}"),
        "pop_port": int(cfg.get("pop_port") or preset.get("pop_port", 995)),
        "pop_ssl": cfg.get("pop_ssl", preset.get("pop_ssl", True)),
        "protocol": cfg.get("protocol", "imap").lower(),
    }


def _decode_str(header_val: str) -> str:
    if not header_val:
        return ""
    parts = email.header.decode_header(header_val)
    decoded = []
    for b, enc in parts:
        if isinstance(b, bytes):
            decoded.append(b.decode(enc or "utf-8", errors="replace"))
        else:
            decoded.append(str(b))
    return " ".join(decoded)


def _get_body_from_message(msg: email.message.Message) -> str:
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            cdisp = str(part.get("Content-Disposition", ""))
            if ctype == "text/plain" and "attachment" not in cdisp:
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    body = payload.decode(charset, errors="replace")
                    break
            elif ctype == "text/html" and "attachment" not in cdisp and not body:
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    raw_html = payload.decode(charset, errors="replace")
                    import re
                    body = re.sub(r"<[^>]+>", " ", raw_html).strip()
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            body = payload.decode(charset, errors="replace")
    return " ".join(body.split())[:1200]


# ── Core Operations ──────────────────────────────────────────────────────────

def send_email(to: str, subject: str, body: str, attachments: str | list = "") -> str:
    cfg = _load_config()
    address = cfg.get("address", "")
    password = cfg.get("password", "")

    if not address or not password:
        return (
            "Sir, email is not configured yet. Please configure your email address and "
            "password (or app password) using the email_manager configure action."
        )

    pcfg = _get_provider_config(address, cfg)
    smtp_host = pcfg["smtp_host"]
    smtp_port = pcfg["smtp_port"]
    smtp_ssl = pcfg["smtp_ssl"]

    msg = MIMEMultipart()
    msg["From"] = address
    msg["To"] = to
    msg["Subject"] = subject
    msg["Date"] = email.utils.formatdate(localtime=True)
    msg.attach(MIMEText(body, "plain", "utf-8"))

    # Process attachments
    attach_list = []
    if isinstance(attachments, str) and attachments.strip():
        attach_list = [p.strip() for p in attachments.split(",") if p.strip()]
    elif isinstance(attachments, list):
        attach_list = [str(p).strip() for p in attachments if str(p).strip()]

    attached_names = []
    for fpath in attach_list:
        p = Path(fpath).expanduser()
        if not p.exists() or not p.is_file():
            # Try fuzzy search in common places
            from actions.file_controller import _smart_find_file
            found = _smart_find_file(fpath)
            if found:
                p = found
        if p.exists() and p.is_file():
            ctype, encoding = mimetypes.guess_type(str(p))
            if ctype is None or encoding is not None:
                ctype = "application/octet-stream"
            maintype, subtype = ctype.split("/", 1)
            with open(p, "rb") as f:
                part = MIMEBase(maintype, subtype)
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f'attachment; filename="{p.name}"')
            msg.attach(part)
            attached_names.append(p.name)

    try:
        if smtp_ssl:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=15)
            server.ehlo()
            server.starttls()
            server.ehlo()

        server.login(address, password)
        recipients = [r.strip() for r in to.split(",") if r.strip()]
        server.sendmail(address, recipients, msg.as_string())
        server.quit()

        att_str = f" with {len(attached_names)} attachment(s)" if attached_names else ""
        return f"Email sent successfully to {to} (Subject: '{subject}'){att_str}."
    except smtplib.SMTPAuthenticationError:
        return (
            "Authentication failed. For Gmail, Yahoo, or Outlook, you must generate "
            "an App Password in your account security settings rather than your standard login password."
        )
    except Exception as e:
        return f"Failed to send email via {smtp_host}:{smtp_port}: {e}"


def read_emails_imap(cfg: dict, pcfg: dict, folder: str = "INBOX", max_count: int = 5, unread_only: bool = True) -> str:
    address = pcfg["address"]
    password = pcfg["password"]
    host = pcfg["imap_host"]
    port = pcfg["imap_port"]
    use_ssl = pcfg["imap_ssl"]

    try:
        mail = imaplib.IMAP4_SSL(host, port) if use_ssl else imaplib.IMAP4(host, port)
        mail.login(address, password)
        mail.select(folder, readonly=True)

        criteria = "UNSEEN" if unread_only else "ALL"
        status, data = mail.search(None, criteria)
        if status != "OK":
            mail.logout()
            return f"Could not search folder '{folder}'."

        mail_ids = data[0].split()
        if not mail_ids:
            mail.logout()
            return f"No {'unread ' if unread_only else ''}emails found in {folder}."

        recent_ids = mail_ids[-max_count:][::-1]
        summaries = []

        for mid in recent_ids:
            st, msg_data = mail.fetch(mid, "(RFC822.HEADER BODY.PEEK[TEXT])")
            if st != "OK":
                continue
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject = _decode_str(msg.get("Subject", "(No Subject)"))
                    sender = _decode_str(msg.get("From", "(Unknown Sender)"))
                    date = msg.get("Date", "")
                    body = _get_body_from_message(msg)
                    snip = (body[:160] + "...") if len(body) > 160 else body
                    summaries.append(f"📧 From: {sender}\n   Subject: {subject}\n   Date: {date}\n   Preview: {snip}")

        mail.logout()
        return f"Latest {len(summaries)} email(s) in {folder}:\n\n" + "\n\n".join(summaries)
    except Exception as e:
        return f"IMAP read error ({host}): {e}"


def read_emails_pop(cfg: dict, pcfg: dict, max_count: int = 5) -> str:
    address = pcfg["address"]
    password = pcfg["password"]
    host = pcfg["pop_host"]
    port = pcfg["pop_port"]
    use_ssl = pcfg["pop_ssl"]

    try:
        pop = poplib.POP3_SSL(host, port, timeout=15) if use_ssl else poplib.POP3(host, port, timeout=15)
        pop.user(address)
        pop.pass_(password)

        num_messages = len(pop.list()[1])
        if num_messages == 0:
            pop.quit()
            return "Inbox is empty (POP3)."

        start = max(1, num_messages - max_count + 1)
        summaries = []

        for i in range(num_messages, start - 1, -1):
            raw_lines = pop.retr(i)[1]
            raw_email = b"\r\n".join(raw_lines)
            msg = email.message_from_bytes(raw_email)
            subject = _decode_str(msg.get("Subject", "(No Subject)"))
            sender = _decode_str(msg.get("From", "(Unknown Sender)"))
            date = msg.get("Date", "")
            body = _get_body_from_message(msg)
            snip = (body[:160] + "...") if len(body) > 160 else body
            summaries.append(f"📧 From: {sender}\n   Subject: {subject}\n   Date: {date}\n   Preview: {snip}")

        pop.quit()
        return f"Latest {len(summaries)} POP3 email(s):\n\n" + "\n\n".join(summaries)
    except Exception as e:
        return f"POP3 read error ({host}): {e}"


def read_emails(folder: str = "INBOX", max_count: int = 5, unread_only: bool = True) -> str:
    cfg = _load_config()
    address = cfg.get("address", "")
    password = cfg.get("password", "")

    if not address or not password:
        return (
            "Sir, email is not configured yet. Please configure your email address and "
            "password using the email_manager configure action."
        )

    pcfg = _get_provider_config(address, cfg)
    if pcfg["protocol"] == "pop":
        return read_emails_pop(cfg, pcfg, max_count=max_count)
    return read_emails_imap(cfg, pcfg, folder=folder, max_count=max_count, unread_only=unread_only)


def search_emails(query: str, max_count: int = 5) -> str:
    cfg = _load_config()
    address = cfg.get("address", "")
    password = cfg.get("password", "")

    if not address or not password:
        return "Sir, email is not configured yet."

    pcfg = _get_provider_config(address, cfg)
    host = pcfg["imap_host"]
    port = pcfg["imap_port"]
    use_ssl = pcfg["imap_ssl"]

    try:
        mail = imaplib.IMAP4_SSL(host, port) if use_ssl else imaplib.IMAP4(host, port)
        mail.login(address, password)
        mail.select("INBOX", readonly=True)

        # Search subject, body, or from
        status, data = mail.search(None, f'(OR (FROM "{query}") (SUBJECT "{query}"))')
        if status != "OK" or not data[0]:
            # Fallback search
            status, data = mail.search(None, f'TEXT "{query}"')

        mail_ids = data[0].split() if status == "OK" and data[0] else []
        if not mail_ids:
            mail.logout()
            return f"No emails found matching query '{query}'."

        recent_ids = mail_ids[-max_count:][::-1]
        summaries = []

        for mid in recent_ids:
            st, msg_data = mail.fetch(mid, "(RFC822.HEADER BODY.PEEK[TEXT])")
            if st != "OK":
                continue
            for part in msg_data:
                if isinstance(part, tuple):
                    msg = email.message_from_bytes(part[1])
                    subject = _decode_str(msg.get("Subject", "(No Subject)"))
                    sender = _decode_str(msg.get("From", "(Unknown Sender)"))
                    body = _get_body_from_message(msg)
                    snip = (body[:140] + "...") if len(body) > 140 else body
                    summaries.append(f"📧 From: {sender} | Subject: {subject}\n   {snip}")

        mail.logout()
        return f"Found {len(summaries)} email(s) for '{query}':\n\n" + "\n\n".join(summaries)
    except Exception as e:
        return f"Email search error: {e}"


def configure_email(
    address: str,
    password: str = "",
    smtp_host: str = "",
    smtp_port: int = 0,
    imap_host: str = "",
    imap_port: int = 0,
    pop_host: str = "",
    pop_port: int = 0,
    protocol: str = "imap",
) -> str:
    """Save email configuration parameters into config/api_keys.json."""
    if not address or "@" not in address:
        return "Please provide a valid email address."

    data = {"address": address.strip()}
    if password:
        data["password"] = password.strip()
    if smtp_host:
        data["smtp_host"] = smtp_host.strip()
    if smtp_port > 0:
        data["smtp_port"] = smtp_port
    if imap_host:
        data["imap_host"] = imap_host.strip()
    if imap_port > 0:
        data["imap_port"] = imap_port
    if pop_host:
        data["pop_host"] = pop_host.strip()
    if pop_port > 0:
        data["pop_port"] = pop_port
    if protocol in ("imap", "pop"):
        data["protocol"] = protocol.lower()

    _save_config(data)
    domain = address.split("@")[-1].lower()
    return f"Email configured for {address} ({domain}). Settings saved to config/api_keys.json."


# ── Action Dispatcher ────────────────────────────────────────────────────────

def email_manager(parameters: dict = None, player=None, session_memory=None) -> str:
    params = parameters or {}
    action = params.get("action", "").lower().strip()

    if player:
        player.write_log(f"[email] action: {action}")

    if action == "send":
        return send_email(
            to=params.get("to", ""),
            subject=params.get("subject", "(No Subject)"),
            body=params.get("body", ""),
            attachments=params.get("attachments", ""),
        )
    elif action in ("read", "check_inbox", "list"):
        return read_emails(
            folder=params.get("folder", "INBOX"),
            max_count=int(params.get("max_count", 5)),
            unread_only=bool(params.get("unread_only", True)),
        )
    elif action == "search":
        return search_emails(
            query=params.get("query", ""),
            max_count=int(params.get("max_count", 5)),
        )
    elif action == "configure":
        return configure_email(
            address=params.get("address", ""),
            password=params.get("password", ""),
            smtp_host=params.get("smtp_host", ""),
            smtp_port=int(params.get("smtp_port", 0)),
            imap_host=params.get("imap_host", ""),
            imap_port=int(params.get("imap_port", 0)),
            pop_host=params.get("pop_host", ""),
            pop_port=int(params.get("pop_port", 0)),
            protocol=params.get("protocol", "imap"),
        )
    else:
        return f"Unknown email action: '{action}'. Available: send | read | search | configure"


# ── Tool Declaration (auto-discovered by core/action_loader.py) ──────────────
TOOL = {
    "name": "email_manager",
    "description": (
        "Universal email management via SMTP, IMAP, and POP3. "
        "Allows sending emails with optional attachments, reading unread messages from the inbox, "
        "searching past email threads, and configuring email credentials. "
        "Supports Gmail, Outlook/Hotmail, Yahoo, iCloud, and custom SMTP/POP/IMAP servers."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "send | read | search | configure"
            },
            "to": {
                "type": "STRING",
                "description": "Recipient email address(es), comma-separated for send"
            },
            "subject": {
                "type": "STRING",
                "description": "Email subject line"
            },
            "body": {
                "type": "STRING",
                "description": "Email body content"
            },
            "attachments": {
                "type": "STRING",
                "description": "Optional file path(s) to attach (comma-separated)"
            },
            "folder": {
                "type": "STRING",
                "description": "Mailbox folder to read from (default: INBOX)"
            },
            "unread_only": {
                "type": "BOOLEAN",
                "description": "True to read only unread messages, False for all latest"
            },
            "max_count": {
                "type": "INTEGER",
                "description": "Maximum number of emails to retrieve (default: 5)"
            },
            "query": {
                "type": "STRING",
                "description": "Search keyword, sender name, or subject to search for"
            },
            "address": {
                "type": "STRING",
                "description": "User email address for configure"
            },
            "password": {
                "type": "STRING",
                "description": "User email app password or token for configure"
            },
            "protocol": {
                "type": "STRING",
                "description": "Incoming mail protocol: imap or pop (default: imap)"
            }
        },
        "required": ["action"]
    },
    "handler": email_manager,
}
