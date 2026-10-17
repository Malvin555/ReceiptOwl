"""Nest — drop receipts in, see the queue, head to Hunt to process them."""

from __future__ import annotations

import gradio as gr

from pipeline.intake import format_size, preview
from ui.components.blocks import screen_heading
from ui.icons import icon

MAX_FILE_MB = 20


def _queue_html(files) -> str:
    items = preview(files)
    if not items:
        return '<div class="owl-queue-head"><span>No files queued yet</span></div>'
    total = sum(i["size_bytes"] for i in items)
    return (
        f'<div class="owl-queue-head"><span><strong>{len(items)}</strong> file(s) queued</span>'
        f"<span>{format_size(total)} total</span></div>"
    )


def build(ctx: dict) -> dict:
    with gr.Column(visible=True, elem_classes=["owl-screen"]) as screen:
        with gr.Column(elem_classes=["owl-workspace"]):
            gr.HTML(
                screen_heading(
                    "Nest",
                    "Drop receipts in — PDFs, JPGs or PNGs. They stay on this machine.",
                )
            )
            with gr.Column(scale=0, elem_classes=["owl-card"]):
                with gr.Column(elem_classes=["owl-dropzone-wrap"]):
                    uploader = gr.File(
                        file_count="multiple",
                        file_types=[".pdf", ".jpg", ".jpeg", ".png"],
                        elem_classes=["owl-dropzone"],
                        label="",
                        show_label=False,
                    )
                    gr.HTML(
                        '<div class="owl-dropzone-overlay-block"><div class="owl-dropzone-overlay">'
                        f'<span class="owl-dropzone-mark">{icon("home", 22)}</span>'
                        '<div class="owl-dropzone-main">Drop receipts here or <span class="owl-link">browse</span></div>'
                        '<div class="owl-dropzone-types">PDF, JPG or PNG</div>'
                        f'<div class="owl-dropzone-note">Up to {MAX_FILE_MB} MB per file · processed entirely offline</div>'
                        "</div></div>"
                    )
                queue_html = gr.HTML(_queue_html(None))

        with gr.Row(elem_classes=["owl-actionbar"]):
            gr.HTML('<span class="owl-muted-text">Nothing leaves this computer.</span>')
            with gr.Row(elem_classes=["owl-actionbar-right"]):
                clear_btn = gr.Button(
                    "Clear queue", elem_classes=["owl-btn", "owl-btn-secondary"]
                )
                start_btn = gr.Button(
                    "Start hunting →",
                    elem_classes=["owl-btn", "owl-btn-primary"],
                    interactive=False,
                )

    def on_change(files):
        has_files = bool(files)
        return _queue_html(files), gr.update(interactive=has_files)

    uploader.change(on_change, inputs=uploader, outputs=[queue_html, start_btn])
    clear_btn.click(
        lambda: (None, _queue_html(None), gr.update(interactive=False)),
        outputs=[uploader, queue_html, start_btn],
    )

    return {
        "screen": screen,
        "uploader": uploader,
        "start_btn": start_btn,
        "clear_btn": clear_btn,
    }
