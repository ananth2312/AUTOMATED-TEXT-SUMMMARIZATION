"""
app/nlp/summarizer.py
──────────────────────
Extractive summarisation using a TextRank-inspired approach.

Algorithm overview (sentence-level TextRank):
1. Split text into sentences.
2. Embed each sentence using TF-IDF vectors.
3. Build a similarity graph (cosine similarity between sentence vectors).
4. Run PageRank on the graph to score sentences.
5. Select the top-N sentences (by score) and return them in document order.

This is a purely extractive algorithm:
- Selected sentences come verbatim from the source text.
- The output is NOT paraphrased or abstractive.

Summary length mapping:
  concise  → top 15% of sentences  (min 2, max ~5)
  medium   → top 30% of sentences  (min 3, max ~10)
  detailed → top 50% of sentences  (min 5, max ~20)

Also provides:
- summarize_with_evidence(): retains source offsets, section origins, and salience scores.
- generate_section_summaries(): creates section-specific intelligent summaries.
"""

import logging
import math
import re
from typing import Optional

from .section_detector import Section

logger = logging.getLogger(__name__)

# Sentence count thresholds for each level
_LENGTH_RATIOS = {
    "concise":  0.15,
    "medium":   0.30,
    "detailed": 0.50,
}
_MIN_SENTENCES = {"concise": 2, "medium": 3, "detailed": 5}
_MAX_SENTENCES = {"concise": 6, "medium": 12, "detailed": 25}

# Minimum word count per sentence to be considered for ranking
_MIN_WORDS_PER_SENTENCE = 5

# Damping factor for PageRank
_DAMPING = 0.85
_PAGERANK_ITERATIONS = 50
_PAGERANK_TOLERANCE = 1e-6


def summarize(
    sentences: list[str],
    summary_type: str = "medium",
) -> tuple[str, list[str], list[str], list[str]]:
    """
    Generate extractive summaries at all three length levels.

    :param sentences: Pre-tokenised sentence list from the preprocessor.
    :param summary_type: Ignored in return values – all three are always computed.
    :returns: Tuple of (requested_summary, concise_sents, medium_sents, detailed_sents).
    """
    # Filter out very short / noisy sentences
    filtered = [s for s in sentences if len(s.split()) >= _MIN_WORDS_PER_SENTENCE]

    if len(filtered) == 0:
        logger.warning("No usable sentences for summarisation.")
        return "", [], [], []

    if len(filtered) == 1:
        # Only one sentence – return it for all levels
        return filtered[0], filtered, filtered, filtered

    # Build TF-IDF matrix
    vocab, tfidf_matrix = _build_tfidf_matrix(filtered)

    # Cosine-similarity graph
    n = len(filtered)
    similarity_matrix = _build_similarity_matrix(tfidf_matrix, n)

    # PageRank scores
    scores = _pagerank(similarity_matrix, n)

    # Select sentences per level
    concise_sents  = _select_sentences(filtered, scores, "concise")
    medium_sents   = _select_sentences(filtered, scores, "medium")
    detailed_sents = _select_sentences(filtered, scores, "detailed")

    summary_map = {
        "concise":  " ".join(concise_sents),
        "medium":   " ".join(medium_sents),
        "detailed": " ".join(detailed_sents),
    }

    requested = summary_map.get(summary_type, summary_map["medium"])
    return requested, concise_sents, medium_sents, detailed_sents


