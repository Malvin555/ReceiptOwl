"""Hunt — live processing view. Streams progress"""

from __future__ import annotations

import time
import uuid
from html import escape

import gradio as gr

from services import receipt_service
from ui.components.blocks import progress, screen_heading
from ui.icons import icon

_STEP_ORDER = [
    ("reading", "Reading"),
    ("extracting", "Extracting"),
    ("categorizing", "Categorizing"),
    ("reporting", "Reporting"),
]
_STEP_DETAIL = {
    "waiting": "Waiting…",
    "active": "In progress…",
    "done": "Done",
}


def _step_icon(status: str) -> str:
    if status == "done":
        return icon("circle-check", 18)
    if status == "active":
        return f'<span class="owl-spin">{icon("loader-circle", 18)}</span>'
    return icon("circle", 18)


def _steps_html(steps: dict) -> str:
    cells = []
    for key, label in _STEP_ORDER:
        status = steps.get(key, "waiting")
        cls = "owl-card owl-step" + (" owl-step--active" if status == "active" else "")
        cells.append(
            f'<div class="{cls}"><div class="owl-step-label">'
            f'<span class="owl-step-icon">{_step_icon(status)}</span><strong>{label}</strong></div>'
            f'<p class="owl-step-detail">{_STEP_DETAIL.get(status, "Waiting…")}</p></div>'
        )
    return f'<div class="owl-steps">{"".join(cells)}</div>'


def _progress_html(done: int, total: int, pct: int) -> str:
    count = f"{done} / {total}" if total else "0 / 0"
    return (
        '<div class="owl-card owl-stack"><div class="owl-card-head">'
        f'<span class="owl-card-title">Processing receipts</span>'
        f'<span class="owl-progress-count">{count} · {pct}%</span></div>'
        f"{progress(pct, tone='amber')}</div>"
    )


def _log_html(log: list[tuple[str, str, str]], live: bool) -> str:
    rows = []
    for t, level, msg in log[-60:]:
        lvl_cls = {"OK": "lvl--ok", "WARN": "lvl--warn"}.get(level, "")
        rows.append(
            f'<div class="owl-log-row"><span class="t">{t}</span>'
            f'<span class="lvl {lvl_cls}">{level}</span><span class="msg">{escape(msg)}</span></div>'
        )
    live_html = (
        f'<span class="owl-live"><i></i>Live</span>'
        if live
        else '<span class="owl-live">Finished</span>'
    )
    return (
        '<div class="owl-log"><div class="owl-log-head"><strong>Activity log</strong>'
        f'{live_html}</div><div class="owl-log-body">{"".join(rows) or '<div class="owl-log-row"><span class="msg">Waiting for files…</span></div>'}</div></div>'
    )


def build(ctx: dict) -> dict:
    with gr.Column(visible=False, elem_classes=["owl-screen"]) as screen:
        with gr.Column(elem_classes=["owl-workspace"]):
            gr.HTML(
                screen_heading(
                    "Hunt",
                    "Reading, extracting and categorizing — all on this machine.",
                )
            )
            progress_html = gr.HTML(_progress_html(0, 0, 0))
            steps_html = gr.HTML(_steps_html({}))
            log_html = gr.HTML(_log_html([], live=False))

        with gr.Row(elem_classes=["owl-actionbar"]):
            gr.HTML(
                '<span class="owl-muted-text" id="hunt-status">Drop files in Nest to begin.</span>'
            )
            with gr.Row(elem_classes=["owl-actionbar-right"]):
                cancel_btn = gr.Button(
                    "Cancel",
                    elem_classes=["owl-btn", "owl-btn-secondary"],
                    interactive=False,
                )
                view_btn = gr.Button(
                    "View in Perch →",
                    elem_classes=["owl-btn", "owl-btn-primary"],
                    interactive=False,
                )

    def run(files, model, job_id):
        if not files:
            yield (
                _progress_html(0, 0, 0),
                _steps_html({}),
                _log_html([], live=False),
                gr.update(interactive=False),
                gr.update(interactive=False),
                job_id,
            )
            return

        new_job_id = uuid.uuid4().hex
        for snap in receipt_service.process_batch(files, new_job_id, model):
            done_flag = snap["phase"] in ("done", "cancelled")
            yield (
                _progress_html(snap["done"], snap["total"], snap["pct"]),
                _steps_html(snap["steps"]),
                _log_html(snap["log"], live=not done_flag),
                gr.update(interactive=not done_flag),
                gr.update(interactive=snap["phase"] == "done"),
                new_job_id,
            )

    def cancel(job_id):
        receipt_service.request_cancel(job_id)
        return gr.update(interactive=False)

    cancel_btn.click(cancel, inputs=ctx["job_id"], outputs=cancel_btn)

    return {
        "screen": screen,
        "run": run,
        "cancel_btn": cancel_btn,
        "view_btn": view_btn,
        "outputs": [
            progress_html,
            steps_html,
            log_html,
            cancel_btn,
            view_btn,
            ctx["job_id"],
        ],
    }
