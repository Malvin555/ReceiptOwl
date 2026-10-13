"""Treasure: totals, downloadable reports, organized folder."""

from __future__ import annotations

from html import escape

import gradio as gr

from ui import mock
from ui.components.blocks import pill, screen_heading
from ui.icons import icon


def _stats() -> str:
    cells = "".join(
        '<div class="owl-stat">'
        f'<span class="owl-stat-label">{escape(s["label"])}</span>'
        f'<span class="owl-stat-value{" owl-stat-value--sm" if s["small"] else ""}">{escape(s["value"])}</span>'
        f'<span class="owl-stat-note">{escape(s["note"])}</span></div>'
        for s in mock.TREASURE_STATS
    )
    return f'<div class="owl-card owl-stats">{cells}</div>'


def _report_card_head(r: dict) -> str:
    return (
        '<div class="owl-report-type">'
        f'<span class="owl-report-icon">{icon(r["icon"])}</span>'
        f'<h3 class="owl-card-title">{escape(r["format"])}</h3></div>'
        f'<p class="owl-report-file">{escape(r["filename"])}</p>'
        f'<p class="owl-report-desc">{escape(r["desc"])}</p>'
        '<div class="owl-report-spacer"></div>'
    )


def build() -> dict:
    folder = mock.TREASURE_FOLDER
    downloads = []
    with gr.Column(elem_classes="owl-screen", visible=False) as screen:
        with gr.Column(elem_classes="owl-workspace owl-workspace--tight"):
            gr.HTML(
                screen_heading(
                    "Treasure",
                    "Review totals, download reports, and open the organized receipt folder.",
                )
            )
            gr.HTML(_stats())
            with gr.Row(elem_classes="owl-reports"):
                for r in mock.TREASURE_REPORTS:
                    with gr.Column(elem_classes="owl-card owl-report"):
                        gr.HTML(_report_card_head(r))
                        with gr.Row(elem_classes="owl-report-foot"):
                            gr.HTML(
                                f'<span class="owl-report-meta">{escape(r["meta"])}</span>'
                            )
                            downloads.append(
                                gr.Button(
                                    "Download",
                                    elem_classes=[
                                        "owl-btn",
                                        "owl-btn-secondary",
                                        "owl-ic-download",
                                    ],
                                )
                            )
            with gr.Column(elem_classes="owl-card owl-folder"):
                gr.HTML(
                    '<div class="owl-card-head"><div class="owl-folder-id">'
                    f'<span class="owl-report-icon">{icon("folder-open")}</span>'
                    '<h3 class="owl-card-title">Organized receipt folder</h3></div>'
                    f'<span class="owl-report-meta">{escape(folder["meta"])}</span></div>'
                )
                with gr.Row(elem_classes="owl-folder-row"):
                    gr.Textbox(
                        value=folder["path"],
                        interactive=False,
                        show_label=False,
                        container=False,
                        elem_classes=[
                            "owl-input",
                            "owl-readonly",
                            "owl-mono",
                            "owl-folder-path",
                        ],
                    )
                    open_folder = gr.Button(
                        "Open folder",
                        elem_classes=[
                            "owl-btn",
                            "owl-btn-secondary",
                            "owl-ic-folder-open",
                        ],
                    )
                gr.HTML(
                    '<p class="owl-report-meta">Totals exclude 2 duplicates. Review 3 flagged receipts '
                    "before filing; these are not tax advice.</p>"
                )
        with gr.Row(elem_classes="owl-actionbar"):
            gr.HTML(pill("Reports saved locally", "success", dot=True))
            regenerate = gr.Button(
                "Regenerate reports",
                elem_classes=["owl-btn", "owl-btn-secondary", "owl-ic-refresh-cw"],
            )
    return {
        "screen": screen,
        "downloads": downloads,
        "open_folder": open_folder,
        "regenerate": regenerate,
    }
