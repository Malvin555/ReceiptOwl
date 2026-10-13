"""Hunt: live processing progress, step checklist and log."""

from __future__ import annotations

from html import escape

import gradio as gr

from ui import mock
from ui.components.blocks import pill, progress, screen_heading
from ui.icons import icon

_TONE = {"done": "success", "active": "warning", "waiting": "neutral"}
_LEVEL_CLS = {"INFO": "info", "OK": "ok", "WARN": "warn"}


def _progress_card() -> str:
    p = mock.HUNT_PROGRESS
    return (
        '<div class="owl-card owl-stack">'
        '<div class="owl-card-head">'
        f'<h3 class="owl-card-title">{escape(p["label"])}</h3>'
        f'<span class="owl-progress-count">{p["done"]} / {p["total"]} · {p["pct"]}%</span></div>'
        f"{progress(p['pct'])}</div>"
    )


def _steps() -> str:
    cards = []
    for s in mock.HUNT_STEPS:
        spin = " owl-spin" if s["state"] == "active" else ""
        active = " owl-step--active" if s["state"] == "active" else ""
        cards.append(
            f'<div class="owl-card owl-step{active}">'
            f'<div class="owl-step-label"><span class="owl-step-icon{spin}">{icon(s["icon"])}</span>'
            f'<h3 class="owl-card-title">{escape(s["title"])}</h3></div>'
            f'<p class="owl-step-detail">{escape(s["detail"])}</p>'
            f"{pill(s['pill'], _TONE[s['state']])}</div>"
        )
    return f'<div class="owl-steps">{"".join(cards)}</div>'


def _log() -> str:
    rows = "".join(
        f'<div class="owl-log-row"><span class="t">{t}</span>'
        f'<span class="lvl lvl--{_LEVEL_CLS[lvl]}">{lvl}</span><span class="msg">{escape(msg)}</span></div>'
        for t, lvl, msg in mock.HUNT_LOG
    )
    return (
        '<div class="owl-log">'
        '<div class="owl-log-head"><strong>Live log</strong>'
        '<span class="owl-live"><i></i>Auto-scroll on</span></div>'
        f'<div class="owl-log-body">{rows}</div></div>'
    )


def build() -> dict:
    with gr.Column(elem_classes="owl-screen", visible=False) as screen:
        with gr.Column(elem_classes="owl-workspace owl-workspace--tight"):
            gr.HTML(
                screen_heading(
                    "Hunt",
                    "Turning receipts into a clean, tax-ready record. Entirely offline.",
                )
            )
            gr.HTML(_progress_card())
            gr.HTML(_steps())
            gr.HTML(_log())
        with gr.Row(elem_classes="owl-actionbar"):
            gr.HTML(
                f'<span class="owl-timing">{icon("clock")}<span>{mock.HUNT_TIMING}</span></span>'
            )
            cancel = gr.Button("Cancel job", elem_classes=["owl-btn", "owl-btn-danger"])
    return {"screen": screen, "cancel": cancel}
