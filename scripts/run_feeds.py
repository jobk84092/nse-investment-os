#!/usr/bin/env python3
"""Run all event feeds once and print what changed."""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.ingest.corporate_actions import run as run_nse
from src.ingest.gdrive_watcher import run as run_drive

ROOT=Path(__file__).resolve().parents[1]
settings=json.loads((ROOT/"config/settings.json").read_text())
events=[]
events += run_nse(settings)
events += run_drive(settings.get("google_drive_watcher",{}))
print(json.dumps({"new_events":len(events),"events":events},indent=2,default=str))
