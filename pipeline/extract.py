# Turn OCR text
from __future__ import annotations

import json
import re
import socket
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from config import DEFAULT_MODEL, OLLAMA_HOST

_AMOUNT_RE = re.compile(r"\$?\s?(\d{1,3}(?:,\d{3})*\.\d{2})\b")
_TAX_LINE_RE = re.compile(r"tax[^\d]{0,12}(\d{1,3}(?:,\d{3})*\.\d{2})", re.IGNORECASE)
_FILENAME_DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
_DATE_PATTERNS = [
    ("%Y-%m-%d", re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")),
    ("%m/%d/%Y", re.compile(r"\b(\d{1,2}/\d{1,2}/\d{4})\b")),
    ("%m/%d/%y", re.compile(r"\b(\d{1,2}/\d{1,2}/\d{2})\b")),
]


def _ollama_reachable(timeout: float = 0.3) -> bool:
    try:
        parsed = urlparse(OLLAMA_HOST)
        with socket.create_connection(
            (parsed.hostname, parsed.port or 11434), timeout=timeout
        ):
            return True
    except OSError:
        return False


def _call_ollama(text: str, model: str) -> dict | None:
    import requests

    prompt = (
        "Extract receipt fields as strict JSON with keys date (YYYY-MM-DD or null), "
        "vendor (string or null), amount (number or null), tax (number or null). "
        "No prose, JSON only.\n\nReceipt text:\n" + text[:4000]
    )
    try:
        resp = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False, "format": "json"},
            timeout=20,
        )
        resp.raise_for_status()
        payload = json.loads(resp.json().get("response", "{}"))
        return {
            "date": payload.get("date"),
            "vendor": payload.get("vendor"),
            "amount": _to_float(payload.get("amount")),
            "tax": _to_float(payload.get("tax")),
        }
    except Exception:
        return None


def _to_float(value) -> float | None:
    if value is None:
        return None
    try:
        return round(float(str(value).replace(",", "").replace("$", "")), 2)
    except (TypeError, ValueError):
        return None


def _guess_date(text: str, filename: str) -> str | None:
    for fmt, pattern in _DATE_PATTERNS:
        m = pattern.search(text)
        if m:
            try:
                return datetime.strptime(m.group(1), fmt).date().isoformat()
            except ValueError:
                continue
    m = _FILENAME_DATE_RE.search(filename)
    if m:
        return m.group(1)
    return None


def _guess_vendor(text: str, filename: str) -> str | None:
    for line in text.splitlines():
        line = line.strip()
        if 2 <= len(line) <= 40 and not _AMOUNT_RE.search(line):
            return line
    stem = Path(filename).stem
    stem = _FILENAME_DATE_RE.sub("", stem).strip("_- ")
    stem = re.sub(r"[_\-]+", " ", stem).strip()
    return stem.title() if stem else None


def _guess_amount(text: str) -> float | None:
    amounts = [float(m.replace(",", "")) for m in _AMOUNT_RE.findall(text)]
    return max(amounts) if amounts else None


def _guess_tax(text: str) -> float | None:
    m = _TAX_LINE_RE.search(text)
    return _to_float(m.group(1)) if m else None


def heuristic_extract(text: str, filename: str) -> dict:
    date = _guess_date(text, filename)
    vendor = _guess_vendor(text, filename)
    amount = _guess_amount(text)
    tax = _guess_tax(text)

    found = sum(x is not None for x in (date, vendor, amount))
    if text.strip() and found == 3:
        confidence = 90.0
    elif text.strip() and found >= 1:
        confidence = 65.0
    elif found >= 1:
        confidence = 40.0  # filename-only guesses
    else:
        confidence = 20.0

    return {
        "date": date,
        "vendor": vendor or "Unknown vendor",
        "amount": amount,
        "tax": tax,
        "confidence": confidence,
        "source": "heuristic",
    }


def extract_fields(text: str, filename: str, model: str = DEFAULT_MODEL) -> dict:
    """Best-effort field extraction. Always returns a usable dict."""
    if text.strip() and _ollama_reachable():
        result = _call_ollama(text, model)
        if result and (result.get("amount") is not None or result.get("vendor")):
            found = sum(
                x is not None
                for x in (
                    result.get("date"),
                    result.get("vendor"),
                    result.get("amount"),
                )
            )
            result["confidence"] = 95.0 if found == 3 else 75.0
            result["source"] = "llm"
            result.setdefault(
                "vendor", _guess_vendor(text, filename) or "Unknown vendor"
            )
            return result

    return heuristic_extract(text, filename)
