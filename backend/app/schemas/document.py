"""
app/schemas/document.py
────────────────────────
Pydantic schemas for document upload, metadata, and listing endpoints.
storage_key (opaque UUID-based filename) is never exposed in responses;
only safe metadata is returned to the client.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    """Returned after a successful upload or document fetch."""
    id: str = Field(..., alias="_id")
    user_id: str
    title: str
    original_filename: str
    content_type: str
    file_size: int
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    extraction_status: str   # pending | success | failed | low_quality
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"populate_by_name": True}


class DocumentListItem(BaseModel):
    """Compact representation used in list/search responses."""
    id: str = Field(..., alias="_id")
    title: str
    original_filename: str
    file_size: int
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    extraction_status: str
    created_at: datetime

    model_config = {"populate_by_name": True}


class DocumentListResponse(BaseModel):
    items: list[DocumentListItem]
    total: int
    page: int
    page_size: int


class TextInputRequest(BaseModel):
    """For the direct-text analysis endpoint."""
    title: str = Field(..., min_length=1, max_length=300)
    text: str = Field(..., min_length=50, description="Minimum 50 characters of text.")
    summary_type: str = Field("medium", pattern="^(concise|medium|detailed)$")


class ExternalIngestRequest(BaseModel):
    """For importing a paper via arXiv ID, arXiv URL, or DOI."""
    url_or_identifier: str = Field(..., min_length=3, description="arXiv ID, arXiv URL, or DOI")
    summary_type: str = Field("medium", pattern="^(concise|medium|detailed)$")
    auto_analyze: bool = True


class ExternalMetadataPreview(BaseModel):
    """Publication metadata fetched before or during ingestion."""
    source: str
    identifier: str
    title: str
    authors: list[str] = []
    year: str = ""
    abstract: str = ""
    venue: str = ""
    pdf_url: Optional[str] = None
