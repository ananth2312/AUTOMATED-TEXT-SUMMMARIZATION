"""
app/services/external_ingestion_service.py
─────────────────────────────────────────
Ingests academic research papers directly via:
1. arXiv ID or URL (e.g. 1706.03762, https://arxiv.org/abs/1706.03762)
2. DOI (e.g. 10.1145/3318464.3389700, https://doi.org/10.1145/3318464.3389700)

Fetches publication metadata (title, authors, year, abstract, venue)
and automatically downloads the PDF into storage for downstream NLP analysis.
"""

import io
import logging
import re
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

import httpx
from bson import ObjectId
from fastapi import HTTPException, status
from pymongo.database import Database

from app.config import get_settings
from app.nlp import extract_text_from_pdf
from app.services.analysis_service import run_analysis

logger = logging.getLogger(__name__)

# Regular expressions for identification
ARXIV_ID_PATTERN = re.compile(
    r"(?:arxiv\.org/(?:abs|pdf)/|arxiv:\s*|^)([0-9]{4}\.[0-9]{4,5}(?:v[0-9]+)?|[a-z\-]+/[0-9]{7})",
    re.IGNORECASE,
)
DOI_PATTERN = re.compile(
    r"(?:doi\.org/|doi:\s*|^)(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)",
    re.IGNORECASE,
)

USER_AGENT = "ResearchLens/1.0 (Academic Research Assistant; mailto:research@academic.edu)"


def detect_identifier_type(raw_input: str) -> Tuple[str, str]:
    """
    Detects whether the input is an arXiv identifier/URL or a DOI.
    Returns (type, normalized_id) where type is 'arxiv', 'doi', or 'unknown'.
    """
    clean = raw_input.strip()

    # Check arXiv first
    arxiv_match = ARXIV_ID_PATTERN.search(clean)
    if arxiv_match:
        # Strip trailing .pdf if matched
        aid = arxiv_match.group(1).rstrip(".pdf")
        return "arxiv", aid

    # Check DOI
    doi_match = DOI_PATTERN.search(clean)
    if doi_match:
        return "doi", doi_match.group(1).rstrip("/")

    return "unknown", clean


