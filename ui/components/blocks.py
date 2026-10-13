"""Reusable HTML builders"""

from __future__ import annotations

from html import escape

from ui.icons import icon


def pill(
    label: str, tone: str = "neutral", dot: bool = False, outlined: bool = False
) -> str:
    """Status pill. tone: success | warning | warning2 | neutral | error."""
    cls = f"owl-pill owl-pill--{tone}" + (" owl-pill--outlined" if outlined else "")
    dot_html = '<span class="owl-pill-dot"></span>' if dot else ""
    return f'<span class="{cls}">{dot_html}{escape(label)}</span>'


def screen_heading(
    title: str, description: str, right: str = "", desc_size: str = "13"
) -> str:
    return (
        '<div class="owl-heading">'
        f'<div><h2 class="owl-title">{escape(title)}</h2>'
        f'<p class="owl-desc owl-desc--{desc_size}">{escape(description)}</p></div>'
        f"{right}</div>"
    )


def local_badge() -> str:
    return f'<span class="owl-badge">{icon("lock")}<span>Local only</span></span>'


def header_left() -> str:
    return (
        '<div class="owl-header-left">'
        f'<span class="owl-logo">{icon("owl", 18)}</span>'
        '<span class="owl-brand">ReceiptOwl</span></div>'
    )


def header_status() -> str:
    """Local-only badge + model-ready dot (green = ready, see Figma model status dots)."""
    return f'<div class="owl-header-status">{local_badge()}<span class="owl-status-dot" title="Model ready"></span></div>'


def progress(pct: float, tone: str = "amber", width: int | None = None) -> str:
    style = f' style="width:{width}px"' if width else ""
    return (
        f'<span class="owl-progress"{style}><span class="owl-progress-value owl-progress-value--{tone}" '
        f'style="width:{pct}%"></span></span>'
    )
