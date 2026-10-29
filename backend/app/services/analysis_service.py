"""
app/services/analysis_service.py
──────────────────────────────────
Core analysis orchestration service.

Coordinates the full NLP pipeline:
  preprocess → section detect → summarise (with evidence) →
  section-wise summaries → methodology & findings extractor →
  key phrases → statistics

Works for both PDF-extracted text and directly-pasted text.
Saves the result to MongoDB and returns the persisted document.
"""

import logging
import re
from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from pymongo.database import Database

from app.config import get_settings
from app.nlp import (
    compute_statistics,
    detect_in_text_citations,
    detect_sections,
    extract_key_phrases,
    extract_methodology_and_findings,
    extract_references_from_text,
    format_paper_self_citation,
    generate_section_summaries,
    preprocess,
    summarize_with_evidence,
)

logger = logging.getLogger(__name__)

# Algorithm version strings stored with each analysis for reproducibility
_ALGORITHM_VERSIONS = {
    "preprocessor": "1.0",
    "summarizer": "textrank-tfidf-evidence-1.1",
    "keyword_extractor": "yake-1.0",
    "section_detector": "regex-heuristic-1.0",
    "methodology_extractor": "heuristic-pattern-1.0",
    "citation_parser": "academic-citation-intel-1.0",
}


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


def _compute_page_offsets(raw_text: str) -> list[int]:
    """Returns list of starting character offsets for each page in raw_text."""
    breaks = [0]
    for m in re.finditer(r"\s*---\s*PAGE BREAK\s*---\s*", raw_text, re.IGNORECASE):
        breaks.append(m.end())
    return breaks


def _find_page(raw_text: str, page_breaks: list[int], sent_text: str, fallback_char: int = 0) -> int:
    """Estimates the 1-indexed page number of an evidence sentence in raw_text."""
    if not page_breaks or len(page_breaks) <= 1:
        return 1
    prefix = sent_text[:35].strip()
    pos = raw_text.find(prefix) if prefix else -1
    target = pos if pos != -1 else fallback_char
    for i in range(len(page_breaks) - 1, -1, -1):
        if target >= page_breaks[i]:
            return i + 1
    return 1