async def fetch_arxiv_metadata(arxiv_id: str) -> dict:
    """
    Queries the official arXiv Export API for paper metadata.
    """
    url = f"https://export.arxiv.org/api/query?id_list={arxiv_id}&max_results=1"
    async with httpx.AsyncClient(timeout=15.0, headers={"User-Agent": USER_AGENT}) as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
        except Exception as exc:
            logger.error("arXiv API query failed for %s: %s", arxiv_id, exc)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to connect to arXiv API: {exc}",
            )

    # Parse Atom XML
    try:
        root = ET.fromstring(resp.text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entry = root.find("atom:entry", ns)
        if entry is None:
            raise ValueError("No entry found")

        title = entry.find("atom:title", ns)
        clean_title = " ".join((title.text or "").split()) if title is not None else f"arXiv:{arxiv_id}"

        summary = entry.find("atom:summary", ns)
        clean_summary = " ".join((summary.text or "").split()) if summary is not None else ""

        authors = []
        for author_elem in entry.findall("atom:author", ns):
            name_elem = author_elem.find("atom:name", ns)
            if name_elem is not None and name_elem.text:
                authors.append(name_elem.text.strip())

        published = entry.find("atom:published", ns)
        year = published.text[:4] if published is not None and published.text else ""

        # Construct direct PDF URL
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

        return {
            "source": "arxiv",
            "identifier": arxiv_id,
            "title": clean_title,
            "authors": authors,
            "year": year,
            "abstract": clean_summary,
            "venue": "arXiv Preprint",
            "pdf_url": pdf_url,
        }
    except Exception as exc:
        logger.error("Failed to parse arXiv XML response: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"arXiv paper '{arxiv_id}' was not found or could not be parsed.",
        )


async def fetch_doi_metadata(doi: str) -> dict:
    """
    Queries Crossref API and Semantic Scholar for DOI metadata and open-access PDF link.
    """
    clean_doi = doi.strip()
    headers = {"User-Agent": USER_AGENT}

    crossref_url = f"https://api.crossref.org/works/{clean_doi}"
    s2_url = f"https://api.semanticscholar.org/graph/v1/paper/{clean_doi}?fields=title,authors,year,abstract,openAccessPdf,venue"

    title = ""
    authors = []
    year = ""
    abstract = ""
    venue = ""
    pdf_url = None

    async with httpx.AsyncClient(timeout=15.0, headers=headers) as client:
        # Try Crossref first
        try:
            cr_resp = await client.get(crossref_url)
            if cr_resp.status_code == 200:
                data = cr_resp.json().get("message", {})
                titles = data.get("title", [])
                if titles:
                    title = titles[0]

                for a in data.get("author", []):
                    name_parts = [a.get("given", ""), a.get("family", "")]
                    full_name = " ".join(p for p in name_parts if p).strip()
                    if full_name:
                        authors.append(full_name)

                # Year
                published = (
                    data.get("published-print")
                    or data.get("published-online")
                    or data.get("created")
                    or {}
                )
                date_parts = published.get("date-parts", [[]])
                if date_parts and date_parts[0]:
                    year = str(date_parts[0][0])

                venues = data.get("container-title", [])
                if venues:
                    venue = venues[0]

                abstract_raw = data.get("abstract", "")
                if abstract_raw:
                    # Strip JATS XML tags if present
                    abstract = re.sub(r"<[^>]+>", " ", abstract_raw).strip()
                    abstract = " ".join(abstract.split())

                # Check for direct PDF in links
                for link in data.get("link", []):
                    if link.get("content-type") == "application/pdf" and link.get("URL"):
                        pdf_url = link.get("URL")
                        break
        except Exception as exc:
            logger.warning("Crossref lookup for %s failed: %s", clean_doi, exc)

        # Also query Semantic Scholar to get open-access PDF link if needed
        if not pdf_url:
            try:
                s2_resp = await client.get(s2_url)
                if s2_resp.status_code == 200:
                    s2_data = s2_resp.json()
                    if not title and s2_data.get("title"):
                        title = s2_data["title"]
                    if not authors and s2_data.get("authors"):
                        authors = [a.get("name", "") for a in s2_data["authors"] if a.get("name")]
                    if not year and s2_data.get("year"):
                        year = str(s2_data["year"])
                    if not abstract and s2_data.get("abstract"):
                        abstract = s2_data["abstract"]
                    if not venue and s2_data.get("venue"):
                        venue = s2_data["venue"]

                    oa_pdf = s2_data.get("openAccessPdf")
                    if oa_pdf and oa_pdf.get("url"):
                        pdf_url = oa_pdf["url"]
            except Exception as exc:
                logger.warning("Semantic Scholar lookup failed: %s", exc)

    if not title:
        title = f"DOI:{clean_doi}"

    return {
        "source": "doi",
        "identifier": clean_doi,
        "title": title,
        "authors": authors,
        "year": year,
        "abstract": abstract,
        "venue": venue,
        "pdf_url": pdf_url,
    }


async def download_pdf_bytes(pdf_url: str) -> bytes:
    """
    Downloads the PDF binary with redirection and standard browser User-Agent headers.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/pdf,*/*",
    }
    async with httpx.AsyncClient(timeout=35.0, headers=headers, follow_redirects=True) as client:
        try:
            resp = await client.get(pdf_url)
            resp.raise_for_status()
            content = resp.content
            if len(content) < 500 or not content.startswith(b"%PDF"):
                logger.warning("Downloaded content from %s is not a valid PDF header.", pdf_url)
                raise ValueError("Downloaded file is not a valid PDF.")
            return content
        except Exception as exc:
            logger.error("Failed to download PDF from %s: %s", pdf_url, exc)
            raise


def create_synthetic_abstract_pdf(meta: dict) -> bytes:
    """
    Generates a clean vector PDF when direct full-text PDF is paywalled,
    allowing the paper to still be processed, read, and cited seamlessly.
    """
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
    from reportlab.lib import colors

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, leftMargin=54, rightMargin=54, topMargin=54, bottomMargin=54)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=12,
    )
    meta_style = ParagraphStyle(
        "DocMeta",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#475569"),
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "DocBody",
        parent=styles["Normal"],
        fontSize=11,
        leading=16,
        textColor=colors.HexColor("#334155"),
        spaceAfter=12,
    )

    story = [
        Paragraph(meta.get("title", "Academic Paper"), title_style),
        Spacer(1, 4),
    ]

    authors_str = ", ".join(meta.get("authors", [])) or "Authors not listed"
    story.append(Paragraph(f"<b>Authors:</b> {authors_str}", meta_style))
    if meta.get("year"):
        story.append(Paragraph(f"<b>Year:</b> {meta.get('year')}", meta_style))
    if meta.get("venue"):
        story.append(Paragraph(f"<b>Venue:</b> {meta.get('venue')}", meta_style))
    if meta.get("identifier"):
        story.append(Paragraph(f"<b>Identifier:</b> {meta.get('identifier')}", meta_style))

    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=15))
    story.append(Paragraph("<b>Abstract</b>", styles["Heading2"]))
    story.append(Spacer(1, 6))

    abstract_text = meta.get("abstract") or "No abstract text was provided in the publisher metadata."
    story.append(Paragraph(abstract_text, body_style))

    doc.build(story)
    return buf.getvalue()


async def ingest_external_paper(
    *,
    db: Database,
    user_id: str,
    raw_input: str,
    summary_type: str = "medium",
    auto_analyze: bool = True,
) -> dict:
    """
    Main entry point for importing an academic paper via arXiv ID/URL or DOI.
    """
    settings = get_settings()
    id_type, normalized_id = detect_identifier_type(raw_input)

    if id_type == "unknown":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Could not recognize input format. Please provide a valid arXiv ID "
                "(e.g., '1706.03762' or 'https://arxiv.org/abs/1706.03762') or a DOI "
                "(e.g., '10.1145/3318464.3389700')."
            ),
        )

    # 1. Fetch metadata
    logger.info("Fetching metadata for %s identifier: %s", id_type, normalized_id)
    if id_type == "arxiv":
        meta = await fetch_arxiv_metadata(normalized_id)
    else:
        meta = await fetch_doi_metadata(normalized_id)

    # 2. Download or generate PDF
    pdf_bytes = None
    warnings = []

    if meta.get("pdf_url"):
        try:
            logger.info("Downloading PDF from %s", meta["pdf_url"])
            pdf_bytes = await download_pdf_bytes(meta["pdf_url"])
        except Exception as exc:
            logger.warning("Direct PDF download failed (%s), falling back to structured paper document.", exc)
            warnings.append(f"Full-text PDF download encountered: {exc}. Ingested abstract & publication records.")
            pdf_bytes = create_synthetic_abstract_pdf(meta)
    else:
        warnings.append("Direct open-access PDF link unavailable. Ingested publication metadata and abstract.")
        pdf_bytes = create_synthetic_abstract_pdf(meta)

    # 3. Store PDF
    storage_key = f"{uuid.uuid4().hex}.pdf"
    storage_path = settings.storage_path / storage_key
    storage_path.write_bytes(pdf_bytes)

    # 4. Extract text
    extraction = extract_text_from_pdf(storage_path)
    extraction_warnings = list(warnings) + list(extraction.warnings)

    # Merge publication metadata
    doc_meta = {
        "title": meta.get("title", ""),
        "authors": meta.get("authors", []),
        "year": meta.get("year", ""),
        "venue": meta.get("venue", ""),
        "identifier_type": id_type,
        "identifier": normalized_id,
        "source_url": meta.get("pdf_url", ""),
    }

    now = datetime.now(timezone.utc)
    original_filename = f"{normalized_id.replace('/', '_')}.pdf"

    doc_record = {
        "user_id": ObjectId(user_id),
        "title": meta.get("title") or original_filename,
        "original_filename": original_filename,
        "storage_key": storage_key,
        "content_type": "application/pdf",
        "file_size": len(pdf_bytes),
        "page_count": extraction.page_count,
        "word_count": len(extraction.text.split()) if extraction.text else 0,
        "extraction_status": extraction.status,
        "extracted_text": extraction.text,
        "extraction_warnings": extraction_warnings,
        "pdf_metadata": doc_meta,
        "created_at": now,
        "updated_at": now,
    }

    result = db.documents.insert_one(doc_record)
    doc_id = str(result.inserted_id)
    doc_record["_id"] = doc_id
    doc_record["user_id"] = user_id
    doc_record.pop("storage_key", None)
    doc_record.pop("extracted_text", None)

    # 5. Optionally run automatic analysis immediately
    analysis_id = None
    if auto_analyze and extraction.text and len(extraction.text.strip()) >= 50:
        logger.info("Auto-analyzing imported paper (doc_id=%s)", doc_id)
        analysis = run_analysis(
            db=db,
            user_id=user_id,
            title=doc_record["title"],
            raw_text=extraction.text,
            summary_type=summary_type,
            document_id=doc_id,
            existing_warnings=extraction_warnings,
        )
        analysis_id = analysis["_id"]

    return {
        "document": doc_record,
        "metadata": meta,
        "analysis_id": analysis_id,
    }
