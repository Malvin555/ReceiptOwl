"""Mock data used while the UI is built without a backend."""

QUEUE_SUMMARY = {
    "count": 47,
    "pdfs": 32,
    "images": 15,
    "size": "28.6 MB",
    "eta": "about 2 minutes",
}

QUEUE_PREVIEW = [
    {"name": "2026-09-28_adobe.pdf", "kind": "pdf", "meta": "PDF · 148 KB"},
    {"name": "2026-09-26_amazon.jpg", "kind": "image", "meta": "JPG · 2.1 MB"},
    {"name": "2026-09-24_notion.pdf", "kind": "pdf", "meta": "PDF · 92 KB"},
    {"name": "2026-09-22_blue-bottle.jpg", "kind": "image", "meta": "JPG · 1.4 MB"},
    {"name": "2026-09-20_wework.pdf", "kind": "pdf", "meta": "PDF · 204 KB"},
]
QUEUE_MORE = 42

HUNT_PROGRESS = {
    "label": "Extracting receipt details",
    "done": 23,
    "total": 47,
    "pct": 48,
}

HUNT_STEPS = [
    {
        "icon": "check",
        "title": "Reading",
        "detail": "47 files loaded",
        "state": "done",
        "pill": "Complete",
    },
    {
        "icon": "loader-circle",
        "title": "Extracting",
        "detail": "23 of 47 receipts",
        "state": "active",
        "pill": "In progress",
    },
    {
        "icon": "circle",
        "title": "Categorizing",
        "detail": "Your category rules",
        "state": "waiting",
        "pill": "Waiting",
    },
    {
        "icon": "circle",
        "title": "Reporting",
        "detail": "CSV, PDF & anomalies",
        "state": "waiting",
        "pill": "Waiting",
    },
]

HUNT_LOG = [
    ("10:42:01", "INFO", "Batch started · 47 files · gemma2:2b"),
    ("10:42:02", "OK", "Reading complete · 32 PDFs, 15 images"),
    ("10:42:19", "OK", "adobe.pdf → Adobe · $59.99 · Software"),
    ("10:42:22", "OK", "amazon.jpg → Amazon · $128.40 · Office supplies"),
    ("10:42:24", "WARN", "blue-bottle.jpg · low confidence · review queued"),
    ("10:42:27", "OK", "wework.pdf → WeWork · $350.00 · Coworking"),
    ("10:42:29", "INFO", "Extracting receipt 24 of 47…"),
]
HUNT_TIMING = "Elapsed 00:29 · about 1 minute remaining"

CATEGORIES = ["Software", "Office supplies", "Meals", "Coworking", "Travel", "Other"]

RECEIPTS = [
    {
        "date": "Sep 28",
        "vendor": "Adobe",
        "amount": "59.99",
        "tax": "5.45",
        "category": "Software",
        "conf": 98,
        "flag": None,
        "state": "normal",
    },
    {
        "date": "Sep 26",
        "vendor": "Amazon",
        "amount": "128.40",
        "tax": "11.67",
        "category": "Office supplies",
        "conf": 94,
        "flag": None,
        "state": "normal",
    },
    {
        "date": "Sep 24",
        "vendor": "Notion",
        "amount": "18.00",
        "tax": "1.64",
        "category": "Software",
        "conf": 96,
        "flag": None,
        "state": "normal",
    },
    {
        "date": "Sep 22",
        "vendor": "Blue Bottle",
        "amount": "24.80",
        "tax": "2.25",
        "category": "Meals",
        "conf": 64,
        "flag": "Review",
        "state": "flagged",
    },
    {
        "date": "Sep 20",
        "vendor": "WeWork",
        "amount": "350.00",
        "tax": "31.82",
        "category": "Coworking",
        "conf": 91,
        "flag": None,
        "state": "normal",
    },
    {
        "date": "Sep 18",
        "vendor": "Uber",
        "amount": "38.60",
        "tax": None,
        "category": "Travel",
        "conf": 78,
        "flag": "Tax",
        "state": "flagged",
    },
    {
        "date": "Sep 17",
        "vendor": "Staples",
        "amount": "86.20",
        "tax": "7.84",
        "category": "Office supplies",
        "conf": 68,
        "flag": "Review",
        "state": "flagged",
    },
    {
        "date": "Sep 26",
        "vendor": "Amazon",
        "amount": "128.40",
        "tax": "11.67",
        "category": "Office supplies",
        "conf": 94,
        "flag": "Dupe",
        "state": "duplicate",
    },
    {
        "date": "Sep 28",
        "vendor": "Adobe",
        "amount": "59.99",
        "tax": "5.45",
        "category": "Software",
        "conf": 98,
        "flag": "Dupe",
        "state": "duplicate",
    },
]
PERCH_SUMMARY = {
    "total": 47,
    "flagged": 3,
    "dupes": 2,
    "unique": 45,
    "period": "Q3 2026 · USD",
    "shown": 9,
}

TREASURE_STATS = [
    {
        "label": "Total",
        "value": "$4,862.40",
        "note": "45 unique receipts",
        "small": False,
    },
    {
        "label": "Tax",
        "value": "$412.68",
        "note": "Tax recorded on receipts",
        "small": False,
    },
    {
        "label": "Deductible",
        "value": "$4,218.90",
        "note": "Based on category rules",
        "small": False,
    },
    {
        "label": "Top category",
        "value": "Software",
        "note": "$1,684.00 · 35% of total",
        "small": True,
    },
]
TREASURE_REPORTS = [
    {
        "icon": "table",
        "format": "CSV",
        "filename": "receipts_Q3-2026.csv",
        "desc": "All 47 receipts, with duplicate and review flags.",
        "meta": "47 rows · 18 KB",
    },
    {
        "icon": "file-text",
        "format": "PDF",
        "filename": "tax-report_Q3-2026.pdf",
        "desc": "Category totals and a deductible expense summary.",
        "meta": "6 pages · 124 KB",
    },
    {
        "icon": "file-warning",
        "format": "Anomaly TXT",
        "filename": "anomalies_Q3-2026.txt",
        "desc": "3 flagged receipts and 2 duplicates to check.",
        "meta": "5 findings · 2 KB",
    },
]
TREASURE_FOLDER = {
    "path": "~/Documents/ReceiptOwl/2026/Q3",
    "meta": "Originals + reports · 28.8 MB",
}

MODELS = ["gemma2:2b", "qwen2.5:3b", "llama3.2:3b"]
SETTINGS_CATEGORIES = [("Software", True), ("Office supplies", True), ("Meals", False)]
SETTINGS_HIDDEN = ["Coworking", "Travel", "Other"]
STORAGE_PATH = "~/Documents/ReceiptOwl"
