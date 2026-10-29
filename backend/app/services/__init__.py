"""app/services/__init__.py"""
from .auth_service import (
    register_user, authenticate_user,
    get_user_profile, update_user_profile, change_password,
)
from .document_service import (
    save_uploaded_document, get_document_by_id,
    list_user_documents, delete_document, get_extracted_text,
)
from .analysis_service import run_analysis
from .export_service import generate_txt_export, generate_pdf_export
from .external_ingestion_service import ingest_external_paper

__all__ = [
    "register_user", "authenticate_user",
    "get_user_profile", "update_user_profile", "change_password",
    "save_uploaded_document", "get_document_by_id",
    "list_user_documents", "delete_document", "get_extracted_text",
    "run_analysis",
    "generate_txt_export", "generate_pdf_export",
    "ingest_external_paper",
]

