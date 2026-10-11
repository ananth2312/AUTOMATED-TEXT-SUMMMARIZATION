"""
app/nlp/preprocessor.py
────────────────────────
Text preprocessing for academic research papers.

Responsibilities:
- Normalise whitespace and encoding artifacts
- Remove repeated page headers/footers (heuristic, best-effort)
- Split text into sentences and paragraphs
- Provide a clean version for summarisation while keeping the
  original extracted text available for source display

The original text is NEVER discarded – only the clean copy is
passed to the NLP algorithms.
"""

import logging
import re
import unicodedata
from typing import NamedTuple

logger = logging.getLogger(__name__)

# Page separator inserted by the extractor
_PAGE_SEP_PATTERN = re.compile(r"\s*---\s*PAGE BREAK\s*---\s*", re.IGNORECASE)


class PreprocessedText(NamedTuple):
    clean_text: str           # normalised, de-noised text for NLP
    sentences: list[str]      # sentence list for summarisation
    paragraphs: list[str]     # paragraph list
    warnings: list[str]


def preprocess(raw_text: str) -> PreprocessedText:
    """
    Clean and segment *raw_text* for downstream NLP tasks.

    :param raw_text: Text as returned by the extractor (may include PAGE BREAK markers).
    :returns: PreprocessedText with clean text, sentences, and paragraphs.
    """
    warnings: list[str] = []

    if not raw_text or not raw_text.strip():
        return PreprocessedText("", [], [], ["Input text is empty."])

    # 1. Unicode normalisation (NFKC fixes ligatures like ﬁ → fi)
    text = unicodedata.normalize("NFKC", raw_text)

    # 2. Remove page-break markers
    text = _PAGE_SEP_PATTERN.sub("\n\n", text)

    # 3. Normalise line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 4. Remove soft hyphens (used for line-break hyphenation in PDFs)
    text = text.replace("\u00ad", "")

    # 5. Fix hyphenated word breaks that occur at line boundaries
    #    e.g.  "infor-\nmation" → "information"
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)

    # 6. Replace single newlines inside paragraphs with spaces
    #    (a double newline marks a paragraph boundary)
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)

    # 7. Collapse runs of 3+ blank lines → exactly two
    text = re.sub(r"\n{3,}", "\n\n", text)

    # 8. Normalise internal whitespace within lines
    lines = [" ".join(line.split()) for line in text.splitlines()]
    text = "\n".join(lines)

    # 9. Heuristic: remove repeated running headers/footers
    text = _remove_repeated_lines(text)

    text = text.strip()

    if len(text) < 100:
        warnings.append(
            "Very little text remains after preprocessing. "
            "Summaries and key phrases may not be meaningful."
        )

    paragraphs = _split_paragraphs(text)
    sentences = _split_sentences(text)

    return PreprocessedText(
        clean_text=text,
        sentences=sentences,
        paragraphs=paragraphs,
        warnings=warnings,
    )


# ── Helpers ──────────────────────────────────────────────────────────────────

def _split_paragraphs(text: str) -> list[str]:
    """Split on blank lines; filter out empty and very short fragments."""
    return [p.strip() for p in text.split("\n\n") if len(p.strip()) > 20]


_CACHED_TOKENIZER = None
_NLTK_CHECKED = False


def _get_sentence_tokenizer():
    global _CACHED_TOKENIZER, _NLTK_CHECKED
    if _NLTK_CHECKED:
        return _CACHED_TOKENIZER

    _NLTK_CHECKED = True
    try:
        import nltk
        for resource in ("tokenizers/punkt_tab/english/", "tokenizers/punkt/english.pickle"):
            try:
                _CACHED_TOKENIZER = nltk.data.load(resource)
                return _CACHED_TOKENIZER
            except LookupError:
                pass

        # Try once to download silently
        try:
            import ssl
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            nltk.download("punkt_tab", quiet=True)
            _CACHED_TOKENIZER = nltk.data.load("tokenizers/punkt_tab/english/")
            return _CACHED_TOKENIZER
        except Exception:
            pass
    except Exception:
        pass

    return None


def _split_sentences(text: str) -> list[str]:
    """
    Sentence tokeniser using NLTK Punkt (falls back to regex if NLTK absent or unavailable).
    Punkt is more robust for academic text containing abbreviations (e.g., Fig., et al.).
    """
    tokenizer = _get_sentence_tokenizer()
    if tokenizer is not None:
        try:
            sentences = tokenizer.tokenize(text)
        except Exception:
            sentences = _regex_sentence_split(text)
    else:
        sentences = _regex_sentence_split(text)

    # Filter trivially short fragments
    return [s.strip() for s in sentences if len(s.split()) >= 3]


def _regex_sentence_split(text: str) -> list[str]:
    """Fallback regex-based sentence splitter."""
    pattern = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")
    return pattern.split(text)


def _remove_repeated_lines(text: str) -> str:
    """
    Best-effort removal of running headers/footers.

    A non-empty line that appears 3 or more times in the document is
    treated as a repeated header/footer and removed.
    This is heuristic and may occasionally remove legitimate repeated lines
    (e.g., table headers); a warning is not emitted to avoid noise.
    """
    lines = text.splitlines()
    from collections import Counter

    # Count non-empty, short lines (headers/footers are usually short)
    line_counts = Counter(
        ln.strip() for ln in lines
        if 0 < len(ln.strip()) < 120
    )
    # Only remove lines that appear very frequently (3+ times)
    repeated = {ln for ln, count in line_counts.items() if count >= 3}

    if not repeated:
        return text

    filtered = [ln for ln in lines if ln.strip() not in repeated]
    return "\n".join(filtered)