def summarize_with_evidence(
    sentences: list[str],
    clean_text: str,
    sections: list[Section],
    summary_type: str = "medium",
    sentence_spans: Optional[list[tuple[int, int]]] = None,
) -> tuple[str, list[str], list[str], list[str], dict[str, list[dict]]]:
    """
    Generate extractive summaries and attach verified source evidence (sentence index,
    character spans, enclosing section, and TextRank score) to each sentence.

    :returns: (requested, concise_sents, medium_sents, detailed_sents, evidence_by_level)
    """
    if not sentence_spans or len(sentence_spans) != len(sentences):
        sentence_spans = _locate_spans(clean_text, sentences)

    # Keep track of original sentence index
    filtered_items = [
        (i, s) for i, s in enumerate(sentences)
        if len(s.split()) >= _MIN_WORDS_PER_SENTENCE
    ]

    empty_evidence = {"concise": [], "medium": [], "detailed": []}

    if len(filtered_items) == 0:
        logger.warning("No usable sentences for summarisation with evidence.")
        return "", [], [], [], empty_evidence

    if len(filtered_items) == 1:
        idx, s = filtered_items[0]
        span = sentence_spans[idx] if idx < len(sentence_spans) else (0, 0)
        sec = _find_section_for_offset(span[0], sections)
        item = {
            "index": idx,
            "text": s,
            "score": 1.0,
            "start_char": span[0],
            "end_char": span[1],
            "section": sec,
        }
        evidence = {"concise": [item], "medium": [item], "detailed": [item]}
        return s, [s], [s], [s], evidence

    filtered_sents = [s for _, s in filtered_items]
    vocab, tfidf_matrix = _build_tfidf_matrix(filtered_sents)
    n = len(filtered_sents)
    similarity_matrix = _build_similarity_matrix(tfidf_matrix, n)
    scores = _pagerank(similarity_matrix, n)

    def _build_level_evidence(level: str) -> tuple[list[str], list[dict]]:
        sel_indices = _select_sentence_indices(n, scores, level)
        sents = []
        ev_items = []
        for filtered_idx in sel_indices:
            orig_idx, s_text = filtered_items[filtered_idx]
            span = sentence_spans[orig_idx] if orig_idx < len(sentence_spans) else (0, 0)
            sec = _find_section_for_offset(span[0], sections)
            sents.append(s_text)
            ev_items.append({
                "index": orig_idx,
                "text": s_text,
                "score": round(float(scores[filtered_idx]), 4),
                "start_char": span[0],
                "end_char": span[1],
                "section": sec,
            })
        return sents, ev_items

    concise_sents, concise_ev = _build_level_evidence("concise")
    medium_sents, medium_ev = _build_level_evidence("medium")
    detailed_sents, detailed_ev = _build_level_evidence("detailed")

    summary_map = {
        "concise": " ".join(concise_sents),
        "medium": " ".join(medium_sents),
        "detailed": " ".join(detailed_sents),
    }
    evidence_map = {
        "concise": concise_ev,
        "medium": medium_ev,
        "detailed": detailed_ev,
    }

    requested = summary_map.get(summary_type, summary_map["medium"])
    return requested, concise_sents, medium_sents, detailed_sents, evidence_map


def generate_section_summaries(
    clean_text: str,
    sentences: list[str],
    sections: list[Section],
    sentence_spans: Optional[list[tuple[int, int]]] = None,
) -> list[dict]:
    """
    Generate section-specific extractive summaries for all detected sections.
    """
    if not sections or not sentences:
        return []

    if not sentence_spans or len(sentence_spans) != len(sentences):
        sentence_spans = _locate_spans(clean_text, sentences)

    results = []

    for sec in sections:
        # Collect sentences belonging to this section
        sec_sentences_meta = []
        for i, s in enumerate(sentences):
            span = sentence_spans[i] if i < len(sentence_spans) else (0, 0)
            if sec.start_char <= span[0] < sec.end_char:
                sec_sentences_meta.append((i, s, span))

        if not sec_sentences_meta:
            results.append({
                "name": sec.name,
                "summary_text": sec.content_preview or "",
                "word_count": sec.word_count,
                "start_char": sec.start_char,
                "end_char": sec.end_char,
                "sentences": [],
            })
            continue

        # If few sentences, use them directly
        filtered_sec = [
            (orig_idx, s, span) for (orig_idx, s, span) in sec_sentences_meta
            if len(s.split()) >= _MIN_WORDS_PER_SENTENCE
        ]

        if len(filtered_sec) <= 2:
            sel_meta = filtered_sec if filtered_sec else sec_sentences_meta[:2]
            summary_text = " ".join(item[1] for item in sel_meta)
            ev_list = [
                {
                    "index": item[0],
                    "text": item[1],
                    "score": 1.0,
                    "start_char": item[2][0],
                    "end_char": item[2][1],
                    "section": sec.name,
                }
                for item in sel_meta
            ]
            results.append({
                "name": sec.name,
                "summary_text": summary_text,
                "word_count": sec.word_count,
                "start_char": sec.start_char,
                "end_char": sec.end_char,
                "sentences": ev_list,
            })
            continue

        # Rank using TextRank on section sentences
        sec_sents_only = [item[1] for item in filtered_sec]
        vocab, tfidf = _build_tfidf_matrix(sec_sents_only)
        n = len(sec_sents_only)
        sim_mat = _build_similarity_matrix(tfidf, n)
        scores = _pagerank(sim_mat, n)

        # Pick top 2 or 3 sentences
        top_k = min(3, max(2, round(n * 0.35)))
        ranked = sorted(range(n), key=lambda idx: scores[idx], reverse=True)
        chosen_indices = sorted(ranked[:top_k])

        chosen_meta = [filtered_sec[idx] for idx in chosen_indices]
        summary_text = " ".join(item[1] for item in chosen_meta)
        ev_list = [
            {
                "index": item[0],
                "text": item[1],
                "score": round(float(scores[idx]), 4),
                "start_char": item[2][0],
                "end_char": item[2][1],
                "section": sec.name,
            }
            for idx, item in zip(chosen_indices, chosen_meta)
        ]

        results.append({
            "name": sec.name,
            "summary_text": summary_text,
            "word_count": sec.word_count,
            "start_char": sec.start_char,
            "end_char": sec.end_char,
            "sentences": ev_list,
        })

    return results


