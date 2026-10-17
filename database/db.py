# SQLite connection

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from config import get_storage_root

_SCHEMA = """
CREATE TABLE IF NOT EXISTS receipts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_hash TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_kind TEXT NOT NULL,
    receipt_date TEXT,
    vendor TEXT,
    amount REAL,
    tax REAL,
    currency TEXT DEFAULT 'USD',
    category TEXT,
    confidence REAL DEFAULT 0,
    ocr_text TEXT DEFAULT '',
    extraction_source TEXT DEFAULT 'heuristic',
    is_duplicate INTEGER DEFAULT 0,
    duplicate_of INTEGER,
    flags TEXT DEFAULT '[]',
    status TEXT DEFAULT 'processed',
    error TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    deductible_default INTEGER DEFAULT 0,
    sort_order INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""

_DEFAULT_CATEGORIES = [
    ("Software", True),
    ("Office supplies", True),
    ("Meals", False),
    ("Coworking", True),
    ("Travel", True),
    ("Other", False),
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def db_path() -> Path:
    return get_storage_root() / "receiptowl.db"


def originals_dir() -> Path:
    d = get_storage_root() / "originals"
    d.mkdir(parents=True, exist_ok=True)
    return d


def reports_dir() -> Path:
    d = get_storage_root() / "reports"
    d.mkdir(parents=True, exist_ok=True)
    return d


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(db_path(), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with connect() as conn:
        conn.executescript(_SCHEMA)
        existing = {r["name"] for r in conn.execute("SELECT name FROM categories")}
        for i, (name, deductible) in enumerate(_DEFAULT_CATEGORIES):
            if name not in existing:
                conn.execute(
                    "INSERT INTO categories (name, deductible_default, sort_order) VALUES (?, ?, ?)",
                    (name, int(deductible), i),
                )


def get_setting(key: str, default: str | None = None) -> str | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else default


def set_setting(key: str, value: str) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )


def list_categories() -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM categories ORDER BY sort_order, id"
        ).fetchall()
        return [dict(r) for r in rows]


def category_names() -> list[str]:
    return [c["name"] for c in list_categories()]


def add_category(name: str, deductible_default: bool = False) -> int:
    name = name.strip()
    if not name:
        raise ValueError("Category name can't be empty.")
    with connect() as conn:
        existing = conn.execute(
            "SELECT id FROM categories WHERE name = ? COLLATE NOCASE", (name,)
        ).fetchone()
        if existing:
            raise ValueError(f'"{name}" already exists.')
        max_order = conn.execute(
            "SELECT COALESCE(MAX(sort_order), -1) AS m FROM categories"
        ).fetchone()["m"]
        cur = conn.execute(
            "INSERT INTO categories (name, deductible_default, sort_order) VALUES (?, ?, ?)",
            (name, int(deductible_default), max_order + 1),
        )
        return cur.lastrowid


def update_category(category_id: int, name: str, deductible_default: bool) -> None:
    name = name.strip()
    if not name:
        raise ValueError("Category name can't be empty.")
    with connect() as conn:
        clash = conn.execute(
            "SELECT id FROM categories WHERE name = ? COLLATE NOCASE AND id != ?",
            (name, category_id),
        ).fetchone()
        if clash:
            raise ValueError(f'"{name}" already exists.')
        old = conn.execute(
            "SELECT name FROM categories WHERE id = ?", (category_id,)
        ).fetchone()
        conn.execute(
            "UPDATE categories SET name = ?, deductible_default = ? WHERE id = ?",
            (name, int(deductible_default), category_id),
        )
        if old and old["name"] != name:
            conn.execute(
                "UPDATE receipts SET category = ? WHERE category = ?",
                (name, old["name"]),
            )


def delete_category(category_id: int) -> None:
    with connect() as conn:
        row = conn.execute(
            "SELECT name FROM categories WHERE id = ?", (category_id,)
        ).fetchone()
        if not row:
            return
        in_use = conn.execute(
            "SELECT COUNT(*) AS n FROM receipts WHERE category = ?", (row["name"],)
        ).fetchone()["n"]
        if in_use:
            raise ValueError(
                f'"{row["name"]}" is used by {in_use} receipt(s) — reassign them first.'
            )
        conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))


def insert_receipt(record: dict[str, Any]) -> int:
    now = _now()
    record = {**record, "created_at": now, "updated_at": now}
    record.setdefault("flags", "[]")
    if isinstance(record.get("flags"), (list, tuple)):
        record["flags"] = json.dumps(list(record["flags"]))
    cols = [
        "file_hash",
        "file_name",
        "file_path",
        "file_kind",
        "receipt_date",
        "vendor",
        "amount",
        "tax",
        "currency",
        "category",
        "confidence",
        "ocr_text",
        "extraction_source",
        "is_duplicate",
        "duplicate_of",
        "flags",
        "status",
        "error",
        "created_at",
        "updated_at",
    ]
    values = [record.get(c) for c in cols]
    with connect() as conn:
        cur = conn.execute(
            f"INSERT INTO receipts ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})",
            values,
        )
        return cur.lastrowid


def update_receipt(receipt_id: int, **fields: Any) -> None:
    if not fields:
        return
    fields["updated_at"] = _now()
    if isinstance(fields.get("flags"), (list, tuple)):
        fields["flags"] = json.dumps(list(fields["flags"]))
    sets = ", ".join(f"{k} = ?" for k in fields)
    with connect() as conn:
        conn.execute(
            f"UPDATE receipts SET {sets} WHERE id = ?", (*fields.values(), receipt_id)
        )


def delete_receipt(receipt_id: int) -> None:
    with connect() as conn:
        conn.execute("DELETE FROM receipts WHERE id = ?", (receipt_id,))


def get_receipt(receipt_id: int) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM receipts WHERE id = ?", (receipt_id,)
        ).fetchone()
        return _row_to_dict(row) if row else None


def list_receipts(
    search: str = "",
    category: str = "",
    flagged_only: bool = False,
    order: str = "receipt_date DESC, id DESC",
) -> list[dict[str, Any]]:
    query = "SELECT * FROM receipts WHERE 1=1"
    params: list[Any] = []
    if search:
        query += " AND (vendor LIKE ? OR file_name LIKE ?)"
        like = f"%{search}%"
        params += [like, like]
    if category and category != "All categories":
        query += " AND category = ?"
        params.append(category)
    if flagged_only:
        query += " AND flags != '[]' AND flags IS NOT NULL"
    query += f" ORDER BY {order}"
    with connect() as conn:
        rows = conn.execute(query, params).fetchall()
        return [_row_to_dict(r) for r in rows]


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    d = dict(row)
    try:
        d["flags"] = json.loads(d.get("flags") or "[]")
    except (ValueError, TypeError):
        d["flags"] = []
    return d


def find_duplicate_candidates() -> list[tuple[int, int]]:
    """Return (newer_id, original_id) pairs sharing vendor+amount+date or file hash."""
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, file_hash, vendor, amount, receipt_date FROM receipts ORDER BY id"
        ).fetchall()
    seen: dict[tuple, int] = {}
    pairs: list[tuple[int, int]] = []
    for r in rows:
        key = (r["file_hash"],)
        soft_key = (
            (r["vendor"] or "").strip().lower(),
            round(r["amount"] or 0, 2),
            r["receipt_date"],
        )
        match_id = seen.get(key) or seen.get(soft_key)
        if match_id:
            pairs.append((r["id"], match_id))
        else:
            seen[key] = r["id"]
            seen[soft_key] = r["id"]
    return pairs


def mark_duplicates() -> int:
    """Recompute duplicate flags across all receipts. Returns count marked."""
    pairs = find_duplicate_candidates()
    with connect() as conn:
        conn.execute("UPDATE receipts SET is_duplicate = 0, duplicate_of = NULL")
        for dup_id, original_id in pairs:
            flags_row = conn.execute(
                "SELECT flags FROM receipts WHERE id = ?", (dup_id,)
            ).fetchone()
            try:
                flags = json.loads(flags_row["flags"] or "[]") if flags_row else []
            except (ValueError, TypeError):
                flags = []
            if "dupe" not in flags:
                flags.append("dupe")
            conn.execute(
                "UPDATE receipts SET is_duplicate = 1, duplicate_of = ?, flags = ? WHERE id = ?",
                (original_id, json.dumps(flags), dup_id),
            )
    return len(pairs)


def get_summary() -> dict[str, Any]:
    with connect() as conn:
        all_rows = conn.execute("SELECT * FROM receipts").fetchall()
    rows = [_row_to_dict(r) for r in all_rows]
    unique = [r for r in rows if not r["is_duplicate"]]
    total = sum((r["amount"] or 0) for r in unique)
    tax = sum((r["tax"] or 0) for r in unique)
    deductible_cats = {c["name"] for c in list_categories() if c["deductible_default"]}
    deductible = sum(
        (r["amount"] or 0) for r in unique if r.get("category") in deductible_cats
    )
    flagged = [r for r in rows if r["flags"]]
    dupes = [r for r in rows if r["is_duplicate"]]

    by_cat: dict[str, float] = {}
    for r in unique:
        by_cat[r.get("category") or "Other"] = by_cat.get(
            r.get("category") or "Other", 0
        ) + (r["amount"] or 0)
    top_category, top_amount = ("—", 0.0)
    if by_cat:
        top_category, top_amount = max(by_cat.items(), key=lambda kv: kv[1])
    top_pct = round((top_amount / total) * 100) if total else 0

    return {
        "total_count": len(rows),
        "unique_count": len(unique),
        "flagged_count": len(flagged),
        "dupe_count": len(dupes),
        "total": total,
        "tax": tax,
        "deductible": deductible,
        "top_category": top_category,
        "top_amount": top_amount,
        "top_pct": top_pct,
    }


def reset_workspace() -> None:
    """Danger Zone: clear receipt records. Original files on disk are untouched."""
    with connect() as conn:
        conn.execute("DELETE FROM receipts")
    for f in reports_dir().glob("*"):
        try:
            if f.is_file():
                f.unlink()
        except OSError:
            pass


init_db()
