"""
app/nlp/keyword_extractor.py
─────────────────────────────
Key-phrase extraction using YAKE (Yet Another Keyword Extractor).

YAKE is:
- Unsupervised (no model downloads or training required)
- Lightweight and fast
- Suitable for academic text with domain-specific terminology
- Lower score = more relevant in YAKE's native output

We invert and normalise YAKE scores to a 0-1 relevance range
(1 = most relevant) for consistent display in the frontend.

NOTE: Scores are algorithmic relevance estimates – they indicate the
algorithm's ranking, not scientifically verified importance.
Near-duplicate phrases are filtered using token-overlap deduplication.
"""

import logging
import re
from typing import NamedTuple

logger = logging.getLogger(__name__)

# Default extraction configuration
_DEFAULT_MAX_PHRASES = 20
_DEFAULT_NGRAM_MAX = 3        # consider 1-, 2-, 3-word phrases
_DEFAULT_DEDUP_THRESHOLD = 0.9  # fraction of shared tokens to consider near-duplicate


class ExtractedPhrase(NamedTuple):
    phrase: str
    score: float   # 0-1, higher = more relevant (normalised from YAKE)
    rank: int


def extract_key_phrases(
    text: str,
    max_phrases: int = _DEFAULT_MAX_PHRASES,
    ngram_max: int = _DEFAULT_NGRAM_MAX,
    dedup_threshold: float = _DEFAULT_DEDUP_THRESHOLD,
) -> list[ExtractedPhrase]:
    """
    Extract and rank key phrases from *text* using YAKE.

    :param text: Clean preprocessed document text.
    :param max_phrases: Maximum number of phrases to return.
    :param ngram_max: Maximum words per phrase.
    :param dedup_threshold: Near-duplicate filter: phrases sharing this
                            fraction of tokens are collapsed to the top-ranked one.
    :returns: List of ExtractedPhrase, ordered by relevance (best first).
    """
    if not text or not text.strip():
        logger.warning("Empty text passed to keyword extractor.")
        return []

    raw_phrases = _run_yake(text, max_phrases * 3, ngram_max)

    if not raw_phrases:
        logger.info("YAKE returned no phrases; falling back to TF-IDF.")
        raw_phrases = _tfidf_fallback(text, max_phrases * 2)

    # Normalise scores to [0, 1] – YAKE: lower raw score = more relevant
    normalised = _normalise_scores(raw_phrases)

    # Deduplicate near-duplicate phrases
    deduplicated = _deduplicate(normalised, dedup_threshold)

    # Cap and assign final ranks
    final = deduplicated[:max_phrases]
    return [
        ExtractedPhrase(phrase=p, score=round(s, 4), rank=i + 1)
        for i, (p, s) in enumerate(final)
    ]


# ── YAKE runner ───────────────────────────────────────────────────────────────

def _run_yake(text: str, n: int, ngram_max: int) -> list[tuple[str, float]]:
    """Run YAKE and return (phrase, raw_score) pairs."""
    try:
        import yake
        extractor = yake.KeywordExtractor(
            lan="en",
            n=ngram_max,
            dedupLim=0.9,
            top=n,
            features=None,
        )
        results = extractor.extract_keywords(text)
        # YAKE returns [(phrase, score), …] with lower score = better
        return [(phrase.strip(), score) for phrase, score in results if phrase.strip()]
    except ImportError:
        logger.warning("YAKE not installed. Using TF-IDF fallback.")
        return []
    except Exception as exc:
        logger.error("YAKE extraction failed: %s", exc)
        return []


# ── TF-IDF fallback ───────────────────────────────────────────────────────────

def _tfidf_fallback(text: str, n: int) -> list[tuple[str, float]]:
    """
    Simple TF-IDF unigram/bigram fallback when YAKE is unavailable.
    Returns (phrase, score) where higher score = more relevant.
    We negate scores before passing to _normalise_scores which expects
    YAKE convention (lower = better), so we return (phrase, -tfidf_score).
    """
    import math
    import re

    _STOP = {
        "the","a","an","and","or","but","in","on","at","to","for","of","with",
        "by","from","is","are","was","were","be","been","has","have","had",
        "do","does","did","not","that","this","these","those","it","its","as",
        "if","than","then","also","so","such","no","nor","yet","both","either",
        "whether","while","when","where","which","who","whom","what","there",
        "here","can","could","will","would","shall","should","may","might",
        "must","each","any","all","some","more","most","other","into",
        "through","during","before","after","above","below","between",
    }

    words = re.findall(r"[a-zA-Z]{3,}", text.lower())
    words = [w for w in words if w not in _STOP]

    # Unigrams
    tf: dict[str, int] = {}
    for w in words:
        tf[w] = tf.get(w, 0) + 1

    total = len(words) or 1
    scored = [(w, count / total) for w, count in tf.items()]
    scored.sort(key=lambda x: x[1], reverse=True)

    # Return as YAKE-convention: lower = better → negate TF scores
    return [(phrase, -score) for phrase, score in scored[:n]]


# ── Score normalisation ───────────────────────────────────────────────────────

def _normalise_scores(
    raw: list[tuple[str, float]],
) -> list[tuple[str, float]]:
    """
    Convert YAKE raw scores (lower = better) to normalised [0,1] where 1 = best.
    """
    if not raw:
        return []

    scores = [s for _, s in raw]
    min_s = min(scores)
    max_s = max(scores)
    span = max_s - min_s or 1.0

    normalised = [
        (phrase, 1.0 - (score - min_s) / span)
        for phrase, score in raw
    ]
    # Sort best-first
    normalised.sort(key=lambda x: x[1], reverse=True)
    return normalised


# ── Deduplication ─────────────────────────────────────────────────────────────

def _token_set(phrase: str) -> set[str]:
    return set(re.findall(r"[a-z]+", phrase.lower()))


def _deduplicate(
    phrases: list[tuple[str, float]],
    threshold: float,
) -> list[tuple[str, float]]:
    """
    Remove near-duplicate phrases.
    Two phrases are near-duplicates if their token overlap (Jaccard) ≥ threshold.
    The lower-ranked (later) phrase is removed.
    """
    kept: list[tuple[str, float]] = []
    kept_token_sets: list[set] = []

    for phrase, score in phrases:
        ts = _token_set(phrase)
        is_dup = False
        for existing_ts in kept_token_sets:
            union = existing_ts | ts
            intersection = existing_ts & ts
            jaccard = len(intersection) / len(union) if union else 0.0
            if jaccard >= threshold:
                is_dup = True
                break
        if not is_dup:
            kept.append((phrase, score))
            kept_token_sets.append(ts)

    return kept
