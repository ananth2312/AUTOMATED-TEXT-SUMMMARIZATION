"""
app/nlp/statistics.py
──────────────────────
Document statistics calculator.

Computes:
- Word count (split on whitespace)
- Character count (including spaces)
- Sentence count
- Paragraph count
- Estimated reading time (default: 200 WPM for academic text)
- Summary word count and ratio

All metrics are deterministic, fast, and require no NLP models.
"""

import math
import re


def compute_statistics(
    text: str,
    summary_text: str,
    sentences: list[str],
    paragraphs: list[str],
    words_per_minute: int = 200,
) -> dict:
    """
    Compute document statistics.

    :param text: Clean preprocessed text.
    :param summary_text: The generated summary (any length level).
    :param sentences: Pre-tokenised sentence list.
    :param paragraphs: Pre-tokenised paragraph list.
    :param words_per_minute: Reading-speed assumption (documented in result).
    :returns: Statistics dict matching DocumentStatistics schema.
    """
    source_words = _word_count(text)
    source_chars = len(text)
    sentence_count = len(sentences)
    paragraph_count = len(paragraphs)
    reading_time = round(source_words / words_per_minute, 2) if source_words else 0.0

    summary_words = _word_count(summary_text)
    ratio = round(summary_words / source_words, 4) if source_words else 0.0

    return {
        "word_count": source_words,
        "character_count": source_chars,
        "sentence_count": sentence_count,
        "paragraph_count": paragraph_count,
        "estimated_reading_time_minutes": reading_time,
        "summary_word_count": summary_words,
        "summary_to_source_ratio": ratio,
        "words_per_minute_assumption": words_per_minute,
    }


def _word_count(text: str) -> int:
    """Count whitespace-delimited tokens (simple, fast, language-agnostic)."""
    return len(text.split()) if text else 0
