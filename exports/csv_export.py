# CSV export

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from pipeline.anomalies import flag_label, primary_flag

COLUMNS = [
    "Date",
    "Vendor",
    "Amount",
    "Tax",
    "Category",
    "Confidence",
    "Flag",
    "Duplicate",
]


def write(receipts: list[dict[str, Any]], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(COLUMNS)
        for r in receipts:
            writer.writerow(
                [
                    r.get("receipt_date") or "",
                    r.get("vendor") or "",
                    f"{r.get('amount') or 0:.2f}",
                    f"{r.get('tax'):.2f}" if r.get("tax") is not None else "",
                    r.get("category") or "",
                    f"{round(r.get('confidence') or 0)}%",
                    flag_label(primary_flag(r.get("flags") or [])) or "",
                    "Yes" if r.get("is_duplicate") else "No",
                ]
            )
    return path
