"""Append-only JSONL event store shared by watchers and analysis agents."""
from __future__ import annotations
import json, hashlib
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_EVENTS = Path("data/events/events.jsonl")

def _fingerprint(event: dict) -> str:
    stable = {k:v for k,v in event.items() if k not in {"event_id","observed_at"}}
    return hashlib.sha256(json.dumps(stable, sort_keys=True, default=str).encode()).hexdigest()

def emit_event(event: dict, path: str | Path = DEFAULT_EVENTS) -> dict:
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    event = dict(event)
    event.setdefault("observed_at", datetime.now(timezone.utc).isoformat())
    event.setdefault("event_id", _fingerprint(event)[:24])
    existing = set()
    if path.exists():
        with path.open(encoding="utf-8") as f:
            for line in f:
                try: existing.add(json.loads(line).get("event_id"))
                except json.JSONDecodeError: pass
    if event["event_id"] not in existing:
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, default=str) + "\n")
    return event

def events_since(iso_timestamp: str | None = None, path: str | Path = DEFAULT_EVENTS) -> list[dict]:
    path = Path(path)
    if not path.exists(): return []
    out=[]
    with path.open(encoding="utf-8") as f:
        for line in f:
            try:
                e=json.loads(line)
                if not iso_timestamp or e.get("observed_at","") > iso_timestamp: out.append(e)
            except json.JSONDecodeError: continue
    return out
