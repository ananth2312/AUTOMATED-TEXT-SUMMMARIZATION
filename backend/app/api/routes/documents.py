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

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from pymongo.database import Database

from app.core.dependencies import CurrentUser, get_db
from app.schemas import DocumentListResponse, DocumentMetadata
from app.services import (
    delete_document,
    get_document_by_id,
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
