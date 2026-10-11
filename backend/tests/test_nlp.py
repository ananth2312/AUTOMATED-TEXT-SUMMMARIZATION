"""
tests/test_nlp.py
──────────────────
Unit tests for the NLP pipeline (no HTTP, no database needed):
  - Preprocessor
  - Section detector
  - Summarizer
  - Keyword extractor
  - Statistics calculator
"""

import pytest

from app.nlp.preprocessor import preprocess
from app.nlp.section_detector import detect_sections
from app.nlp.summarizer import (
    generate_section_summaries,
    summarize,
    summarize_with_evidence,
)
from app.nlp.methodology_extractor import extract_methodology_and_findings
from app.nlp.keyword_extractor import extract_key_phrases
from app.nlp.statistics import compute_statistics


# ── Sample academic text ──────────────────────────────────────────────────────

SAMPLE_TEXT = """
Abstract

This paper presents a novel approach to automated text summarisation
using graph-based algorithms. We demonstrate that TextRank, combined
with TF-IDF sentence embeddings, produces competitive extractive summaries.

Introduction

Academic reading places significant cognitive demands on researchers.
The volume of published literature has grown exponentially, making it
impractical to read every relevant paper in full. Automated summarisation
tools offer a practical solution by condensing long documents into shorter,
informative representations. This work addresses the challenge of
summarising academic research papers across diverse domains.

Methodology

We implemented an extractive summarisation pipeline using sentence-level
TextRank. Each sentence is represented as a TF-IDF vector. Cosine similarity
between sentence pairs forms the edges of a graph. PageRank scores determine
sentence importance. The top-ranked sentences, in document order, form the summary.

Results

Experiments on 50 academic papers showed an average ROUGE-1 score of 0.42.
The system processed each document in under two seconds on a standard laptop.
Extraction quality was higher for papers with clear section boundaries.

Conclusion

We presented a lightweight, efficient extractive summariser suitable for
academic research papers. Future work will explore abstractive methods
using transformer-based language models.
"""


class TestPreprocessor:
    def test_basic_preprocessing(self):
        result = preprocess(SAMPLE_TEXT)
        assert result.clean_text
        assert len(result.sentences) > 0
        assert len(result.paragraphs) > 0

    def test_empty_text(self):
        result = preprocess("")
        assert result.clean_text == ""
        assert "empty" in result.warnings[0].lower()

    def test_soft_hyphen_removal(self):
        text = "infor\u00admation systems are im\u00adportant for research."
        result = preprocess(text)
        assert "\u00ad" not in result.clean_text

    def test_hyphenated_line_break_fix(self):
        # Simulates a PDF line-break hyphen
        text = "The algorithm demon-\nstrated excellent per-\nformance on all benchmarks."
        result = preprocess(text)
        assert "demonstrated" in result.clean_text
        assert "performance" in result.clean_text

    def test_sentences_minimum_word_count(self):
        result = preprocess(SAMPLE_TEXT)
        for sent in result.sentences:
            assert len(sent.split()) >= 3


class TestSectionDetector:
    def test_detects_abstract(self):
        sections = detect_sections(SAMPLE_TEXT)
        names = [s.name for s in sections]
        assert "Abstract" in names

    def test_detects_introduction(self):
        sections = detect_sections(SAMPLE_TEXT)
        names = [s.name for s in sections]
        assert "Introduction" in names

    def test_detects_methodology(self):
        sections = detect_sections(SAMPLE_TEXT)
        names = [s.name for s in sections]
        assert "Methodology" in names

    def test_detects_conclusion(self):
        sections = detect_sections(SAMPLE_TEXT)
        names = [s.name for s in sections]
        assert "Conclusion" in names

    def test_empty_text(self):
        assert detect_sections("") == []

    def test_sections_in_document_order(self):
        sections = detect_sections(SAMPLE_TEXT)
        offsets = [s.start_char for s in sections]
        assert offsets == sorted(offsets)

    def test_no_duplicate_section_names(self):
        sections = detect_sections(SAMPLE_TEXT)
        names = [s.name for s in sections]
        assert len(names) == len(set(names))


class TestSummarizer:
    def setup_method(self):
        self.preprocessed = preprocess(SAMPLE_TEXT)

    def test_concise_summary_shorter_than_detailed(self):
        _, concise_sents, _, detailed_sents = summarize(self.preprocessed.sentences)
        assert len(concise_sents) <= len(detailed_sents)

    def test_sentences_in_document_order(self):
        _, concise_sents, medium_sents, detailed_sents = summarize(self.preprocessed.sentences)
        for sents in [concise_sents, medium_sents, detailed_sents]:
            if len(sents) > 1:
                idxs = [self.preprocessed.sentences.index(s)
                        for s in sents if s in self.preprocessed.sentences]
                assert idxs == sorted(idxs)

    def test_summary_not_empty(self):
        requested, _, _, _ = summarize(self.preprocessed.sentences, "medium")
        assert requested.strip()

    def test_single_sentence_input(self):
        sentences = ["This is the only sentence in the document and it is quite long."]
        requested, c, m, d = summarize(sentences)
        assert requested == sentences[0]

    def test_empty_sentences(self):
        requested, c, m, d = summarize([])
        assert requested == ""

    def test_all_summary_types_returned(self):
        _, c, m, d = summarize(self.preprocessed.sentences)
        assert len(c) > 0
        assert len(m) > 0
        assert len(d) > 0


