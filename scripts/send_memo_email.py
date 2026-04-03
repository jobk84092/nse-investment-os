#!/usr/bin/env python3
"""
Send pipeline outputs: SMTP (app password) or Gmail API (OAuth), configurable.

Loads nse_investment_os/.email_env into the process environment when present
(UTF-8 BOM safe). Does not override variables already set in the environment.
"""
from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import re
import smtplib
import ssl
from datetime import date
from email import policy
from email.message import EmailMessage
from pathlib import Path

from googleapiclient.errors import HttpError

_ROOT = Path(__file__).resolve().parent.parent
_CONFIG = _ROOT / "config" / "settings.json"
_OUTPUT = _ROOT / "output"


def _attachment_path(rel: str) -> Path:
    """Paths under data/ are from project root; others are under output/."""
    r = rel.replace("\\", "/").lstrip("/")
    if r.startswith("data/"):
        return _ROOT / r
    return _OUTPUT / r


def _load_cfg() -> dict:
    return json.loads(_CONFIG.read_text(encoding="utf-8"))


def apply_email_env_file() -> None:
    """Parse .email_env like the shell would; do not override existing os.environ."""
    path = _ROOT / ".email_env"
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8-sig")
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$", line)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        if key in os.environ and os.environ.get(key, "").strip():
            continue
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        os.environ[key] = val


def _env_or(cfg_key: str, default: str = "") -> str:
    return (os.environ.get(cfg_key) or default).strip()


def _gmail_paths(cfg: dict) -> tuple[Path, Path]:
    ga = (cfg.get("email_digest") or {}).get("gmail_api") or {}
    cred = _ROOT / (ga.get("credentials_path") or "credentials.json")
    tok = _ROOT / (ga.get("token_path") or "gmail_send_token.json")
    return cred, tok


def build_message(cfg: dict) -> tuple[EmailMessage, list[str]]:
    ed = cfg.get("email_digest") or {}

    to_addr = (ed.get("to") or cfg.get("alerts", {}).get("recipient_email") or "").strip()
    if not to_addr:
        raise ValueError("No recipient: set email_digest.to or alerts.recipient_email")

    from_addr = (ed.get("from_address") or to_addr).strip()
    sub_tmpl = ed.get("subject_template") or "NSE Investment OS — {date}"
    subject = sub_tmpl.format(date=date.today().isoformat())

    attach_names = ed.get("attachment_files") or [
        "monthly_investment_memo.md",
        "portfolio_snapshot.csv",
        "sector_snapshot.csv",
        "top_ideas.csv",
        "watchlist_rankings.csv",
        "data/raw/telegram_for_commentary.csv",
    ]
    also_alerts = ed.get("attach_alerts_email_summary", True)
    if also_alerts:
        p = _OUTPUT / "alerts" / "email_summary.md"
        if p.is_file():
            attach_names = list(attach_names) + ["alerts/email_summary.md"]

    missing: list[str] = []
    for rel in attach_names:
        path = _attachment_path(rel)
        if not path.is_file():
            missing.append(rel)

    intro = (
        f"NSE Investment OS — generated {date.today().isoformat()}\n\n"
        f"Recipient: {to_addr}\n"
        f"Attachments ({len(attach_names)} planned):\n"
        + "\n".join(f"  - {n}" for n in attach_names)
    )
    if missing:
        intro += "\n\nMissing (skipped):\n" + "\n".join(f"  - {m}" for m in missing)

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg.set_content(intro + "\n\n— Sent by scripts/send_memo_email.py\n")

    attached: list[str] = []
    for rel in attach_names:
        path = _attachment_path(rel)
        if not path.is_file():
            continue
        ctype, _ = mimetypes.guess_type(str(path))
        if ctype is None:
            ctype = "application/octet-stream"
        maintype, subtype = ctype.split("/", 1)
        data = path.read_bytes()
        msg.add_attachment(
            data,
            maintype=maintype,
            subtype=subtype,
            filename=path.name,
        )
        attached.append(rel)

    return msg, attached


def send_smtp(msg: EmailMessage, cfg: dict) -> None:
    ed = cfg.get("email_digest") or {}
    host = (ed.get("smtp_host") or "smtp.gmail.com").strip()
    port = int(ed.get("smtp_port") or 587)
    use_tls = ed.get("smtp_use_tls", True)

    user_key = ed.get("smtp_user_env") or "NSE_INVEST_SMTP_USER"
    pass_key = ed.get("smtp_password_env") or "NSE_INVEST_SMTP_PASSWORD"
    user = _env_or(user_key, ed.get("from_address") or str(msg["From"]))
    password = _env_or(pass_key)

    if not password:
        raise RuntimeError(
            f"Missing SMTP password: set {pass_key} in .email_env or the environment "
            "(Gmail: app password), or use Gmail API (see docs/EMAIL_DIGEST.md)."
        )

    if "gmail" in host.lower():
        password = "".join(password.split())

    context = ssl.create_default_context()
    with smtplib.SMTP(host, port, timeout=45) as server:
        server.ehlo()
        if use_tls:
            server.starttls(context=context)
            server.ehlo()
        server.login(user, password)
        server.send_message(msg)


