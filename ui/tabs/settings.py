"""Settings — storage location, model choice, categories, and the Danger Zone reset"""

from __future__ import annotations

from html import escape
from pathlib import Path

import gradio as gr

import config
from database import db
from pipeline.extract import _ollama_reachable
from services import receipt_service
from ui.components.blocks import screen_heading
from ui.components.modal import build_confirm_modal, hide, show
from ui.icons import icon


def _category_rows_html() -> str:
    cats = db.list_categories()
    head = '<div class="owl-cat-head"><span>Category</span><span class="owl-cat-default">Tax-deductible</span></div>'
    rows = []
    for c in cats:
        badge = (
            '<span class="owl-pill owl-pill--success">Deductible</span>'
            if c["deductible_default"]
            else '<span class="owl-pill owl-pill--neutral">Not deductible</span>'
        )
        rows.append(
            f'<div class="owl-cat-row"><span class="owl-cat-name">{escape(c["name"])}</span>'
            f'<span class="owl-cat-default">{badge}</span></div>'
        )
    return f'<div class="owl-cat-table">{head}{"".join(rows)}</div>'


def _model_status_html(model: str) -> str:
    reachable = _ollama_reachable()
    text = (
        f"Using local Ollama ({model})"
        if reachable
        else "Ollama not reachable — using the offline heuristic extractor"
    )
    ic = "circle-check" if reachable else "circle-alert"
    return f'<div class="owl-model-status">{icon(ic, 16)}<span>{text}</span></div>'


