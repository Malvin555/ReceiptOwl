from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP_NAME = "ReceiptOwl"
SUPPORTED_FILE_TYPES = [".pdf", ".jpg", ".jpeg", ".png"]
SCREENS = ("nest", "hunt", "perch", "treasure", "settings")

OLLAMA_HOST = "http://127.0.0.1:11434"
MODEL_OPTIONS = ["gemma2:2b", "qwen2.5:3b", "llama3.2:3b"]
DEFAULT_MODEL = MODEL_OPTIONS[0]

CONFIDENCE_GREEN = 85
CONFIDENCE_AMBER = 70

_STATE_FILE = ROOT / ".receiptowl_state.json"
_DEFAULT_STORAGE = Path.home() / "Documents" / "ReceiptOwl"


def get_storage_root() -> Path:
    chosen = _DEFAULT_STORAGE
    if _STATE_FILE.exists():
        try:
            saved = json.loads(_STATE_FILE.read_text(encoding="utf-8")).get(
                "storage_root"
            )
            if saved:
                chosen = Path(saved)
        except (OSError, ValueError):
            pass

    try:
        chosen.mkdir(parents=True, exist_ok=True)
        probe = chosen / ".write_test"
        probe.touch()
        probe.unlink()
        return chosen
    except OSError:
        fallback = ROOT / "data"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def set_storage_root(path: Path) -> None:
    """Remember a new workspace location. Does not move existing data."""
    _STATE_FILE.write_text(json.dumps({"storage_root": str(path)}), encoding="utf-8")