def run_analysis(
    *,
    db: Database,
    user_id: str,
    title: str,
    raw_text: str,
    summary_type: str = "medium",
    document_id: Optional[str] = None,
    existing_warnings: Optional[list[str]] = None,
) -> dict:
    """
    Run the full NLP pipeline on *raw_text* and persist the result.

    :param db:               MongoDB database instance.
    :param user_id:          Authenticated user's ID string.
    :param title:            Document title shown in UI.
    :param raw_text:         Extracted or pasted source text.
    :param summary_type:     "concise" | "medium" | "detailed".
    :param document_id:      Linked document _id (None for text-only analyses).
    :param existing_warnings: Warnings from extraction stage to carry forward.
    :returns: The inserted analysis document dict (with _id as str).
    """
    settings = get_settings()
    warnings: list[str] = list(existing_warnings or [])

    # ── 1. Preprocess ──────────────────────────────────────────────────────
    logger.info("Preprocessing text for analysis (doc_id=%s)", document_id)
    preprocessed = preprocess(raw_text)
    warnings.extend(preprocessed.warnings)

    if not preprocessed.clean_text:
        raise ValueError("Text is empty after preprocessing. Cannot generate analysis.")

    # ── 2. Section detection ───────────────────────────────────────────────
    sections = detect_sections(preprocessed.clean_text)
    logger.info("Detected %d sections", len(sections))

    # Sentence spans for accurate evidence linking
    sentence_spans = _locate_spans(preprocessed.clean_text, preprocessed.sentences)

    # ── 3. Summarisation with evidence ─────────────────────────────────────
    (
        requested_summary,
        concise_sents,
        medium_sents,
        detailed_sents,
        evidence_map,
    ) = summarize_with_evidence(
        sentences=preprocessed.sentences,
        clean_text=preprocessed.clean_text,
        sections=sections,
        summary_type=summary_type,
        sentence_spans=sentence_spans,
    )

    concise_summary  = " ".join(concise_sents)
    medium_summary   = " ".join(medium_sents)
    detailed_summary = " ".join(detailed_sents)

    if not requested_summary:
        warnings.append(
            "Summarisation produced no output. The text may be too short or repetitive."
        )

    # ── 4. Section-wise intelligent summaries ──────────────────────────────
    section_summaries = generate_section_summaries(
        clean_text=preprocessed.clean_text,
        sentences=preprocessed.sentences,
        sections=sections,
        sentence_spans=sentence_spans,
    )

    # ── 5. Methodology & Findings extraction ───────────────────────────────
    methodology_res = extract_methodology_and_findings(
        clean_text=preprocessed.clean_text,
        sentences=preprocessed.sentences,
        sections=sections,
        sentence_spans=sentence_spans,
    )

    # ── 6. Page mapping for split-screen evidence sync ─────────────────────
    page_breaks = _compute_page_offsets(raw_text)
    for level, ev_list in evidence_map.items():
        for ev in ev_list:
            if isinstance(ev, dict):
                ev["page_number"] = _find_page(raw_text, page_breaks, ev.get("text", ""), ev.get("start_char", 0))

    for sec_sum in section_summaries:
        sec_sum["page_number"] = _find_page(raw_text, page_breaks, sec_sum.get("summary_text", "")[:40], sec_sum.get("start_char", 0))
        for ev in sec_sum.get("sentences", []):
            if isinstance(ev, dict):
                ev["page_number"] = _find_page(raw_text, page_breaks, ev.get("text", ""), ev.get("start_char", 0))

    meth_dict = methodology_res.to_dict()
    for dim in meth_dict.get("dimensions", []):
        ev_text = dim.get("evidence") or dim.get("summary") or ""
        dim["page_number"] = _find_page(raw_text, page_breaks, ev_text[:35], dim.get("char_start") or 0)

    # ── 7. Key-phrase extraction ───────────────────────────────────────────
    phrases = extract_key_phrases(
        preprocessed.clean_text,
        max_phrases=settings.MAX_KEY_PHRASES,
    )

    # ── 8. Citation Intelligence & BibTeX ─────────────────────────────────
    doc_meta = None
    if document_id:
        try:
            doc_rec = db.documents.find_one({"_id": ObjectId(document_id)})
            if doc_rec:
                doc_meta = doc_rec.get("pdf_metadata")
        except Exception:
            pass

    parsed_refs = extract_references_from_text(preprocessed.clean_text, sections)
    in_text_cites = detect_in_text_citations(preprocessed.clean_text, parsed_refs)
    self_citation = format_paper_self_citation(title, doc_meta)

    citations_payload = {
        "total_references": len(parsed_refs),
        "references": [r.to_dict() for r in parsed_refs],
        "in_text_citations": in_text_cites,
        "paper_citation": self_citation,
    }

    # ── 9. Statistics ──────────────────────────────────────────────────────
    stats = compute_statistics(
        text=preprocessed.clean_text,
        summary_text=requested_summary,
        sentences=preprocessed.sentences,
        paragraphs=preprocessed.paragraphs,
        words_per_minute=settings.WORDS_PER_MINUTE,
    )

    # ── 10. Persist to MongoDB ────────────────────────────────────────────
    now = datetime.now(timezone.utc)
    analysis_doc = {
        "user_id": ObjectId(user_id),
        "document_id": ObjectId(document_id) if document_id else None,
        "title": title,
        "summary_type": summary_type,
        "summary_text": requested_summary,
        "concise_summary": concise_summary,
        "medium_summary": medium_summary,
        "detailed_summary": detailed_summary,
        "summary_sentences_with_evidence": evidence_map.get(summary_type, evidence_map.get("medium", [])),
        "evidence_by_level": evidence_map,
        "section_summaries": section_summaries,
        "methodology_findings": meth_dict,
        "citations": citations_payload,
        "key_phrases": [
            {"phrase": p.phrase, "score": p.score, "rank": p.rank}
            for p in phrases
        ],
        "detected_sections": [
            {
                "name": s.name,
                "start_char": s.start_char,
                "end_char": s.end_char,
                "word_count": s.word_count,
                "content_preview": s.content_preview,
            }
            for s in sections
        ],
        "statistics": stats,
        "processing_status": "success",
        "warnings": warnings,
        "algorithm_versions": _ALGORITHM_VERSIONS,
        "source_text_preview": preprocessed.clean_text[:500],
        "created_at": now,
    }

    result = db.analyses.insert_one(analysis_doc)
    analysis_doc["_id"] = str(result.inserted_id)
    analysis_doc["user_id"] = user_id
    if document_id:
        analysis_doc["document_id"] = document_id

    logger.info(
        "Analysis %s saved for user %s (summary_type=%s, phrases=%d, sections=%d, findings=%d, citations=%d)",
        analysis_doc["_id"],
        user_id,
        summary_type,
        len(phrases),
        len(section_summaries),
        methodology_res.total_found,
        len(parsed_refs),
    )
    return analysis_doc

