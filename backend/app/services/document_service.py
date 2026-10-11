"""
app/services/document_service.py
──────────────────────────────────
Document upload, storage, and management service.

Responsibilities:
- Validate uploaded files (type, size, filename)
- Store PDFs with opaque UUID-based filenames (never expose internal paths)
- Extract PDF text and metadata
- Persist document records to MongoDB
- Delete documents and associated analyses
- List and search user documents
"""

import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from bson import ObjectId
from fastapi import UploadFile, HTTPException, status
from pymongo.database import Database

from app.config import get_settings
from app.nlp import extract_text_from_pdf

logger = logging.getLogger(__name__)

_ALLOWED_CONTENT_TYPES = {"application/pdf"}
_ALLOWED_EXTENSIONS = {".pdf"}


# ── Upload ────────────────────────────────────────────────────────────────────

async def save_uploaded_document(
    *,
    db: Database,
    user_id: str,
    file: UploadFile,
    title: str,
) -> dict:
    """
    Validate, store, and record an uploaded PDF.

    :param db:       MongoDB database.
    :param user_id:  Authenticated user ID.
    :param file:     FastAPI UploadFile object.
    :param title:    User-supplied document title.
    :returns: The inserted document record dict.
    :raises HTTPException: For invalid files.
    """
    settings = get_settings()

    # ── Validate filename and content type ────────────────────────────────
    original_filename = file.filename or "untitled.pdf"
    suffix = Path(original_filename).suffix.lower()

    if suffix not in _ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Only PDF files are supported. Received: '{suffix or 'unknown'}'.",
        )

    content_type = file.content_type or ""
    # Allow lenient content-type check (browsers sometimes send wrong type)
    if content_type and content_type not in _ALLOWED_CONTENT_TYPES:
        # Warning only – content_type from browser is not always reliable
        logger.warning("Unexpected content_type '%s' for file '%s'.", content_type, original_filename)

    # ── Read file bytes ───────────────────────────────────────────────────
    data = await file.read()
    file_size = len(data)

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )
    if file_size > settings.MAX_UPLOAD_SIZE:
        max_mb = settings.MAX_UPLOAD_SIZE // (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the {max_mb} MB upload limit.",
        )

    # ── Store with opaque key (UUID) ──────────────────────────────────────
    storage_key = f"{uuid.uuid4().hex}{suffix}"
    storage_path = settings.storage_path / storage_key
    storage_path.write_bytes(data)
    logger.info("Stored file '%s' as '%s' (%d bytes).", original_filename, storage_key, file_size)

    # ── Extract text ───────────────────────────────────────────────────────
    extraction = extract_text_from_pdf(storage_path)

    # ── Persist document record ────────────────────────────────────────────
    now = datetime.now(timezone.utc)
    doc = {
        "user_id": ObjectId(user_id),
        "title": title or original_filename,
        "original_filename": original_filename,
        "storage_key": storage_key,        # opaque; never sent to client
        "content_type": "application/pdf",
        "file_size": file_size,
        "page_count": extraction.page_count,
        "word_count": len(extraction.text.split()) if extraction.text else 0,
        "extraction_status": extraction.status,
        "extracted_text": extraction.text,  # stored for re-analysis
        "extraction_warnings": extraction.warnings,
        "pdf_metadata": extraction.metadata,
        "created_at": now,
        "updated_at": now,
    }

    result = db.documents.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    doc["user_id"] = user_id
    # Remove internal fields before returning
    doc.pop("storage_key", None)
    doc.pop("extracted_text", None)

    return doc


# ── Retrieval ─────────────────────────────────────────────────────────────────

def get_document_by_id(db: Database, document_id: str, user_id: str) -> dict:
    """
    Fetch a document by ID, enforcing user ownership.

    :raises HTTPException 404: Document not found or not owned by user.
    """
    try:
        oid = ObjectId(document_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Document not found.")

    doc = db.documents.find_one({"_id": oid, "user_id": ObjectId(user_id)})
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    return _sanitise_document(doc)


def list_user_documents(
    db: Database,
    user_id: str,
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
) -> dict:
    """
    Return a paginated list of the user's documents.
    Optionally filter by title substring (case-insensitive).
    """
    query: dict = {"user_id": ObjectId(user_id)}
    if search:
        import re
        query["title"] = {"$regex": re.escape(search), "$options": "i"}

    total = db.documents.count_documents(query)
    skip = (page - 1) * page_size
    cursor = (
        db.documents
        .find(query, {"storage_key": 0, "extracted_text": 0})
        .sort("created_at", -1)
        .skip(skip)
        .limit(page_size)
    )
    items = [_sanitise_document(d) for d in cursor]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


# ── Deletion ──────────────────────────────────────────────────────────────────

def delete_document(db: Database, document_id: str, user_id: str) -> dict:
    """
    Delete a document record, its stored file, and all associated analyses.

    :returns: Deletion summary dict.
    :raises HTTPException 404: If not found or not owned.
    """
    settings = get_settings()
    try:
        oid = ObjectId(document_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Document not found.")

    doc = db.documents.find_one({"_id": oid, "user_id": ObjectId(user_id)})
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    # Delete stored file
    storage_key = doc.get("storage_key")
    if storage_key:
        file_path = settings.storage_path / storage_key
        if file_path.exists():
            file_path.unlink()
            logger.info("Deleted file: %s", storage_key)

    # Delete all analyses linked to this document
    analysis_result = db.analyses.delete_many({"document_id": oid})

    # Delete the document record
    db.documents.delete_one({"_id": oid})

    logger.info(
        "Deleted document %s and %d analyses for user %s.",
        document_id, analysis_result.deleted_count, user_id,
    )
    return {
        "deleted": True,
        "document_id": document_id,
        "analyses_deleted": analysis_result.deleted_count,
    }


# ── Get extracted text for re-analysis ────────────────────────────────────────

def get_extracted_text(db: Database, document_id: str, user_id: str) -> str:
    """Return the stored extracted text for a document (ownership enforced)."""
    try:
        oid = ObjectId(document_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Document not found.")

    doc = db.documents.find_one(
        {"_id": oid, "user_id": ObjectId(user_id)},
        {"extracted_text": 1, "extraction_status": 1},
    )
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    if doc.get("extraction_status") == "failed":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Text extraction failed for this document. Cannot analyse.",
        )
    return doc.get("extracted_text", "")


# ── Internal helpers ──────────────────────────────────────────────────────────

def _sanitise_document(doc: dict) -> dict:
    """Remove internal fields and stringify ObjectIds."""
    doc = dict(doc)
    doc["_id"] = str(doc["_id"])
    doc["user_id"] = str(doc.get("user_id", ""))
    doc.pop("storage_key", None)
    doc.pop("extracted_text", None)
    return doc
