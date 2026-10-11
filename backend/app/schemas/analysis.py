"""
app/schemas/analysis.py
────────────────────────
Pydantic schemas for analysis request, results, and listing.
Scores from NLP algorithms are clearly labelled as algorithmic estimates.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ── Key-phrase item ───────────────────────────────────────────────────────────

class KeyPhrase(BaseModel):
    phrase: str
    score: float = Field(
        ...,
        description=(
            "Algorithmic relevance score (algorithm-specific scale). "
            "This is a machine-estimated ranking, not a verified measure of importance."
        ),
    )
    rank: int


# ── Detected section ─────────────────────────────────────────────────────────

class DetectedSection(BaseModel):
    name: str
    start_char: Optional[int] = None
    end_char: Optional[int] = None
    word_count: Optional[int] = None
    content_preview: Optional[str] = None   # first ~200 chars


# ── Statistics ───────────────────────────────────────────────────────────────

class DocumentStatistics(BaseModel):
    word_count: int
    character_count: int
    sentence_count: int
    paragraph_count: int
    estimated_reading_time_minutes: float
    summary_word_count: int
    summary_to_source_ratio: float
    words_per_minute_assumption: int = 200


# ── Evidence and Section Summaries ───────────────────────────────────────────

class SummarySentenceEvidence(BaseModel):
    index: int
    text: str
    score: float
    start_char: int
    end_char: int
    section: str


class SectionSummary(BaseModel):
    name: str
    summary_text: str
    word_count: int
    start_char: int
    end_char: int
    sentences: list[SummarySentenceEvidence] = []


class ExtractedDimensionSchema(BaseModel):
    dimension: str
    label: str
    found: bool
    summary: str
    evidence: Optional[str] = None
    section: Optional[str] = None
    char_start: Optional[int] = None
    char_end: Optional[int] = None


class MethodologyFindings(BaseModel):
    dimensions: list[ExtractedDimensionSchema]
    total_found: int
    total_dimensions: int


# ── Analysis result ───────────────────────────────────────────────────────────

class AnalysisResult(BaseModel):
    id: str = Field(..., alias="_id")
    user_id: str
    document_id: Optional[str] = None     # None when text was pasted directly
    title: str
    summary_type: str
    summary_text: str
    concise_summary: Optional[str] = None
    medium_summary: Optional[str] = None
    detailed_summary: Optional[str] = None
    key_phrases: list[KeyPhrase]
    detected_sections: list[DetectedSection]
    statistics: DocumentStatistics
    processing_status: str
    warnings: list[str]
    algorithm_versions: dict[str, str]
    source_text_preview: Optional[str] = None  # first 500 chars
    created_at: datetime

    # New Stage 1 features
    summary_sentences_with_evidence: Optional[list[SummarySentenceEvidence]] = None
    section_summaries: Optional[list[SectionSummary]] = None
    methodology_findings: Optional[MethodologyFindings] = None

    model_config = {"populate_by_name": True}


class AnalysisListItem(BaseModel):
    id: str = Field(..., alias="_id")
    document_id: Optional[str] = None
    title: str
    summary_type: str
    processing_status: str
    word_count: int
    created_at: datetime

    model_config = {"populate_by_name": True}


class AnalysisListResponse(BaseModel):
    items: list[AnalysisListItem]
    total: int
    page: int
    page_size: int


# ── Analyse requests ──────────────────────────────────────────────────────────

class AnalyzeDocumentRequest(BaseModel):
    summary_type: str = Field("medium", pattern="^(concise|medium|detailed)$")


# ── Dashboard stats ───────────────────────────────────────────────────────────

class DailyAnalysisCount(BaseModel):
    date: str
    count: int


class DashboardStats(BaseModel):
    total_documents: int
    total_analyses: int
    total_words_processed: int
    recent_analyses: list[AnalysisListItem]
    analyses_by_day: list[DailyAnalysisCount]