def send_gmail_api(msg: EmailMessage, cfg: dict) -> None:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    _, tok_path = _gmail_paths(cfg)
    cred_path, _ = _gmail_paths(cfg)

    if not cred_path.is_file():
        raise RuntimeError(
            f"Missing {cred_path}. Add OAuth desktop client JSON, then run scripts/auth_gmail_send.py."
        )

    scopes = ["https://www.googleapis.com/auth/gmail.send"]
    creds = None
    if tok_path.is_file():
        creds = Credentials.from_authorized_user_file(str(tok_path), scopes)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            tok_path.write_text(creds.to_json(), encoding="utf-8")
        else:
            raise RuntimeError(
                "Gmail send token missing or unusable. Run: .venv/bin/python scripts/auth_gmail_send.py"
            )

    raw = base64.urlsafe_b64encode(msg.as_bytes(policy=policy.SMTP)).decode()
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)
    service.users().messages().send(userId="me", body={"raw": raw}).execute()


def _send_with_transport(transport: str, msg: EmailMessage, cfg: dict) -> None:
    ed = cfg.get("email_digest") or {}
    _, tok_path = _gmail_paths(cfg)
    t = (transport or "auto").lower()

    if t == "gmail_api":
        send_gmail_api(msg, cfg)
        return

    if t == "smtp":
        send_smtp(msg, cfg)
        return

    # auto
    if tok_path.is_file():
        try:
            send_gmail_api(msg, cfg)
            return
        except HttpError as e:
            err = str(e)
            if e.resp is not None and e.resp.status == 403 and (
                "accessNotConfigured" in err or "Gmail API has not been used" in err
            ):
                m = re.search(r"project[=/](\d+)", err)
                proj = m.group(1) if m else ""
                link = (
                    f"https://console.cloud.google.com/apis/library/gmail.googleapis.com?project={proj}"
                    if proj
                    else "https://console.cloud.google.com/apis/library/gmail.googleapis.com"
                )
                raise RuntimeError(
                    "Gmail API is turned OFF for this Google Cloud project.\n"
                    f"  1) Open: {link}\n"
                    "  2) Click **Enable**, wait 1–2 minutes, run send again.\n"
                    "(SMTP fallback skipped — your account already rejects app-password SMTP.)"
                ) from e
            print(f"Gmail API send failed ({e}); falling back to SMTP…")
        except Exception as e:
            print(f"Gmail API send failed ({e}); falling back to SMTP…")

    send_smtp(msg, cfg)


def main() -> int:
    ap = argparse.ArgumentParser(description="Email pipeline outputs (SMTP or Gmail API)")
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Show recipient and attachments; do not send",
    )
    ap.add_argument(
        "--force",
        action="store_true",
        help="Send even if email_digest.enabled is false",
    )
    ap.add_argument(
        "--transport",
        choices=("auto", "smtp", "gmail_api"),
        default=None,
        help="Override email_digest.transport (default: from settings)",
    )
    args = ap.parse_args()

    apply_email_env_file()

    cfg = _load_cfg()
    ed = cfg.get("email_digest") or {}
    if not ed.get("enabled") and not args.force:
        print("email_digest.enabled is false; use --force to send anyway.")
        return 0

    try:
        msg, attached = build_message(cfg)
    except ValueError as e:
        print(e)
        return 2

    print("To:", msg["To"])
    print("Subject:", msg["Subject"])
    print("Attachments:", ", ".join(attached) or "(none)")

    if args.dry_run:
        print("Dry run — not sending.")
        return 0

    transport = args.transport or (ed.get("transport") or "auto")

    try:
        _send_with_transport(transport, msg, cfg)
    except Exception as e:
        print("Send failed:", e)
        _, tok = _gmail_paths(cfg)
        if not tok.is_file():
            print(
                "\nIf Gmail keeps rejecting SMTP (535), use OAuth instead:\n"
                "  1. Put credentials.json in nse_investment_os/ (same as other Google desktop apps).\n"
                "  2. .venv/bin/python scripts/auth_gmail_send.py\n"
                "  3. .venv/bin/python scripts/send_memo_email.py --transport gmail_api\n"
            )
        return 1

    print("Sent OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
