"""Perch — the receipts table"""

from __future__ import annotations

from html import escape

import gradio as gr

from config import CONFIDENCE_AMBER, CONFIDENCE_GREEN
from database import db
from pipeline.anomalies import flag_label, primary_flag
from services import receipt_service
from ui.components.blocks import screen_heading
from ui.icons import icon


def _conf_tone(conf: float) -> str:
    if conf >= CONFIDENCE_GREEN:
        return "success"
    if conf >= CONFIDENCE_AMBER:
        return "warning"
    return "error"


def _table_html(receipts: list[dict]) -> str:
    head = (
        '<div class="owl-table-head"><span class="owl-col-date">Date</span>'
        '<span class="owl-col-vendor">Vendor</span><span class="owl-col-amount">Amount</span>'
        '<span class="owl-col-tax">Tax</span><span class="owl-col-cat">Category</span>'
        '<span class="owl-col-conf">Confidence</span><span class="owl-col-flag">Flag</span></div>'
    )

    if not receipts:
        body = (
            '<div class="owl-row">'
            '<span style="color:var(--owl-feather)">'
            "No receipts yet — process some in Hunt."
            "</span></div>"
        )
    else:
        rows = []

        for r in receipts:
            flag = primary_flag(r.get("flags") or [])
            row_cls = "owl-row"

            if r.get("is_duplicate"):
                row_cls += " owl-row--duplicate"
            elif flag:
                row_cls += " owl-row--flagged"

            conf = r.get("confidence") or 0

            tax_html = (
                f"${r['tax']:,.2f}"
                if r.get("tax") is not None
                else '<span class="owl-tax-missing">Missing</span>'
            )

            flag_html = (
                f'<span class="owl-flag--{flag}">{flag_label(flag)}</span>'
                if flag
                else "—"
            )

            rows.append(
                f'<div class="{row_cls}">'
                f'<span class="owl-col-date">'
                f"{escape(r.get('receipt_date') or '—')}</span>"
                f'<span class="owl-col-vendor">'
                f"{escape(r.get('vendor') or 'Unknown')}</span>"
                f'<span class="owl-col-amount">'
                f"${(r.get('amount') or 0):,.2f}</span>"
                f'<span class="owl-col-tax">{tax_html}</span>'
                f'<span class="owl-col-cat">'
                f"{escape(r.get('category') or 'Other')}</span>"
                f'<span class="owl-col-conf">'
                f'<span class="owl-conf-text owl-conf--{_conf_tone(conf)}">'
                f"{round(conf)}%</span></span>"
                f'<span class="owl-col-flag">{flag_html}</span>'
                "</div>"
            )

        body = "".join(rows)

    foot = f'<div class="owl-table-foot"><span>{len(receipts)} receipt(s)</span></div>'

    return (
        f'<div class="owl-table">'
        f'<div class="owl-table-scroll">{head}{body}</div>'
        f"</div>{foot}"
    )


def _receipt_choices(receipts: list[dict]) -> list[tuple[str, int]]:
    out = []

    for r in receipts:
        label = (
            f"#{r['id']} · {r.get('vendor') or 'Unknown'} · "
            f"${(r.get('amount') or 0):,.2f}"
        )
        out.append((label, r["id"]))

    return out


