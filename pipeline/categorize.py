from __future__ import annotations

_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Software": (
        "adobe",
        "notion",
        "github",
        "slack",
        "figma",
        "microsoft",
        "google",
        "zoom",
        "dropbox",
        "openai",
        "anthropic",
        "atlassian",
        "jira",
        "aws",
        "digitalocean",
        "vercel",
        "netlify",
        "canva",
    ),
    "Office supplies": (
        "staples",
        "amazon",
        "office depot",
        "costco",
        "best buy",
        "target",
        "walmart",
        "ikea",
    ),
    "Meals": (
        "starbucks",
        "blue bottle",
        "restaurant",
        "cafe",
        "coffee",
        "doordash",
        "ubereats",
        "uber eats",
        "grubhub",
        "chipotle",
        "mcdonald",
    ),
    "Coworking": ("wework", "regus", "spaces", "industrious"),
    "Travel": (
        "uber",
        "lyft",
        "delta",
        "united",
        "airbnb",
        "hotel",
        "marriott",
        "airline",
        "airport",
        "hertz",
        "avis",
    ),
}


def categorize(
    vendor: str | None, text: str, categories: list[str]
) -> tuple[str, float]:
    """Returns (category, confidence 0-100). Falls back to "Other" (or the
    first available category if "Other" isn't configured)."""
    haystack_vendor = (vendor or "").lower()
    haystack_text = (text or "").lower()
    fallback = (
        "Other" if "Other" in categories else (categories[0] if categories else "Other")
    )

    for category, keywords in _KEYWORDS.items():
        if category not in categories:
            continue
        if any(k in haystack_vendor for k in keywords):
            return category, 90.0

    for category, keywords in _KEYWORDS.items():
        if category not in categories:
            continue
        if any(k in haystack_text for k in keywords):
            return category, 70.0

    return fallback, 50.0