# ── Internal helpers ─────────────────────────────────────────────────────────

def _locate_spans(text: str, sentences: list[str]) -> list[tuple[int, int]]:
    """Compute character spans for each sentence in text."""
    spans: list[tuple[int, int]] = []
    curr = 0
    for s in sentences:
        pos = text.find(s, curr)
        if pos != -1:
            spans.append((pos, pos + len(s)))
            curr = pos + len(s)
        else:
            prefix = s[:min(30, len(s))]
            pos = text.find(prefix, curr)
            if pos != -1:
                spans.append((pos, pos + len(s)))
                curr = pos + len(s)
            else:
                spans.append((0, 0))
    return spans


def _find_section_for_offset(offset: int, sections: list[Section]) -> str:
    """Find section name enclosing the character offset."""
    for s in sections:
        if s.start_char <= offset < s.end_char:
            return s.name
    return "General / Body"


def _tokenize(sentence: str) -> list[str]:
    """Lowercase alphabetic tokens; remove stop words and single chars."""
    _STOP = {
        "the","a","an","and","or","but","in","on","at","to","for","of","with",
        "by","from","up","about","into","over","after","is","are","was","were",
        "be","been","being","have","has","had","do","does","did","will","would",
        "shall","should","may","might","must","can","could","it","its","this",
        "that","these","those","i","we","you","he","she","they","their","our",
        "which","what","when","where","who","how","all","both","each","more",
        "most","other","some","such","no","nor","not","only","own","same","so",
        "than","too","very","just","also","as","if","then","because","while",
    }
    tokens = re.findall(r"[a-z]+", sentence.lower())
    return [t for t in tokens if len(t) > 2 and t not in _STOP]


def _build_tfidf_matrix(sentences: list[str]) -> tuple[list[str], list[list[float]]]:
    tokenised = [_tokenize(s) for s in sentences]
    df: dict[str, int] = {}
    for tokens in tokenised:
        for term in set(tokens):
            df[term] = df.get(term, 0) + 1

    vocab = sorted(df.keys())
    term_idx = {term: i for i, term in enumerate(vocab)}
    n = len(sentences)

    matrix: list[list[float]] = []
    for tokens in tokenised:
        row = [0.0] * len(vocab)
        if not tokens:
            matrix.append(row)
            continue
        tf: dict[str, int] = {}
        for t in tokens:
            tf[t] = tf.get(t, 0) + 1
        max_tf = max(tf.values()) if tf else 1
        norm_sq = 0.0
        for term, count in tf.items():
            if term in term_idx:
                tf_val = 0.5 + 0.5 * (count / max_tf)
                idf_val = math.log((1 + n) / (1 + df[term])) + 1.0
                val = tf_val * idf_val
                row[term_idx[term]] = val
                norm_sq += val * val
        if norm_sq > 0:
            norm = math.sqrt(norm_sq)
            row = [v / norm for v in row]
        matrix.append(row)

    return vocab, matrix


def _build_similarity_matrix(tfidf_matrix: list[list[float]], n: int) -> list[list[float]]:
    sim = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            row_i = tfidf_matrix[i]
            row_j = tfidf_matrix[j]
            dot = sum(row_i[k] * row_j[k] for k in range(len(row_i)))
            sim[i][j] = dot
            sim[j][i] = dot
    return sim


def _pagerank(matrix: list[list[float]], n: int) -> list[float]:
    if n == 0:
        return []
    if n == 1:
        return [1.0]

    scores = [1.0 / n] * n
    col_sums = [sum(matrix[k][j] for k in range(n)) for j in range(n)]
    trans = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j and col_sums[j] > 0:
                trans[i][j] = matrix[i][j] / col_sums[j]

    for _ in range(_PAGERANK_ITERATIONS):
        new_scores = [0.0] * n
        for i in range(n):
            s = sum(trans[i][j] * scores[j] for j in range(n) if i != j)
            new_scores[i] = ((1 - _DAMPING) / n) + (_DAMPING * s)
        diff = sum(abs(new_scores[i] - scores[i]) for i in range(n))
        scores = new_scores
        if diff < _PAGERANK_TOLERANCE:
            break

    return scores


def _select_sentence_indices(
    n: int,
    scores: list[float],
    level: str,
) -> list[int]:
    ratio = _LENGTH_RATIOS[level]
    top_k = max(
        _MIN_SENTENCES[level],
        min(_MAX_SENTENCES[level], round(n * ratio)),
    )
    ranked = sorted(range(n), key=lambda i: scores[i], reverse=True)
    return sorted(ranked[:top_k])


def _select_sentences(
    sentences: list[str],
    scores: list[float],
    level: str,
) -> list[str]:
    selected_indices = _select_sentence_indices(len(sentences), scores, level)
    return [sentences[i] for i in selected_indices]
