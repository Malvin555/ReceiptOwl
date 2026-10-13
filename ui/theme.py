"""Theme + CSS assembly."""

from __future__ import annotations

from pathlib import Path

import gradio as gr

from ui.icons import ICON_NAMES, data_uri

ASSETS = Path(__file__).resolve().parent / "assets"
CSS_FILES = ["main.css", "layout.css", "components.css", "tabs.css"]


def _icon_mask_css() -> str:
    """``.owl-ic-<name>::before`` rules so a gr.Button / tab can show a Lucide icon."""
    rules = []
    for name in ICON_NAMES:
        uri = data_uri(name)
        rules.append(
            f'.owl-ic-{name}::before{{content:"";display:inline-block;flex:none;width:18px;height:18px;'
            f'background-color:currentColor;-webkit-mask:url("{uri}") center/contain no-repeat;'
            f'mask:url("{uri}") center/contain no-repeat;}}'
        )
    root = (
        f':root{{--owl-search-icon:url("{data_uri("search")}");'
        f'--owl-chevron:url("{data_uri("chevron-down", "#2b2117")}");}}'
    )
    return root + "\n" + "\n".join(rules)


def build_css() -> str:
    parts = [(ASSETS / "css" / name).read_text(encoding="utf-8") for name in CSS_FILES]
    parts.append(_icon_mask_css())
    return "\n".join(parts)


def get_theme() -> gr.themes.Base:
    return gr.themes.Base(
        font=[
            "-apple-system",
            "BlinkMacSystemFont",
            "Segoe UI",
            "Roboto",
            "Ubuntu",
            "sans-serif",
        ],
        font_mono=["IBM Plex Mono", "ui-monospace", "monospace"],
    )


def get_launch_kwargs() -> dict:
    return {"theme": get_theme(), "css": build_css()}
