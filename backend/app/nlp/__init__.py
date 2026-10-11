"""app/nlp/__init__.py"""
from .extractor import ExtractionResult, extract_text_from_pdf
from .preprocessor import PreprocessedText, preprocess
from .section_detector import Section, detect_sections
from .summarizer import (
    generate_section_summaries,
    summarize,
    summarize_with_evidence,
)
from .methodology_extractor import (
    ExtractedDimension,
    MethodologyFindingsResult,
    extract_methodology_and_findings,
)
from .keyword_extractor import ExtractedPhrase, extract_key_phrases
from .statistics import compute_statistics

__all__ = [
    "ExtractionResult", "extract_text_from_pdf",
    "PreprocessedText", "preprocess",
    "Section", "detect_sections",
    "summarize",
    "summarize_with_evidence",
    "generate_section_summaries",
    "ExtractedDimension",
    "MethodologyFindingsResult",
    "extract_methodology_and_findings",
    "ExtractedPhrase", "extract_key_phrases",
    "compute_statistics",
]
