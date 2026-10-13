"""Settings: AI model, storage, categories, danger zone."""

from __future__ import annotations

from html import escape

import gradio as gr

from ui import mock
from ui.components.blocks import screen_heading
from ui.icons import icon


def _card_head(title: str, meta: str, sub: str = "") -> str:
    sub_html = f'<p class="owl-card-sub">{escape(sub)}</p>' if sub else ""
    return (
        f'<div><div class="owl-card-head"><h3 class="owl-card-title">{escape(title)}</h3>'
        f'<span class="meta">{escape(meta)}</span></div>{sub_html}</div>'
    )


def _categories() -> str:
    rows = "".join(
        f'<div class="owl-cat-row"><span class="owl-cat-name">{escape(name)}</span>'
        f'<span class="owl-cat-edit" title="Rename">{icon("pencil")}</span>'
        f'<span class="owl-cat-default"><input type="checkbox" class="owl-check owl-check--lg"'
        f'{" checked" if on else ""} aria-label="Deductible by default"></span></div>'
        for name, on in mock.SETTINGS_CATEGORIES
    )
    return (
        '<div class="owl-cat-table">'
        '<div class="owl-cat-head"><span>Category name</span><span class="owl-cat-default">Deductible by default</span></div>'
        f"{rows}</div>"
    )


def build() -> dict:
    with gr.Column(elem_classes="owl-screen", visible=False) as screen:
        with gr.Column(elem_classes="owl-workspace owl-workspace--tight"):
            gr.HTML(
                screen_heading(
                    "Settings", "Configure ReceiptOwl preferences and local storage."
                )
            )
            with gr.Row(elem_classes="owl-settings-grid"):
                with gr.Column(elem_classes="owl-settings-left"):
                    with gr.Column(elem_classes="owl-card owl-card--stack"):
                        gr.HTML(
                            _card_head(
                                "AI Model",
                                "Runs with Ollama",
                                "Choose the local model used to read your receipts.",
                            )
                        )
                        with gr.Row(elem_classes="owl-inline-row"):
                            model = gr.Dropdown(
                                choices=mock.MODELS,
                                value=mock.MODELS[0],
                                show_label=False,
                                container=False,
                                filterable=False,
                                elem_classes=["owl-input", "owl-grow"],
                            )
                            test = gr.Button(
                                "Test connection",
                                elem_classes=["owl-btn", "owl-btn-secondary"],
                            )
                        gr.HTML(
                            '<p class="owl-card-sub">Available: '
                            + " · ".join(mock.MODELS)
                            + "</p>"
                            f'<div class="owl-model-status">{icon("circle-check")}'
                            "<span>Ollama + Gemma · Ready · localhost:11434</span></div>"
                        )
                    with gr.Column(elem_classes="owl-card owl-card--stack"):
                        gr.HTML(_card_head("Storage", "Originals and reports"))
                        with gr.Row(elem_classes="owl-inline-row"):
                            gr.Textbox(
                                value=mock.STORAGE_PATH,
                                interactive=False,
                                show_label=False,
                                container=False,
                                elem_classes=["owl-input", "owl-readonly", "owl-grow"],
                            )
                            browse = gr.Button(
                                "Browse",
                                elem_classes=[
                                    "owl-btn",
                                    "owl-btn-secondary",
                                    "owl-ic-folder-open",
                                ],
                            )
                        gr.HTML(
                            '<p class="owl-card-sub">Your workspace stays on this computer.</p>'
                        )
                with gr.Column(
                    elem_classes="owl-card owl-card--stack owl-settings-right"
                ):
                    gr.HTML(
                        _card_head(
                            "Categories",
                            f"{len(mock.SETTINGS_CATEGORIES) + len(mock.SETTINGS_HIDDEN)} categories",
                            "Edit names and set the default deduction for new receipts.",
                        )
                    )
                    gr.HTML(_categories())
                    gr.HTML(
                        '<div class="owl-collapsed"><div>'
                        f'<p class="owl-muted-text" style="margin:0">{len(mock.SETTINGS_HIDDEN)} more categories</p>'
                        f'<p class="owl-collapsed-names">{escape(", ".join(mock.SETTINGS_HIDDEN))}</p></div>'
                        f'<span class="owl-showall">Show all {icon("chevron-down")}</span></div>'
                    )
                    add_cat = gr.Button(
                        "Add category",
                        elem_classes=["owl-btn", "owl-btn-accent", "owl-ic-plus"],
                    )
            with gr.Row(elem_classes="owl-danger"):
                gr.HTML(
                    '<div><h3 class="owl-danger-title">Danger Zone</h3>'
                    '<p class="owl-card-sub" style="margin-top:8px">Clear receipt records and generated reports. '
                    "Your original documents remain untouched.</p></div>"
                )
                reset = gr.Button(
                    "Reset workspace",
                    elem_classes=["owl-btn", "owl-btn-danger", "owl-ic-trash"],
                )
        with gr.Row(elem_classes="owl-actionbar"):
            gr.HTML(
                '<span class="owl-muted-text">No unsaved changes · preferences stored locally</span>'
            )
            save = gr.Button(
                "Save preferences",
                interactive=False,
                elem_classes=["owl-btn", "owl-btn-disabled"],
            )
    return {
        "screen": screen,
        "model": model,
        "test": test,
        "browse": browse,
        "add_category": add_cat,
        "reset": reset,
        "save": save,
    }
