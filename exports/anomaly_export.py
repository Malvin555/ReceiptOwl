from __future__ import annotations

from pathlib import Path
from typing import Any

from pipeline.anomalies import flag_label


def write(receipts: list[dict[str, Any]], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    flagged = [r for r in receipts if r.get("flags")]
    lines = [f"ReceiptOwl anomaly report · {len(flagged)} finding(s)", ""]
    for r in flagged:
        labels = ", ".join(flag_label(f) for f in r.get("flags", []))
        lines.append(
            f"- {r.get('receipt_date') or '—'} · {r.get('vendor') or 'Unknown'} · "
            f"${(r.get('amount') or 0):,.2f} · {labels}"
        )
    if not flagged:
        lines.append("Nothing flagged.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
