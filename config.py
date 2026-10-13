"""App-wide constants. Kept tiny for the UI-only phase."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP_NAME = "ReceiptOwl"
SUPPORTED_FILE_TYPES = [".pdf", ".jpg", ".jpeg", ".png"]
SCREENS = ("nest", "hunt", "perch", "treasure", "settings")
