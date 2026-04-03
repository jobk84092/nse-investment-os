#!/usr/bin/env python3
"""
One-time (or rare) OAuth setup for sending mail via Gmail API.

Uses the same OAuth client JSON as other Google desktop apps: save as
nse_investment_os/credentials.json (gitignored). Enable "Gmail API" in Google Cloud.

Scopes: gmail.send only (not full mailbox access).
"""
from __future__ import annotations

import json
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

_ROOT = Path(__file__).resolve().parent.parent
_CONFIG = _ROOT / "config" / "settings.json"
_SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def _token_path() -> Path:
    cfg = json.loads(_CONFIG.read_text(encoding="utf-8"))
    ga = (cfg.get("email_digest") or {}).get("gmail_api") or {}
    return _ROOT / (ga.get("token_path") or "gmail_send_token.json")


def _credentials_path() -> Path:
    cfg = json.loads(_CONFIG.read_text(encoding="utf-8"))
    ga = (cfg.get("email_digest") or {}).get("gmail_api") or {}
    return _ROOT / (ga.get("credentials_path") or "credentials.json")


def main() -> int:
    cred_path = _credentials_path()
    if not cred_path.is_file():
        print(f"Missing OAuth client file: {cred_path}")
        print("Download JSON from Google Cloud → APIs & Services → Credentials → OAuth 2.0 Client (Desktop).")
        return 2

    flow = InstalledAppFlow.from_client_secrets_file(str(cred_path), _SCOPES)
    creds = flow.run_local_server(port=0)
    out = _token_path()
    out.write_text(creds.to_json(), encoding="utf-8")
    print(f"Saved Gmail send token to {out}")
    print("You can run scripts/send_memo_email.py with transport auto or gmail_api.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