class TestKeywordExtractor:
    def test_returns_phrases(self):
        phrases = extract_key_phrases(SAMPLE_TEXT, max_phrases=10)
        assert len(phrases) > 0

    def test_max_phrases_respected(self):
        phrases = extract_key_phrases(SAMPLE_TEXT, max_phrases=5)
        assert len(phrases) <= 5

    def test_scores_in_range(self):
        phrases = extract_key_phrases(SAMPLE_TEXT)
        for p in phrases:
            assert 0.0 <= p.score <= 1.0

    def test_ranks_sequential(self):
        phrases = extract_key_phrases(SAMPLE_TEXT, max_phrases=10)
        ranks = [p.rank for p in phrases]
        assert ranks == list(range(1, len(phrases) + 1))

    def test_no_empty_phrases(self):
        phrases = extract_key_phrases(SAMPLE_TEXT)
        for p in phrases:
            assert p.phrase.strip()

    def test_empty_text_returns_empty(self):
        assert extract_key_phrases("") == []

    def test_scores_best_first(self):
        phrases = extract_key_phrases(SAMPLE_TEXT, max_phrases=10)
        scores = [p.score for p in phrases]
        assert scores == sorted(scores, reverse=True)


class TestStatistics:
    def setup_method(self):
        self.preprocessed = preprocess(SAMPLE_TEXT)
        self.summary = "This paper presents a novel approach to automated text summarisation."

    def test_word_count_positive(self):
        stats = compute_statistics(
            self.preprocessed.clean_text, self.summary,
            self.preprocessed.sentences, self.preprocessed.paragraphs,
        )
        assert stats["word_count"] > 0

    def test_summary_word_count(self):
        stats = compute_statistics(
            self.preprocessed.clean_text, self.summary,
            self.preprocessed.sentences, self.preprocessed.paragraphs,
        )
        assert stats["summary_word_count"] == len(self.summary.split())

    def test_reading_time_positive(self):
        stats = compute_statistics(
            self.preprocessed.clean_text, self.summary,
            self.preprocessed.sentences, self.preprocessed.paragraphs,
        )
        assert stats["estimated_reading_time_minutes"] > 0

    def test_ratio_between_0_and_1_for_summary(self):
        stats = compute_statistics(
            self.preprocessed.clean_text, self.summary,
            self.preprocessed.sentences, self.preprocessed.paragraphs,
        )
        assert 0.0 <= stats["summary_to_source_ratio"] <= 1.0

    def test_empty_text(self):
        stats = compute_statistics("", "", [], [])
        assert stats["word_count"] == 0
        assert stats["estimated_reading_time_minutes"] == 0.0


class TestEvidenceSummarizer:
    def setup_method(self):
        self.preprocessed = preprocess(SAMPLE_TEXT)
        self.sections = detect_sections(self.preprocessed.clean_text)

    def test_evidence_structure(self):
        req, c, m, d, ev = summarize_with_evidence(
            self.preprocessed.sentences,
            self.preprocessed.clean_text,
            self.sections,
            "medium",
        )
        assert req
        assert len(ev["medium"]) > 0
        for item in ev["medium"]:
            assert "index" in item
            assert "text" in item
            assert "score" in item
            assert "start_char" in item
            assert "end_char" in item
            assert "section" in item
            assert item["start_char"] <= item["end_char"]

    def test_evidence_levels(self):
        _, c, m, d, ev = summarize_with_evidence(
            self.preprocessed.sentences,
            self.preprocessed.clean_text,
            self.sections,
            "medium",
        )
        assert len(ev["concise"]) <= len(ev["medium"]) <= len(ev["detailed"])


class TestSectionSummaries:
    def setup_method(self):
        self.preprocessed = preprocess(SAMPLE_TEXT)
        self.sections = detect_sections(self.preprocessed.clean_text)

    def test_generate_section_summaries(self):
        sec_summaries = generate_section_summaries(
            self.preprocessed.clean_text,
            self.preprocessed.sentences,
            self.sections,
        )
        assert len(sec_summaries) == len(self.sections)
        for s in sec_summaries:
            assert s["name"]
            assert "summary_text" in s
            assert "word_count" in s
            assert s["word_count"] > 0

    def test_empty_sections_returns_empty(self):
        res = generate_section_summaries(self.preprocessed.clean_text, self.preprocessed.sentences, [])
        assert res == []


class TestMethodologyExtractor:
    def setup_method(self):
        self.preprocessed = preprocess(SAMPLE_TEXT)
        self.sections = detect_sections(self.preprocessed.clean_text)

    def test_extracts_9_dimensions(self):
        res = extract_methodology_and_findings(
            self.preprocessed.clean_text,
            self.preprocessed.sentences,
            self.sections,
        )
        assert res.total_dimensions == 9
        assert len(res.dimensions) == 9

    def test_dimension_fields(self):
        res = extract_methodology_and_findings(
            self.preprocessed.clean_text,
            self.preprocessed.sentences,
            self.sections,
        )
        for d in res.dimensions:
            assert d.dimension
            assert d.label
            assert isinstance(d.found, bool)
            assert d.summary
            if d.found:
                assert d.evidence
                assert d.section

    def test_sample_text_identifies_key_dimensions(self):
        res = extract_methodology_and_findings(
            self.preprocessed.clean_text,
            self.preprocessed.sentences,
            self.sections,
        )
        # In SAMPLE_TEXT, objectives, methodology, and findings are explicitly present
        dim_map = {d.dimension: d for d in res.dimensions}
        assert dim_map["objectives"].found is True
        assert dim_map["main_findings"].found is True

    def test_fallback_on_empty(self):
        res = extract_methodology_and_findings("", [], [])
        assert res.total_found == 0
        for d in res.dimensions:
            assert d.found is False
            assert "Not explicitly stated" in d.summary
            assert d.evidence is None

