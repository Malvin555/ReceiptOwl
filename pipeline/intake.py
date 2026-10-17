"""Validate uploaded files, stage them into the workspace, and hash"""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from typing import Any

from config import SUPPORTED_FILE_TYPES
from database.db import originals_dir


def _allowed_extensions() -> set[str]:
    out = set()
    for item in SUPPORTED_FILE_TYPES:
        ext = str(item).strip().lower()
        if ext and not ext.startswith("."):
            ext = f".{ext}"
        if ext:
            out.add(ext)
    return out


def _file_path(file: Any) -> Path | None:
    """Gradio hands back str paths, dicts, or objects with .name/.path."""
    if isinstance(file, (str, Path)):
        return Path(file)
    if isinstance(file, dict):
        value = file.get("path") or file.get("name")
        return Path(value) if value else None
    value = getattr(file, "path", None) or getattr(file, "name", None)
    return Path(value) if value else None


def format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024**2:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024**2):.1f} MB"


def preview(files: list[Any] | None) -> list[dict[str, Any]]:
    """Lightweight metadata for the Nest queue list. No disk writes."""
    allowed = _allowed_extensions()
    out = []
    for f in files or []:
        path = _file_path(f)
        if path is None or not path.is_file():
            continue
        if allowed and path.suffix.lower() not in allowed:
            continue
        size = path.stat().st_size
        out.append(
            {
                "path": str(path),
                "name": path.name,
                "kind": "pdf" if path.suffix.lower() == ".pdf" else "image",
                "size_bytes": size,
                "meta": f"{path.suffix.lstrip('.').upper()} · {format_size(size)}",
            }
        )
    return out


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def stage(files: list[Any] | None) -> list[dict[str, Any]]:
    """Validate, hash and copy uploads into ``<workspace>/originals``.

    Returns one dict per accepted file with the staged path and hash, ready
    for ``pipeline.ocr`` / ``pipeline.extract``. Files already staged
    (same hash) are not copied twice.
    """
    allowed = _allowed_extensions()
    staged = []
    dest_dir = originals_dir()

    for f in files or []:
        src = _file_path(f)
        if src is None or not src.is_file():
            continue
        ext = src.suffix.lower()
        if allowed and ext not in allowed:
            continue

        file_hash = _hash_file(src)
        bucket = dest_dir / file_hash[:2]
        bucket.mkdir(parents=True, exist_ok=True)
        dest = bucket / f"{file_hash}{ext}"
        if not dest.exists():
            shutil.copyfile(src, dest)

        size = dest.stat().st_size
        staged.append(
            {
                "path": str(dest),
                "name": src.name,
                "kind": "pdf" if ext == ".pdf" else "image",
                "size_bytes": size,
                "meta": f"{ext.lstrip('.').upper()} · {format_size(size)}",
                "hash": file_hash,
            }
        )

    return staged
