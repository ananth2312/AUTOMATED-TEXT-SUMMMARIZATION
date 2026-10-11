"""
app/nlp/extractor.py
─────────────────────
PDF text extraction using PyMuPDF (fitz).

Returns:
  - Extracted text (str)
  - Page count (int)
  - Extraction quality flag: "success" | "low_quality" | "failed"
  - Warning messages for the caller to surface to the user

Design notes:
- Preserves paragraph and page structure markers for downstream preprocessing.
- Does NOT claim OCR capability; image-only PDFs produce a low_quality result.
- Handles encrypted, corrupt, and empty PDFs safely.
"""

import logging
import re
from pathlib import Path
from typing import NamedTuple

logger = logging.getLogger(__name__)

# Minimum characters extracted before we consider the PDF usable
_MIN_CHARS_THRESHOLD = 200
# Marker inserted between pages so preprocessing can detect page boundaries
_PAGE_SEPARATOR = "\n\n--- PAGE BREAK ---\n\n"


class ExtractionResult(NamedTuple):
    text: str
    page_count: int
    status: str           # "success" | "low_quality" | "failed"
    warnings: list[str]
    metadata: dict        # title, author, subject from PDF metadata


def extract_text_from_pdf(file_path: Path) -> ExtractionResult:
    """
    Extract all text from *file_path* using PyMuPDF.

    :param file_path: Absolute path to the PDF file.
    :returns: ExtractionResult named tuple.
    """
    warnings: list[str] = []

    try:
        import fitz  # PyMuPDF
    except ImportError:
        logger.error("PyMuPDF (fitz) is not installed.")
        return ExtractionResult("", 0, "failed", ["PyMuPDF not installed."], {})

    try:
        doc = fitz.open(str(file_path))
    except fitz.FileDataError as exc:
        logger.warning("Corrupt PDF: %s – %s", file_path.name, exc)
        return ExtractionResult("", 0, "failed", [f"PDF file is corrupt or unreadable: {exc}"], {})
    except Exception as exc:
        logger.warning("Cannot open PDF: %s – %s", file_path.name, exc)
        return ExtractionResult("", 0, "failed", [f"Cannot open file: {exc}"], {})

    # Handle encrypted PDFs
    if doc.needs_pass:
        doc.close()
        return ExtractionResult(
            "", 0, "failed",
            ["This PDF is password-protected. Please provide an unencrypted version."],
            {},
        )

    page_count = len(doc)
    pdf_metadata: dict = {}
    try:
        raw_meta = doc.metadata or {}
        pdf_metadata = {
            "title": (raw_meta.get("title") or "").strip(),
            "author": (raw_meta.get("author") or "").strip(),
            "subject": (raw_meta.get("subject") or "").strip(),
        }
    except Exception:
        pass

    page_texts: list[str] = []
    for page_num in range(page_count):
        try:
            page = doc[page_num]
            text = page.get_text("text")   # plain text, preserves layout
            page_texts.append(text or "")
        except Exception as exc:
            logger.warning("Page %d extraction error: %s", page_num + 1, exc)
            warnings.append(f"Page {page_num + 1} could not be fully extracted.")
            page_texts.append("")

    doc.close()

    combined = _PAGE_SEPARATOR.join(page_texts)
    combined = _clean_raw_extraction(combined)

    char_count = len(combined.strip())

    if char_count < _MIN_CHARS_THRESHOLD:
        status = "low_quality"
        warnings.append(
            "Very little text was extracted from this PDF. "
            "The document may be scanned or image-based. "
            "OCR is not currently supported; results will be limited."
        )
    else:
        status = "success"

    return ExtractionResult(
        text=combined,
        page_count=page_count,
        status=status,
        warnings=warnings,
        metadata=pdf_metadata,
    )


# ── Internal helpers ─────────────────────────────────────────────────────────

def _clean_raw_extraction(text: str) -> str:
    """
    Lightweight cleanup of common PDF extraction artifacts.
    Does NOT remove scientific terms, citations, or formulae.
    """
    # Normalise Windows-style line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove form-feed characters (page-break markers from some PDF renderers)
    text = text.replace("\x0c", "\n")

    # Collapse runs of 3+ blank lines into exactly two (paragraph break)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove null bytes
    text = text.replace("\x00", "")

    return text