def build(ctx: dict) -> dict:
    with gr.Column(visible=False, elem_classes=["owl-screen"]) as screen:
        with gr.Column(elem_classes=["owl-workspace", "owl-workspace--tight"]):
            gr.HTML(
                screen_heading(
                    "Perch",
                    "Every receipt, organized and ready for tax season.",
                )
            )

            with gr.Row(elem_classes=["owl-toolbar"]):
                search_box = gr.Textbox(
                    placeholder="Search vendor or file name…",
                    show_label=False,
                    elem_classes=[
                        "owl-input",
                        "owl-search",
                        "owl-toolbar-search",
                    ],
                )

                category_filter = gr.Dropdown(
                    choices=["All categories"],
                    value="All categories",
                    show_label=False,
                    elem_classes=[
                        "owl-input",
                        "owl-toolbar-category",
                    ],
                )

                flagged_only = gr.Checkbox(
                    label="Flagged only",
                    elem_classes=["owl-toggle"],
                )

            table_html = gr.HTML(_table_html([]))

            # Edit receipt card
            with gr.Column(
                scale=0,
                elem_classes=[
                    "owl-card",
                    "owl-card--stack",
                    "owl-edit-receipt",
                ],
            ):
                gr.HTML(
                    '<span class="owl-card-title owl-edit-title">Edit a receipt</span>'
                )

                with gr.Row(elem_classes=["owl-inline-row"]):
                    receipt_select = gr.Dropdown(
                        choices=[],
                        label="Receipt",
                        elem_classes=["owl-input", "owl-grow"],
                    )

                    category_select = gr.Dropdown(
                        choices=[],
                        label="Category",
                        elem_classes=["owl-input"],
                    )

                    save_btn = gr.Button(
                        "Save",
                        elem_classes=["owl-btn", "owl-btn-primary"],
                    )

                    delete_btn = gr.Button(
                        "Delete",
                        elem_classes=["owl-btn", "owl-btn-danger"],
                    )

        with gr.Row(elem_classes=["owl-actionbar"]):
            gr.HTML('<span class="owl-muted-text" id="perch-status"></span>')
            gr.HTML("")

    def _load(search="", category="All categories", flagged=False):
        receipts = receipt_service.list_receipts(
            search=search,
            category=category,
            flagged_only=flagged,
        )

        cats = ["All categories"] + db.category_names()
        choices = _receipt_choices(receipts)

        return (
            _table_html(receipts),
            gr.update(choices=cats),
            gr.update(
                choices=choices,
                value=(choices[0][1] if choices else None),
            ),
            gr.update(choices=db.category_names()),
        )

    def refresh_filtered(search, category, flagged):
        receipts = receipt_service.list_receipts(
            search=search,
            category=category,
            flagged_only=flagged,
        )

        choices = _receipt_choices(receipts)

        return (
            _table_html(receipts),
            gr.update(
                choices=choices,
                value=(choices[0][1] if choices else None),
            ),
        )

    search_box.change(
        refresh_filtered,
        inputs=[search_box, category_filter, flagged_only],
        outputs=[table_html, receipt_select],
    )

    category_filter.change(
        refresh_filtered,
        inputs=[search_box, category_filter, flagged_only],
        outputs=[table_html, receipt_select],
    )

    flagged_only.change(
        refresh_filtered,
        inputs=[search_box, category_filter, flagged_only],
        outputs=[table_html, receipt_select],
    )

    def on_select(receipt_id):
        if receipt_id is None:
            return gr.update(value=None)

        r = db.get_receipt(int(receipt_id))
        return gr.update(value=r["category"] if r else None)

    receipt_select.change(
        on_select,
        inputs=receipt_select,
        outputs=category_select,
    )

    def on_save(receipt_id, category):
        if receipt_id is None or not category:
            gr.Warning("Pick a receipt and a category first.")
            return gr.update()

        receipt_service.update_receipt_category(
            int(receipt_id),
            category,
        )

        gr.Info("Category updated.")
        return gr.update()

    def on_delete(receipt_id, search, category, flagged):
        if receipt_id is None:
            gr.Warning("Pick a receipt to delete first.")
            return _table_html([]), gr.update(), gr.update()

        receipt_service.delete_receipt(int(receipt_id))

        gr.Info("Receipt deleted.")

        table, select_update = refresh_filtered(
            search,
            category,
            flagged,
        )

        return table, select_update, gr.update(value=None)

    save_btn.click(
        on_save,
        inputs=[receipt_select, category_select],
        outputs=category_select,
    ).then(
        refresh_filtered,
        inputs=[search_box, category_filter, flagged_only],
        outputs=[table_html, receipt_select],
    )

    delete_btn.click(
        on_delete,
        inputs=[
            receipt_select,
            search_box,
            category_filter,
            flagged_only,
        ],
        outputs=[table_html, receipt_select, category_select],
    )

    return {
        "screen": screen,
        "load": _load,
        "load_inputs": [
            search_box,
            category_filter,
            flagged_only,
        ],
        "load_outputs": [
            table_html,
            category_filter,
            receipt_select,
            category_select,
        ],
        "search_box": search_box,
        "category_filter": category_filter,
        "flagged_only": flagged_only,
    }
