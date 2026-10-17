"""Text extraction from a staged receipt file."""

from __future__ import annotations

import shutil
from pathlib import Path

MIN_TEXT_LAYER_CHARS = 20


def _pdf_text_layer(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        return ""
    try:
        reader = PdfReader(str(path))
        pages = [p.extract_text() or "" for p in reader.pages]
        return "\n".join(t.strip() for t in pages if t.strip())
    except Exception:
        return ""


def _tesseract_available() -> bool:
    try:
        import pytesseract  # noqa: F401
    except ImportError:
        return False
    return shutil.which("tesseract") is not None


def _ocr_image(path: Path) -> str:
    import pytesseract
    from PIL import Image

    with Image.open(path) as img:
        return pytesseract.image_to_string(img).strip()


def _ocr_scanned_pdf(path: Path) -> str:
    try:
        import fitz  # PyMuPDF — optional
    except ImportError:
        return ""
    import pytesseract
    from PIL import Image

    pages = []
    with fitz.open(path) as doc:
        for page in doc:
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            text = pytesseract.image_to_string(img).strip()
            if text:
                pages.append(text)
    return "\n\n".join(pages)


def extract_text(path: Path, kind: str) -> tuple[str, str]:
    """Returns (text, method). method documents how the text was obtained,
    which ``pipeline.extract`` uses to judge how much to trust it."""
    path = Path(path)

    if kind == "pdf":
        text = _pdf_text_layer(path)
        if len(text) >= MIN_TEXT_LAYER_CHARS:
            return text, "pdf_text"
        if _tesseract_available():
            ocr_text = _ocr_scanned_pdf(path)
            if ocr_text:
                return ocr_text, "pdf_ocr"
        return "", "pdf_text_unavailable"

    # image
    if _tesseract_available():
        try:
            text = _ocr_image(path)
            return text, "image_ocr"
        except Exception:
            return "", "image_ocr_failed"
    return "", "image_ocr_unavailable"
