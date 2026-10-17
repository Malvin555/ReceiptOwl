"""Treasure — the payoff screen: totals, and the CSV / tax-PDF / anomaly"""

from __future__ import annotations

import gradio as gr

from services import receipt_service
from ui.components.blocks import screen_heading
from ui.icons import icon


def _stats_html(summary: dict) -> str:
    def stat(label, value, note, small=False):
        cls = "owl-stat-value owl-stat-value--sm" if small else "owl-stat-value"
        return f'<div class="owl-stat"><span class="owl-stat-label">{label}</span><span class="{cls}">{value}</span><span class="owl-stat-note">{note}</span></div>'

    return (
        '<div class="owl-card owl-stats">'
        + stat(
            "Total expenses",
            f"${summary['total']:,.2f}",
            f"{summary['unique_count']} receipt(s)",
        )
        + stat("Sales tax", f"${summary['tax']:,.2f}", "tracked across receipts")
        + stat(
            "Est. deductible",
            f"${summary['deductible']:,.2f}",
            "based on category defaults",
        )
        + stat(
            "Top category",
            summary["top_category"],
            f"{summary['top_pct']}% of spend",
            small=True,
        )
        + "</div>"
    )


def _report_card(title: str, icon_name: str, info: dict, desc: str) -> str:
    return (
        '<div class="owl-card owl-report">'
        f'<div class="owl-report-type"><span class="owl-report-icon">{icon(icon_name, 20)}</span>'
        f'<span class="owl-card-title">{title}</span></div>'
        f'<p class="owl-report-file">{info["filename"]}</p>'
        f'<p class="owl-report-desc">{desc}</p>'
        '<div class="owl-report-spacer"></div>'
        f'<div class="owl-report-foot"><span class="owl-report-meta">{info["meta"]}</span></div></div>'
    )


def build(ctx: dict) -> dict:
    with gr.Column(visible=False, elem_classes=["owl-screen"]) as screen:
        with gr.Column(elem_classes=["owl-workspace"]):
            gr.HTML(
                screen_heading(
                    "Treasure",
                    "Your tax-ready exports — generated locally, updated automatically.",
                )
            )

            stats_html = gr.HTML(_stats_html(receipt_service.get_summary()))

            with gr.Row(elem_classes=["owl-reports"]):
                csv_card = gr.HTML("")
                pdf_card = gr.HTML("")
                anomaly_card = gr.HTML("")
            with gr.Row():
                csv_dl = gr.DownloadButton(
                    "Download CSV", elem_classes=["owl-btn", "owl-btn-secondary"]
                )
                pdf_dl = gr.DownloadButton(
                    "Download tax PDF", elem_classes=["owl-btn", "owl-btn-secondary"]
                )
                anomaly_dl = gr.DownloadButton(
                    "Download anomalies", elem_classes=["owl-btn", "owl-btn-secondary"]
                )

            with gr.Column(elem_classes=["owl-folder"]):
                gr.HTML('<span class="owl-card-title">Organized folder</span>')
                with gr.Row(elem_classes=["owl-folder-row"]):
                    folder_path = gr.HTML("", elem_classes=["owl-folder-path"])
                    open_btn = gr.Button(
                        "Open folder", elem_classes=["owl-btn", "owl-btn-secondary"]
                    )
                    refresh_btn = gr.Button(
                        "Regenerate reports", elem_classes=["owl-btn", "owl-btn-accent"]
                    )

        with gr.Row(elem_classes=["owl-actionbar"]):
            gr.HTML(
                '<span class="owl-muted-text">Reports regenerate automatically after each Hunt run.</span>'
            )
            gr.HTML("")

    def _load():
        summary = receipt_service.get_summary()
        reports = receipt_service.regenerate_reports()
        folder = receipt_service.organized_folder()
        return (
            _stats_html(summary),
            _report_card(
                "Receipts CSV",
                "file-text",
                reports["csv"],
                "Every receipt, flagged and categorized.",
            ),
            _report_card(
                "Tax summary PDF",
                "file-text",
                reports["pdf"],
                "Totals by category, ready to hand off.",
            ),
            _report_card(
                "Anomaly report",
                "file-warning",
                reports["anomalies"],
                "Duplicates and low-confidence reads.",
            ),
            str(reports["csv"]["path"]),
            str(reports["pdf"]["path"]),
            str(reports["anomalies"]["path"]),
            f'<span class="owl-folder-id">{icon("folder-open", 16)}<code>{folder["path"]}</code></span><span class="owl-muted-text">{folder["size_label"]}</span>',
        )

    outputs = [
        stats_html,
        csv_card,
        pdf_card,
        anomaly_card,
        csv_dl,
        pdf_dl,
        anomaly_dl,
        folder_path,
    ]
    refresh_btn.click(_load, outputs=outputs)

    def _open():
        ok = receipt_service.open_folder()
        if ok:
            gr.Info("Opening the folder…")
        else:
            gr.Warning(
                "Can't open a file browser from this environment — use the path shown above."
            )

    open_btn.click(_open)

    return {"screen": screen, "load": _load, "load_outputs": outputs}
