# Tax-summary PDF
from __future__ import annotations

from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

_AMBER = colors.HexColor("#C77B30")
_BARK = colors.HexColor("#2B2117")
_FEATHER = colors.HexColor("#6B6357")
_BORDER = colors.HexColor("#DED8CF")


def write(
    summary: dict[str, Any],
    receipts: list[dict[str, Any]],
    period_label: str,
    path: Path,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "OwlTitle", parent=styles["Title"], textColor=_BARK, fontSize=20
    )
    sub_style = ParagraphStyle(
        "OwlSub", parent=styles["Normal"], textColor=_FEATHER, fontSize=10
    )
    h2 = ParagraphStyle(
        "OwlH2", parent=styles["Heading2"], textColor=_BARK, fontSize=13, spaceBefore=16
    )

    doc = SimpleDocTemplate(
        str(path), pagesize=letter, topMargin=0.75 * inch, bottomMargin=0.75 * inch
    )
    story = [
        Paragraph("ReceiptOwl · Tax Summary", title_style),
        Paragraph(
            f"{period_label} · Expense summary and bookkeeping assistance, not tax advice.",
            sub_style,
        ),
        Spacer(1, 16),
    ]

    totals_data = [
        ["Total", "Tax", "Deductible", "Unique receipts"],
        [
            f"${summary['total']:,.2f}",
            f"${summary['tax']:,.2f}",
            f"${summary['deductible']:,.2f}",
            str(summary["unique_count"]),
        ],
    ]
    totals_table = Table(totals_data, colWidths=[1.6 * inch] * 4)
    totals_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), _BORDER),
                ("TEXTCOLOR", (0, 0), (-1, 0), _BARK),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.5, _BORDER),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(totals_table)

    story.append(Paragraph("By category", h2))
    by_cat: dict[str, dict[str, float]] = {}
    for r in receipts:
        if r.get("is_duplicate"):
            continue
        cat = r.get("category") or "Other"
        bucket = by_cat.setdefault(cat, {"amount": 0.0, "count": 0})
        bucket["amount"] += r.get("amount") or 0
        bucket["count"] += 1

    cat_rows = [["Category", "Receipts", "Amount"]]
    for cat, bucket in sorted(by_cat.items(), key=lambda kv: -kv[1]["amount"]):
        cat_rows.append([cat, str(int(bucket["count"])), f"${bucket['amount']:,.2f}"])
    if len(cat_rows) == 1:
        cat_rows.append(["No receipts yet", "—", "$0.00"])

    cat_table = Table(cat_rows, colWidths=[3 * inch, 1.5 * inch, 1.5 * inch])
    cat_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), _BORDER),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.5, _BORDER),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(cat_table)

    story.append(Paragraph("Flagged for review", h2))
    flagged = [r for r in receipts if r.get("flags")]
    if flagged:
        flag_rows = [["Date", "Vendor", "Amount", "Reason"]]
        for r in flagged[:40]:
            flag_rows.append(
                [
                    r.get("receipt_date") or "—",
                    r.get("vendor") or "—",
                    f"${(r.get('amount') or 0):,.2f}",
                    ", ".join(r.get("flags") or []),
                ]
            )
        flag_table = Table(
            flag_rows, colWidths=[1.2 * inch, 2.3 * inch, 1.2 * inch, 1.3 * inch]
        )
        flag_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), _BORDER),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("GRID", (0, 0), (-1, -1), 0.5, _BORDER),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(flag_table)
    else:
        story.append(Paragraph("Nothing flagged.", styles["Normal"]))

    doc.build(story)
    return path
