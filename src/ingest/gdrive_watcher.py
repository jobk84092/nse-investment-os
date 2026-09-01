"""Google Drive change watcher.

Polls a configured Drive folder and emits a document_uploaded event for files
not previously seen. Google credentials are local-only and must never be
committed.
"""
from __future__ import annotations
import json
from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from src.core.event_store import emit_event

STATE=Path("data/state/gdrive_seen.json")

def _load_state():
    if STATE.exists(): return set(json.loads(STATE.read_text()))
    return set()

def _save_state(ids):
    STATE.parent.mkdir(parents=True, exist_ok=True); STATE.write_text(json.dumps(sorted(ids)))

def run(cfg: dict) -> list[dict]:
    if not cfg.get("enabled") or not cfg.get("folder_id"): return []
    creds=Credentials.from_authorized_user_file(cfg.get("token_path","gdrive_token.json"))
    service=build("drive","v3",credentials=creds,cache_discovery=False)
    folder=cfg["folder_id"]
    q=f"'{folder}' in parents and trashed=false"
    items=service.files().list(q=q,fields="files(id,name,mimeType,modifiedTime,webViewLink,size)",orderBy="modifiedTime desc").execute().get("files",[])
    seen=_load_state(); emitted=[]
    for item in items:
        if item["id"] in seen: continue
        emitted.append(emit_event({
            "source":"google_drive","type":"document_uploaded",
            "file_id":item["id"],"file_name":item["name"],"mime_type":item.get("mimeType"),
            "modified_time":item.get("modifiedTime"),"url":item.get("webViewLink"),
            "requires_review":True
        }))
        seen.add(item["id"])
    _save_state(seen)
    return emitted
