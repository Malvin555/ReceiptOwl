from __future__ import annotations

import platform
import subprocess
from datetime import date
from pathlib import Path

from database.db import get_storage_root, originals_dir, reports_dir


def period_label(d: date | None = None) -> str:
    d = d or date.today()
    quarter = (d.month - 1) // 3 + 1
    return f"Q{quarter}-{d.year}"


def period_dir(d: date | None = None) -> Path:
    d = d or date.today()
    quarter = (d.month - 1) // 3 + 1
    p = get_storage_root() / str(d.year) / f"Q{quarter}"
    p.mkdir(parents=True, exist_ok=True)
    return p


def folder_size(path: Path) -> int:
    total = 0
    if path.exists():
        for f in path.rglob("*"):
            if f.is_file():
                try:
                    total += f.stat().st_size
                except OSError:
                    pass
    return total


def format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024**2:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024**2):.1f} MB"


def summary() -> dict:
    root = get_storage_root()
    total = folder_size(originals_dir()) + folder_size(reports_dir())
    return {"path": str(root), "size_label": format_size(total)}


def try_open_folder(path: Path) -> bool:
    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.Popen(["open", str(path)])
        elif system == "Windows":
            subprocess.Popen(["explorer", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
        return True
    except (OSError, FileNotFoundError):
        return False
