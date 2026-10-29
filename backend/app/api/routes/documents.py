"""
app/api/routes/documents.py
────────────────────────────
Document management endpoints:
  POST   /api/documents/upload
  GET    /api/documents
  GET    /api/documents/{document_id}
  DELETE /api/documents/{document_id}
"""

from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from pymongo.database import Database

from app.config import get_settings
from app.core.dependencies import CurrentUser, get_db
from app.schemas import (
    DocumentListResponse,
    DocumentMetadata,
    ExternalIngestRequest,
    ExternalMetadataPreview,
)
from app.services import (
    delete_document,
    get_document_by_id,
    ingest_external_paper,
    list_user_documents,
    save_uploaded_document,
)

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post(
    "/upload",
    response_model=DocumentMetadata,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a PDF research paper",
    description=(
        "Accepts a PDF file (max 20 MB). Extracts text and stores document metadata. "
        "Returns extraction status – check `extraction_status` to determine if text "
        "is available for analysis."
    ),
)
async def upload_document(
    file: UploadFile = File(..., description="PDF file to upload"),
    title: str = Form(..., min_length=1, max_length=300, description="Document title"),
    current_user: CurrentUser = None,
    db: Database = Depends(get_db),
):
    user_id = str(current_user["_id"])
    return await save_uploaded_document(
        db=db,
        user_id=user_id,
        file=file,
        title=title,
    )


@router.post(
    "/import-external",
    summary="Import an academic research paper via arXiv ID, arXiv URL, or DOI",
    status_code=status.HTTP_201_CREATED,
)
async def import_external(
    payload: ExternalIngestRequest,
    current_user: CurrentUser = None,
    db: Database = Depends(get_db),
):
    user_id = str(current_user["_id"])
    return await ingest_external_paper(
        db=db,
        user_id=user_id,
        raw_input=payload.url_or_identifier,
        summary_type=payload.summary_type,
        auto_analyze=payload.auto_analyze,
    )


@router.post(
    "/preview-external",
    response_model=ExternalMetadataPreview,
    summary="Preview publication metadata for an arXiv ID or DOI prior to import",
)
async def preview_external(
    payload: ExternalIngestRequest,
    current_user: CurrentUser = None,
):
    from app.services.external_ingestion_service import (
        detect_identifier_type,
        fetch_arxiv_metadata,
        fetch_doi_metadata,
    )

    id_type, normalized_id = detect_identifier_type(payload.url_or_identifier)
    if id_type == "arxiv":
        meta = await fetch_arxiv_metadata(normalized_id)
    elif id_type == "doi":
        meta = await fetch_doi_metadata(normalized_id)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not recognize input as a valid arXiv ID/URL or DOI.",
        )
    return meta


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="List the current user's uploaded documents",
)
def list_documents(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page"),
    search: Optional[str] = Query(None, max_length=200, description="Filter by title"),
    current_user: CurrentUser = None,
    db: Database = Depends(get_db),
):
    user_id = str(current_user["_id"])
    return list_user_documents(db, user_id=user_id, page=page, page_size=page_size, search=search)


@router.get(
    "/{document_id}",
    response_model=DocumentMetadata,
    summary="Get a single document's metadata",
)
def get_document(
    document_id: str,
    current_user: CurrentUser = None,
    db: Database = Depends(get_db),
):
    return get_document_by_id(db, document_id=document_id, user_id=str(current_user["_id"]))


@router.get(
    "/{document_id}/pdf",
    summary="Stream or download the original PDF document file for the interactive reader",
)
def stream_document_pdf(
    document_id: str,
    current_user: CurrentUser = None,
    db: Database = Depends(get_db),
):
    try:
        oid = ObjectId(document_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Document not found.")

    doc = db.documents.find_one({"_id": oid, "user_id": ObjectId(current_user["_id"])})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    storage_key = doc.get("storage_key")
    if not storage_key:
        raise HTTPException(status_code=404, detail="No PDF storage record for this document.")

    settings = get_settings()
    pdf_path = settings.storage_path / storage_key
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="Document PDF file is missing from storage.")

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=doc.get("original_filename", "paper.pdf"),
    )


@router.delete(
    "/{document_id}",
    summary="Delete a document and all its associated analyses",
    description=(
        "Permanently deletes the document record, stored PDF file, and all linked analyses. "
        "This action cannot be undone."
    ),
)
def delete_doc(
    document_id: str,
    current_user: CurrentUser = None,
    db: Database = Depends(get_db),
):
    return delete_document(db, document_id=document_id, user_id=str(current_user["_id"]))

