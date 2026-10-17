from __future__ import annotations

from config import CONFIDENCE_AMBER

_PRIORITY = ("dupe", "tax", "review")
_LABELS = {"dupe": "Dupe", "tax": "Tax", "review": "Review"}


def detect(amount: float | None, tax: float | None, confidence: float) -> list[str]:
    flags = []
    if amount and not tax:
        flags.append("tax")
    if confidence < CONFIDENCE_AMBER:
        flags.append("review")
    return flags


def primary_flag(flags: list[str]) -> str | None:
    for candidate in _PRIORITY:
        if candidate in flags:
            return candidate
    return None


def flag_label(flag: str | None) -> str | None:
    return _LABELS.get(flag) if flag else None
