"""Nest: upload receipts and review the queue before processing."""

from __future__ import annotations

from html import escape

import gradio as gr

from config import SUPPORTED_FILE_TYPES
from ui import mock
from ui.components.blocks import screen_heading
from ui.icons import icon


def _queue_html() -> str:
    s = mock.QUEUE_SUMMARY
    rows = "".join(
        f'<div class="owl-queue-row">{icon("file-text" if r["kind"] == "pdf" else "image")}'
        f'<span class="owl-queue-name">{escape(r["name"])}</span>'
        f'<span class="owl-queue-meta">{escape(r["meta"])}</span>'
        f'<span class="owl-queue-x" title="Remove">{icon("x")}</span></div>'
        for r in mock.QUEUE_PREVIEW
    )
    return (
        '<div class="owl-queue">'
        '<div class="owl-queue-head">'
        f"<strong>File queue · {s['count']} receipts</strong>"
        f"<span>{s['pdfs']} PDFs · {s['images']} images · {s['size']}</span></div>"
        f'<div class="owl-queue-list">{rows}'
        '<div class="owl-queue-more">'
        f"<span>{mock.QUEUE_MORE} more files in this batch</span>"
        '<span class="owl-link">Show all files ↓</span></div></div></div>'
    )


def _dropzone_overlay() -> str:
    return (
        '<div class="owl-dropzone-overlay">'
        f'<span class="owl-dropzone-mark">{icon("owl", 28)}</span>'
        '<span class="owl-dropzone-main">Drop receipts here, or browse files</span>'
        '<span class="owl-dropzone-types">PDF, JPG, PNG</span>'
        '<span class="owl-dropzone-note">Files stay on this laptop</span></div>'
    )


def build() -> dict:
    with gr.Column(elem_classes="owl-screen", visible=True) as screen:
        with gr.Column(elem_classes="owl-workspace"):
            gr.HTML(
                screen_heading(
                    "Drop receipts into the nest",
                    "Upload receipts and prepare them for processing.",
                )
            )
            with gr.Column(elem_classes="owl-dropzone-wrap"):
                files = gr.File(
                    file_count="multiple",
                    file_types=SUPPORTED_FILE_TYPES,
                    show_label=False,
                    container=False,
                    elem_classes="owl-dropzone",
                )
                gr.HTML(_dropzone_overlay(), elem_classes="owl-dropzone-overlay-block")
            gr.HTML(_queue_html())
        with gr.Row(elem_classes="owl-actionbar"):
            clear = gr.Button("Clear all", elem_classes=["owl-btn", "owl-btn-ghost"])
            with gr.Row(elem_classes="owl-actionbar-right"):
                gr.HTML(
                    f'<span class="owl-muted-text">ETA · {mock.QUEUE_SUMMARY["eta"]}</span>'
                )
                start = gr.Button(
                    f"Start processing ({mock.QUEUE_SUMMARY['count']})",
                    elem_classes=["owl-btn", "owl-btn-primary", "owl-ic-play"],
                )
    return {"screen": screen, "files": files, "clear": clear, "start": start}
