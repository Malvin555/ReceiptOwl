"""Perch: review extracted receipt data before it becomes a report."""

from __future__ import annotations

from html import escape

import gradio as gr

from ui import mock
from ui.components.blocks import pill, progress, screen_heading
from ui.icons import icon


def _conf_tone(pct: int) -> str:
    return "success" if pct >= 85 else "warning" if pct >= 70 else "error"


def _flag_html(flag: str | None) -> str:
    if flag is None:
        return "—"
    glyph = "copy" if flag == "Dupe" else "circle-alert"
    return f'<span class="owl-flag owl-flag--{flag.lower()}">{icon(glyph)}</span><span class="owl-flag owl-flag--{flag.lower()}">{flag}</span>'


def _row(r: dict) -> str:
    tone = _conf_tone(r["conf"])
    options = "".join(
        f"<option{' selected' if c == r['category'] else ''}>{escape(c)}</option>"
        for c in mock.CATEGORIES
    )
    tax = escape(r["tax"]) if r["tax"] else '<span class="owl-tax-missing">—</span>'
    cls = {"flagged": " owl-row--flagged", "duplicate": " owl-row--duplicate"}.get(
        r["state"], ""
    )
    return (
        f'<div class="owl-row{cls}">'
        '<span class="owl-col-check"><input type="checkbox" class="owl-check" aria-label="Select receipt"></span>'
        f'<span class="owl-col-date">{escape(r["date"])}</span>'
        f'<span class="owl-col-vendor">{escape(r["vendor"])}</span>'
        f'<span class="owl-col-amount">{escape(r["amount"])}</span>'
        f'<span class="owl-col-tax">{tax}</span>'
        f'<span class="owl-col-cat"><select class="owl-select" aria-label="Category">{options}</select></span>'
        f'<span class="owl-col-conf">{progress(r["conf"], tone, 48)}'
        f'<span class="owl-conf-text owl-conf--{tone}">{r["conf"]}%</span></span>'
        f'<span class="owl-col-flag">{_flag_html(r["flag"])}</span></div>'
    )


def _table() -> str:
    s = mock.PERCH_SUMMARY
    head = (
        '<div class="owl-table-head"><span class="owl-col-check"><input type="checkbox" class="owl-check" aria-label="Select all"></span>'
        '<span class="owl-col-date">Date</span><span class="owl-col-vendor">Vendor</span>'
        '<span class="owl-col-amount">Amount</span><span class="owl-col-tax">Tax</span>'
        '<span class="owl-col-cat">Category</span><span class="owl-col-conf">Confidence</span>'
        '<span class="owl-col-flag">Flag</span></div>'
    )
    rows = "".join(_row(r) for r in mock.RECEIPTS)
    foot = (
        f'<div class="owl-table-foot"><span>Showing {s["shown"]} of {s["total"]} · scroll for more</span>'
        "<span>No unsaved changes · USD</span></div>"
    )
    return f'<div class="owl-table"><div class="owl-table-scroll">{head}{rows}</div>{foot}</div>'


def _summary() -> str:
    s = mock.PERCH_SUMMARY
    return (
        '<div class="owl-summary">'
        f'{pill(f"{s["total"]} receipts", "success")}<span class="dot">·</span>'
        f'{pill(f"{s["flagged"]} flagged", "warning2")}<span class="dot">·</span>'
        f"{pill(f'{s["dupes"]} dupes', 'neutral', outlined=True)}"
        '<span class="owl-muted-text" style="margin-left:0">Duplicates are excluded from report totals.</span></div>'
    )


def build() -> dict:
    s = mock.PERCH_SUMMARY
    with gr.Column(elem_classes="owl-screen", visible=False) as screen:
        with gr.Column(elem_classes="owl-workspace owl-workspace--tight"):
            gr.HTML(
                screen_heading(
                    "Perch",
                    "Review the details before they become your reports.",
                    right=pill(s["period"], "neutral"),
                    desc_size="15",
                )
            )
            gr.HTML(_summary())
            with gr.Row(elem_classes="owl-toolbar"):
                search = gr.Textbox(
                    placeholder="Search vendors or receipts",
                    show_label=False,
                    container=False,
                    elem_classes=["owl-input", "owl-search", "owl-toolbar-search"],
                )
                category = gr.Dropdown(
                    choices=["All categories"] + mock.CATEGORIES,
                    value="All categories",
                    show_label=False,
                    container=False,
                    filterable=False,
                    elem_classes=["owl-input", "owl-toolbar-category"],
                )
                flagged_only = gr.Checkbox(
                    label="Flagged only",
                    value=False,
                    container=False,
                    elem_classes="owl-toggle",
                )
                save = gr.Button(
                    "Save changes",
                    interactive=False,
                    elem_classes=["owl-btn", "owl-btn-disabled"],
                )
            gr.HTML(_table())
        with gr.Row(elem_classes="owl-actionbar"):
            export = gr.Button(
                "Export CSV",
                elem_classes=["owl-btn", "owl-btn-secondary", "owl-ic-download"],
            )
            with gr.Row(elem_classes="owl-actionbar-right"):
                gr.HTML(
                    f'<span class="owl-muted-text">{s["unique"]} unique receipts in reports</span>'
                )
                to_treasure = gr.Button(
                    "Go to Treasure",
                    elem_classes=["owl-btn", "owl-btn-primary", "owl-ic-arrow-right"],
                )
    return {
        "screen": screen,
        "search": search,
        "category": category,
        "flagged_only": flagged_only,
        "save": save,
        "export": export,
        "to_treasure": to_treasure,
    }