def build(ctx: dict) -> dict:
    with gr.Column(visible=False, elem_classes=["owl-screen"]) as screen:
        with gr.Column(elem_classes=["owl-workspace"]):
            gr.HTML(
                screen_heading(
                    "Settings",
                    "Storage, model and category preferences — all stored locally.",
                )
            )

            with gr.Row(elem_classes=["owl-settings-grid"]):
                with gr.Column(elem_classes=["owl-settings-left"]):
                    with gr.Column(elem_classes=["owl-card", "owl-card--stack"]):
                        gr.HTML(
                            '<span class="owl-card-title">Storage location</span>'
                            '<p class="owl-card-sub">Where your database, originals and reports live.</p>'
                        )
                        with gr.Row(elem_classes=["owl-inline-row"]):
                            storage_box = gr.Textbox(
                                value=str(config.get_storage_root()),
                                show_label=False,
                                elem_classes=["owl-input", "owl-grow"],
                            )
                            save_storage_btn = gr.Button(
                                "Save", elem_classes=["owl-btn", "owl-btn-secondary"]
                            )

                    with gr.Column(elem_classes=["owl-card", "owl-card--stack"]):
                        gr.HTML(
                            '<span class="owl-card-title">AI model</span>'
                            '<p class="owl-card-sub">Used for field extraction when a local Ollama server is running.</p>'
                        )
                        model_dropdown = gr.Dropdown(
                            choices=config.MODEL_OPTIONS,
                            value=config.DEFAULT_MODEL,
                            show_label=False,
                            elem_classes=["owl-input"],
                        )
                        model_status = gr.HTML(_model_status_html(config.DEFAULT_MODEL))

                    with gr.Column(elem_classes=["owl-danger"]):
                        gr.HTML(
                            '<div><p class="owl-danger-title">Danger Zone</p>'
                            '<p class="owl-card-sub">Clears every receipt record from the database. '
                            "Original files already saved to your originals folder are left untouched.</p></div>"
                        )
                        reset_open_btn = gr.Button(
                            "Reset workspace",
                            elem_classes=["owl-btn", "owl-btn-danger"],
                        )

                with gr.Column(elem_classes=["owl-card", "owl-card--stack"]):
                    gr.HTML('<span class="owl-card-title">Categories</span>')
                    cat_table = gr.HTML(_category_rows_html())
                    with gr.Row(elem_classes=["owl-inline-row"]):
                        cat_select = gr.Dropdown(
                            choices=db.category_names(),
                            label="Category",
                            elem_classes=["owl-input", "owl-grow"],
                        )
                        cat_name = gr.Textbox(
                            label="Name", elem_classes=["owl-input", "owl-grow"]
                        )
                        cat_deductible = gr.Checkbox(
                            label="Deductible", elem_classes=["owl-toggle"]
                        )
                    with gr.Row(elem_classes=["owl-inline-row"]):
                        cat_add_btn = gr.Button(
                            "Add new", elem_classes=["owl-btn", "owl-btn-secondary"]
                        )
                        cat_save_btn = gr.Button(
                            "Save changes", elem_classes=["owl-btn", "owl-btn-primary"]
                        )
                        cat_delete_btn = gr.Button(
                            "Delete", elem_classes=["owl-btn", "owl-btn-danger"]
                        )

        with gr.Row(elem_classes=["owl-actionbar"]):
            gr.HTML(
                '<span class="owl-muted-text">All processing and storage stays on this machine.</span>'
            )
            gr.HTML("")

    overlay, confirm_btn, cancel_btn = build_confirm_modal(
        "reset-modal",
        "Reset workspace?",
        "This permanently clears every receipt record and regenerated report. "
        "Original uploaded files stay in your originals folder. This can't be undone.",
        confirm_label="Reset workspace",
    )

    # ---- storage ----
    def save_storage(path_str):
        try:
            p = Path(path_str).expanduser()
            p.mkdir(parents=True, exist_ok=True)
            config.set_storage_root(p)
            gr.Info(
                "Storage location saved. Restart ReceiptOwl for it to take full effect."
            )
        except OSError as exc:
            gr.Warning(f"Couldn't use that folder: {exc}")

    save_storage_btn.click(save_storage, inputs=storage_box)

    # ---- model ----
    model_dropdown.change(
        lambda m: _model_status_html(m), inputs=model_dropdown, outputs=model_status
    )

    # ---- categories ----
    def reload_categories():
        names = db.category_names()
        return _category_rows_html(), gr.update(choices=names)

    def on_cat_select(name):
        if not name:
            return gr.update(value=""), gr.update(value=False)
        c = next((c for c in db.list_categories() if c["name"] == name), None)
        if not c:
            return gr.update(value=""), gr.update(value=False)
        return gr.update(value=c["name"]), gr.update(
            value=bool(c["deductible_default"])
        )

    cat_select.change(
        on_cat_select, inputs=cat_select, outputs=[cat_name, cat_deductible]
    )

    def on_add(name, deductible):
        try:
            db.add_category(name, deductible)
            gr.Info(f'"{name}" added.')
        except ValueError as exc:
            gr.Warning(str(exc))
        return reload_categories()

    def on_save(selected, name, deductible):
        if not selected:
            gr.Warning("Pick a category to edit first.")
            return reload_categories()
        cat = next((c for c in db.list_categories() if c["name"] == selected), None)
        if not cat:
            return reload_categories()
        try:
            db.update_category(cat["id"], name, deductible)
            gr.Info("Category updated.")
        except ValueError as exc:
            gr.Warning(str(exc))
        return reload_categories()

    def on_delete(selected):
        if not selected:
            gr.Warning("Pick a category to delete first.")
            return reload_categories()
        cat = next((c for c in db.list_categories() if c["name"] == selected), None)
        if not cat:
            return reload_categories()
        try:
            db.delete_category(cat["id"])
            gr.Info("Category deleted.")
        except ValueError as exc:
            gr.Warning(str(exc))
        return reload_categories()

    cat_add_btn.click(
        on_add, inputs=[cat_name, cat_deductible], outputs=[cat_table, cat_select]
    )
    cat_save_btn.click(
        on_save,
        inputs=[cat_select, cat_name, cat_deductible],
        outputs=[cat_table, cat_select],
    )
    cat_delete_btn.click(on_delete, inputs=cat_select, outputs=[cat_table, cat_select])

    # ---- danger zone / reset modal ----
    reset_open_btn.click(show, outputs=overlay)
    cancel_btn.click(hide, outputs=overlay)

    def do_reset():
        receipt_service.reset_workspace()
        gr.Info("Workspace reset. All receipt records cleared.")
        return hide()

    reset_done = confirm_btn.click(do_reset, outputs=overlay)

    return {
        "screen": screen,
        "reset_done_event": reset_done,
        "reload_categories": reload_categories,
    }
