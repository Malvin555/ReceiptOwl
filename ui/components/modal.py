from __future__ import annotations

import gradio as gr

from ui.icons import icon


def build_confirm_modal(
    elem_id: str,
    title: str,
    body: str,
    confirm_label: str = "Confirm",
    cancel_label: str = "Cancel",
    danger: bool = True,
):
    with gr.Group(
        visible=False, elem_id=elem_id, elem_classes=["owl-modal-overlay"]
    ) as overlay:
        with gr.Column(elem_classes=["owl-modal"]):
            gr.HTML(
                f'<div class="owl-modal-head">{icon("circle-alert", 20)}'
                f'<h3 class="owl-modal-title">{title}</h3></div>'
                f'<p class="owl-modal-body">{body}</p>'
            )
            with gr.Row(elem_classes=["owl-modal-actions"]):
                cancel_btn = gr.Button(
                    cancel_label, elem_classes=["owl-btn", "owl-btn-secondary"]
                )
                confirm_btn = gr.Button(
                    confirm_label,
                    elem_classes=[
                        "owl-btn",
                        "owl-btn-danger" if danger else "owl-btn-primary",
                    ],
                )
    return overlay, confirm_btn, cancel_btn


def show() -> "gr.update":
    return gr.update(visible=True)


def hide() -> "gr.update":
    return gr.update(visible=False)
