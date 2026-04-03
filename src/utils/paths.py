from pathlib import Path
import json

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_FILE = PROJECT_ROOT / "config" / "settings.json"
DATA_MANUAL = PROJECT_ROOT / "data" / "manual"
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR = PROJECT_ROOT / "output"
ALERTS_DIR = OUTPUT_DIR / "alerts"

def settings() -> dict:
    return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
