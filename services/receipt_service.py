from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from database import db
from exports import anomaly_export, csv_export, organize, pdf_export
from pipeline import anomalies, categorize, extract, intake, ocr

_CANCEL_FLAGS: dict[str, bool] = {}


def request_cancel(job_id: str) -> None:
    if job_id:
        _CANCEL_FLAGS[job_id] = True


def _is_cancelled(job_id: str) -> bool:
    return bool(job_id and _CANCEL_FLAGS.get(job_id))


def _now_str() -> str:
    return datetime.now(timezone.utc).strftime("%H:%M:%S")


def preview_queue(files) -> list[dict[str, Any]]:
    return intake.preview(files)


def process_batch(files, job_id: str, model: str) -> Iterator[dict[str, Any]]:

    _CANCEL_FLAGS[job_id] = False
    log: list[tuple[str, str, str]] = []
    categories = db.category_names()

    def emit(
        phase: str, done: int, total: int, steps: dict[str, str]
    ) -> dict[str, Any]:
        return {
            "phase": phase,
            "done": done,
            "total": total,
            "pct": round((done / total) * 100) if total else 0,
            "steps": dict(steps),
            "log": list(log),
            "cancelled": _is_cancelled(job_id),
        }

    previewed = intake.preview(files)
    total = len(previewed)
    steps = {
        "reading": "active",
        "extracting": "waiting",
        "categorizing": "waiting",
        "reporting": "waiting",
    }

    log.append((_now_str(), "INFO", f"Batch started · {total} file(s) · {model}"))
    yield emit("reading", 0, total, steps)

    if total == 0:
        log.append((_now_str(), "WARN", "No supported files in this batch."))
        steps["reading"] = "done"
        yield emit("done", 0, 0, steps)
        return

    staged = intake.stage(files)
    pdfs = sum(1 for s in staged if s["kind"] == "pdf")
    images = len(staged) - pdfs
    log.append((_now_str(), "OK", f"Reading complete · {pdfs} PDFs, {images} images"))
    steps["reading"] = "done"
    steps["extracting"] = "active"
    steps["categorizing"] = "active"
    yield emit("extracting", 0, total, steps)

    done = 0
    for item in staged:
        if _is_cancelled(job_id):
            log.append((_now_str(), "INFO", "Job cancelled by user"))
            yield emit("cancelled", done, total, steps)
            return

        try:
            text, method = ocr.extract_text(Path(item["path"]), item["kind"])
            fields = extract.extract_fields(text, item["name"], model=model)
            category, cat_conf = categorize.categorize(
                fields.get("vendor"), text, categories
            )
            confidence = min(fields.get("confidence", 50.0), 100.0)
            flags = anomalies.detect(
                fields.get("amount"), fields.get("tax"), confidence
            )

            db.insert_receipt(
                {
                    "file_hash": item["hash"],
                    "file_name": item["name"],
                    "file_path": item["path"],
                    "file_kind": item["kind"],
                    "receipt_date": fields.get("date"),
                    "vendor": fields.get("vendor"),
                    "amount": fields.get("amount"),
                    "tax": fields.get("tax"),
                    "category": category,
                    "confidence": confidence,
                    "ocr_text": text,
                    "extraction_source": fields.get("source", "heuristic"),
                    "flags": flags,
                    "status": "processed",
                }
            )

            done += 1
            if confidence < 70:
                log.append(
                    (
                        _now_str(),
                        "WARN",
                        f"{item['name']} · low confidence · review queued",
                    )
                )
            else:
                amt = (
                    f"${fields['amount']:.2f}"
                    if fields.get("amount") is not None
                    else "amount unknown"
                )
                vendor = fields.get("vendor") or "Unknown vendor"
                log.append(
                    (
                        _now_str(),
                        "OK",
                        f"{item['name']} → {vendor} · {amt} · {category}",
                    )
                )
        except Exception as exc:
            done += 1
            db.insert_receipt(
                {
                    "file_hash": item["hash"],
                    "file_name": item["name"],
                    "file_path": item["path"],
                    "file_kind": item["kind"],
                    "status": "failed",
                    "error": f"{type(exc).__name__}: {exc}",
                    "flags": ["review"],
                }
            )
            log.append(
                (_now_str(), "WARN", f"{item['name']} · failed to process · {exc}")
            )

        if done < total:
            log.append(
                (_now_str(), "INFO", f"Extracting receipt {done + 1} of {total}…")
            )
        yield emit("extracting", done, total, steps)

    steps["extracting"] = "done"
    steps["categorizing"] = "done"
    steps["reporting"] = "active"
    yield emit("reporting", total, total, steps)

    dupes = db.mark_duplicates()
    if dupes:
        log.append((_now_str(), "INFO", f"Found {dupes} duplicate receipt(s)"))
    regenerate_reports()
    log.append((_now_str(), "OK", "Reports regenerated · CSV, PDF & anomalies"))
    steps["reporting"] = "done"
    yield emit("done", total, total, steps)


def list_receipts(
    search: str = "", category: str = "All categories", flagged_only: bool = False
):
    return db.list_receipts(search=search, category=category, flagged_only=flagged_only)


def update_receipt_category(receipt_id: int, category: str) -> None:
    db.update_receipt(receipt_id, category=category)
    regenerate_reports()


def delete_receipt(receipt_id: int) -> None:
    db.delete_receipt(receipt_id)
    regenerate_reports()


def get_summary() -> dict[str, Any]:
    return db.get_summary()


def reset_workspace() -> None:
    db.reset_workspace()
    regenerate_reports()


def regenerate_reports() -> dict[str, Any]:
    """Rebuild the CSV / PDF / anomaly-TXT files Treasure links to. Cheap
    enough (small per-user datasets) to just always run after a mutation."""
    receipts = db.list_receipts()
    summary = db.get_summary()
    label = organize.period_label()
    out_dir = db.reports_dir()

    csv_path = csv_export.write(receipts, out_dir / f"receipts_{label}.csv")
    pdf_path = pdf_export.write(
        summary, receipts, label, out_dir / f"tax-report_{label}.pdf"
    )
    txt_path = anomaly_export.write(receipts, out_dir / f"anomalies_{label}.txt")

    def meta(path: Path, unit: str) -> str:
        size = path.stat().st_size if path.exists() else 0
        from exports.organize import format_size

        if unit == "rows":
            return f"{len(receipts)} rows · {format_size(size)}"
        if unit == "findings":
            n = sum(1 for r in receipts if r.get("flags"))
            return f"{n} finding(s) · {format_size(size)}"
        return format_size(size)

    return {
        "csv": {
            "path": csv_path,
            "filename": csv_path.name,
            "meta": meta(csv_path, "rows"),
        },
        "pdf": {
            "path": pdf_path,
            "filename": pdf_path.name,
            "meta": meta(pdf_path, "size"),
        },
        "anomalies": {
            "path": txt_path,
            "filename": txt_path.name,
            "meta": meta(txt_path, "findings"),
        },
    }


def organized_folder() -> dict[str, Any]:
    return organize.summary()


def open_folder() -> bool:
    return organize.try_open_folder(db.get_storage_root())
