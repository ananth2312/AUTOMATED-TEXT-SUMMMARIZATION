"""
app/nlp/section_detector.py
────────────────────────────
Heuristic academic-section detector.

Uses a list of known heading patterns and document-structure rules to
identify common academic paper sections. Detection is best-effort:
- If the heading evidence is insufficient, the section is not invented.
- Results include the section name, character span, and a short preview.

Supported sections (case-insensitive, with common variants):
  Abstract, Introduction, Related Work, Literature Review,
  Methodology / Methods / Materials and Methods,
  Results, Discussion, Conclusion / Conclusions,
  References / Bibliography, Acknowledgements
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


# ── Pattern registry ─────────────────────────────────────────────────────────

# Each entry: (canonical_name, list_of_regex_patterns)
# Patterns match the heading line; ^ is anchored to start-of-line.
_SECTION_PATTERNS: list[tuple[str, list[str]]] = [
    ("Abstract", [
        r"^\s*abstract\s*$",
        r"^\s*\d+\.?\s+abstract\s*$",
    ]),
    ("Introduction", [
        r"^\s*(?:\d+\.?\s+)?introduction\s*$",
        r"^\s*i\.\s+introduction\s*$",
    ]),
    ("Related Work", [
        r"^\s*(?:\d+\.?\s+)?related\s+work(?:s)?\s*$",
        r"^\s*(?:\d+\.?\s+)?related\s+literature\s*$",
    ]),
    ("Literature Review", [
        r"^\s*(?:\d+\.?\s+)?literature\s+review\s*$",
        r"^\s*(?:\d+\.?\s+)?review\s+of\s+literature\s*$",
        r"^\s*(?:\d+\.?\s+)?background\s*$",
    ]),
    ("Methodology", [
        r"^\s*(?:\d+\.?\s+)?method(?:s|ology)?\s*$",
        r"^\s*(?:\d+\.?\s+)?materials?\s+and\s+methods?\s*$",
        r"^\s*(?:\d+\.?\s+)?experimental\s+setup\s*$",
        r"^\s*(?:\d+\.?\s+)?proposed\s+(?:method|approach|system)\s*$",
    ]),
    ("Results", [
        r"^\s*(?:\d+\.?\s+)?results?\s*$",
        r"^\s*(?:\d+\.?\s+)?experimental\s+results?\s*$",
        r"^\s*(?:\d+\.?\s+)?findings\s*$",
    ]),
    ("Discussion", [
        r"^\s*(?:\d+\.?\s+)?discussion\s*$",
        r"^\s*(?:\d+\.?\s+)?results?\s+and\s+discussion\s*$",
        r"^\s*(?:\d+\.?\s+)?analysis\s*$",
    ]),
    ("Conclusion", [
        r"^\s*(?:\d+\.?\s+)?conclusions?\s*$",
        r"^\s*(?:\d+\.?\s+)?concluding\s+remarks?\s*$",
        r"^\s*(?:\d+\.?\s+)?summary\s+and\s+conclusions?\s*$",
    ]),
    ("Future Work", [
        r"^\s*(?:\d+\.?\s+)?future\s+work\s*$",
        r"^\s*(?:\d+\.?\s+)?future\s+directions?\s*$",
    ]),
    ("Acknowledgements", [
        r"^\s*acknowledge?ments?\s*$",
        r"^\s*(?:\d+\.?\s+)?acknowledge?ments?\s*$",
    ]),
    ("References", [
        r"^\s*references?\s*$",
        r"^\s*bibliography\s*$",
        r"^\s*(?:\d+\.?\s+)?references?\s*$",
    ]),
]

# Pre-compile for speed
_COMPILED: list[tuple[str, list[re.Pattern]]] = [
    (name, [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in pats])
    for name, pats in _SECTION_PATTERNS
]


# ── Result dataclass ──────────────────────────────────────────────────────────

@dataclass
class Section:
    name: str
    start_char: int
    end_char: int
    word_count: int = 0
    content_preview: str = ""   # first 200 chars of section body


# ── Main detector ─────────────────────────────────────────────────────────────

def detect_sections(text: str) -> list[Section]:
    """
    Identify academic sections in *text*.

    :param text: Clean (preprocessed) document text.
    :returns: Ordered list of Section objects found in the document.
    """
    if not text or not text.strip():
        return []

    # Build a line-indexed view for heading detection
    lines = text.splitlines()
    line_start_offsets = _compute_line_offsets(text)

    hits: list[tuple[int, str]] = []   # (char_offset, section_name)

    for name, patterns in _COMPILED:
        for pat in patterns:
            for match in pat.finditer(text):
                heading_start = match.start()
                # Confirm the match is a short standalone line (not mid-paragraph)
                line_idx = _char_to_line(heading_start, line_start_offsets)
                line_text = lines[line_idx] if line_idx < len(lines) else ""
                word_count_on_line = len(line_text.split())
                if word_count_on_line <= 8:   # headings are short
                    hits.append((heading_start, name))
                break   # first matching pattern for this section is enough

    # Fallback for inline run-in headings (e.g. "Abstract. ...", "Introduction. ...")
    if not hits:
        inline_patterns = [
            ("Abstract", r"(?:^|[\r\n]|(?<=\.\s))\s*(?:\d+\.?\s+)?abstract\s*[\.:]\s+"),
            ("Introduction", r"(?:^|[\r\n]|(?<=\.\s))\s*(?:\d+\.?\s+)?introduction\s*[\.:]\s+"),
            ("Related Work", r"(?:^|[\r\n]|(?<=\.\s))\s*(?:\d+\.?\s+)?related\s+work(?:s)?\s*[\.:]\s+"),
            ("Methodology", r"(?:^|[\r\n]|(?<=\.\s))\s*(?:\d+\.?\s+)?(?:methodology|methods?)\s*[\.:]\s+"),
            ("Results", r"(?:^|[\r\n]|(?<=\.\s))\s*(?:\d+\.?\s+)?results?\s*[\.:]\s+"),
            ("Discussion", r"(?:^|[\r\n]|(?<=\.\s))\s*(?:\d+\.?\s+)?discussion\s*[\.:]\s+"),
            ("Conclusion", r"(?:^|[\r\n]|(?<=\.\s))\s*(?:\d+\.?\s+)?conclusions?\s*[\.:]\s+"),
            ("Future Work", r"(?:^|[\r\n]|(?<=\.\s))\s*(?:\d+\.?\s+)?future\s+work\s*[\.:]\s+"),
            ("References", r"(?:^|[\r\n]|(?<=\.\s))\s*(?:\d+\.?\s+)?references?\s*[\.:]\s+"),
        ]
        for name, pat_str in inline_patterns:
            pat = re.compile(pat_str, re.IGNORECASE)
            m = pat.search(text)
            if m:
                hits.append((m.start(), name))

    # Deduplicate: if the same section name appears multiple times, keep the first
    seen: set[str] = set()
    unique_hits: list[tuple[int, str]] = []
    for offset, name in sorted(hits, key=lambda x: x[0]):
        if name not in seen:
            seen.add(name)
            unique_hits.append((offset, name))

    # Build Section objects with span and word count
    sections: list[Section] = []
    for i, (start, name) in enumerate(unique_hits):
        end = unique_hits[i + 1][0] if i + 1 < len(unique_hits) else len(text)
        body = text[start:end]

        # Skip the heading line itself for word count / preview
        body_lines = body.splitlines()
        body_body = "\n".join(body_lines[1:]).strip()

        word_count = len(body_body.split())
        preview = body_body[:200].replace("\n", " ").strip()

        sections.append(Section(
            name=name,
            start_char=start,
            end_char=end,
            word_count=word_count,
            content_preview=preview,
        ))

    return sections


# ── Utilities ─────────────────────────────────────────────────────────────────

def _compute_line_offsets(text: str) -> list[int]:
    """Return the character offset of the start of each line."""
    offsets = [0]
    for i, ch in enumerate(text):
        if ch == "\n":
            offsets.append(i + 1)
    return offsets


def _char_to_line(char_offset: int, offsets: list[int]) -> int:
    """Binary search to find the line index for a given character offset."""
    lo, hi = 0, len(offsets) - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if offsets[mid] <= char_offset:
            lo = mid
        else:
            hi = mid - 1
    return lo
