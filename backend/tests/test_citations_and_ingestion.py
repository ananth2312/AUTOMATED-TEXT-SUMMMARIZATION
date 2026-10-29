"""
tests/test_citations_and_ingestion.py
─────────────────────────────────────
Automated unit and integration tests for:
1. Citation intelligence and reference parsing
2. In-text citation detection
3. arXiv/DOI identifier detection and metadata parsing
"""

import pytest
from app.nlp.citation_parser import (
    extract_references_from_text,
    detect_in_text_citations,
    format_paper_self_citation,
    parse_single_reference,
)
from app.nlp.section_detector import Section
from app.services.external_ingestion_service import detect_identifier_type


class TestCitationParser:
    def test_parse_numbered_reference(self):
        sample = '[1] A. Vaswani, N. Shazeer, N. Parmar, "Attention is all you need," in NeurIPS, 2017. doi:10.5555/3295222.3295349'
        parsed = parse_single_reference(sample)
        assert parsed.id == "1"
        assert "2017" in parsed.year
        assert "Attention is all you need" in parsed.title
        assert "@article" in parsed.bibtex
        assert "2017" in parsed.bibtex
        assert "Vaswani" in parsed.apa
        assert "[1]" in parsed.ieee

    def test_extract_references_from_text(self):
        text = (
            "This is the main body discussing transformers [1] and deep learning [2].\n\n"
            "References\n"
            "[1] A. Vaswani et al., Attention is all you need, 2017.\n"
            "[2] Y. LeCun, Y. Bengio, G. Hinton, Deep learning, Nature, 2015.\n"
        )
        sections = [
            Section(name="Introduction", start_char=0, end_char=70),
            Section(name="References", start_char=72, end_char=len(text)),
        ]
        refs = extract_references_from_text(text, sections)
        assert len(refs) == 2
        assert refs[0].id == "1"
        assert refs[1].id == "2"

    def test_detect_in_text_citations(self):
        text = "As shown by prior work [1] and recent advances [2, 3], attention is effective."
        sample_refs = [
            parse_single_reference("[1] Vaswani et al., 2017"),
            parse_single_reference("[2] LeCun et al., 2015"),
            parse_single_reference("[3] Devlin et al., 2018"),
        ]
        in_text = detect_in_text_citations(text, sample_refs)
        assert len(in_text) >= 2
        assert in_text[0]["marker"] == "[1]"
        assert "1" in in_text[0]["ref_ids"]

    def test_paper_self_citation(self):
        meta = {
            "authors": ["John Doe", "Jane Smith"],
            "year": "2026",
            "venue": "IEEE Transactions on NLP",
            "identifier_type": "doi",
            "identifier": "10.1109/TNNLS.2026.12345",
        }
        res = format_paper_self_citation("Novel Extractive Summarization", meta)
        assert "John Doe" in res["apa"]
        assert "@article" in res["bibtex"]
        assert "2026" in res["ieee"]


class TestExternalIdentifierDetector:
    def test_detect_arxiv_id(self):
        t, i = detect_identifier_type("1706.03762")
        assert t == "arxiv"
        assert i == "1706.03762"

    def test_detect_arxiv_url(self):
        t, i = detect_identifier_type("https://arxiv.org/abs/2305.18290v2")
        assert t == "arxiv"
        assert "2305.18290" in i

    def test_detect_doi(self):
        t, i = detect_identifier_type("10.1145/3318464.3389700")
        assert t == "doi"
        assert i == "10.1145/3318464.3389700"

    def test_detect_doi_url(self):
        t, i = detect_identifier_type("https://doi.org/10.1016/j.neucom.2021.08.132")
        assert t == "doi"
        assert "10.1016/j.neucom.2021.08.132" in i
