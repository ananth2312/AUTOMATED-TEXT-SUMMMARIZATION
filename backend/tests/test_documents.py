"""
tests/test_documents.py
─────────────────────────
Tests for document upload, listing, retrieval, isolation, and deletion.
"""

import io
import fitz
import pytest
from fastapi.testclient import TestClient

from tests.conftest import auth_headers, register_and_login


def _create_sample_pdf_bytes(title: str = "Test Academic Paper") -> bytes:
    """Generate a valid PDF in memory using PyMuPDF."""
    doc = fitz.open()
    page = doc.new_page()
    content = (
        f"{title}\n\n"
        "Abstract\n"
        "Recent advances in natural language processing have enabled automated text summarization.\n"
        "This paper introduces a comprehensive benchmark on academic research papers.\n\n"
        "Introduction\n"
        "Academic literature is growing at an exponential rate. Researchers face information overload.\n"
        "Our method extracts key phrases and generates concise multi-length summaries.\n\n"
        "Methodology\n"
        "We construct a graph representation using TextRank sentence similarity.\n\n"
        "Conclusion\n"
        "The proposed architecture demonstrates superior efficiency and accuracy.\n"
    )
    page.insert_text((50, 72), content)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


class TestDocumentUpload:
    def test_upload_pdf_success(self, test_client: TestClient):
        token = register_and_login(test_client, "author1@example.com")
        pdf_bytes = _create_sample_pdf_bytes("Deep Learning in NLP")

        response = test_client.post(
            "/api/documents/upload",
            headers=auth_headers(token),
            data={"title": "Deep Learning in NLP"},
            files={"file": ("paper.pdf", pdf_bytes, "application/pdf")},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Deep Learning in NLP"
        assert data["page_count"] >= 1
        assert data["word_count"] > 10
        assert data["extraction_status"] == "success"
        assert "_id" in data
        assert "storage_key" not in data  # internal field not exposed

    def test_upload_non_pdf_rejected(self, test_client: TestClient):
        token = register_and_login(test_client, "author2@example.com")
        response = test_client.post(
            "/api/documents/upload",
            headers=auth_headers(token),
            data={"title": "Text File"},
            files={"file": ("notes.txt", b"plain text content", "text/plain")},
        )
        assert response.status_code == 415

    def test_upload_empty_pdf_rejected(self, test_client: TestClient):
        token = register_and_login(test_client, "author3@example.com")
        response = test_client.post(
            "/api/documents/upload",
            headers=auth_headers(token),
            data={"title": "Empty File"},
            files={"file": ("empty.pdf", b"", "application/pdf")},
        )
        assert response.status_code == 400

    def test_upload_unauthenticated(self, test_client: TestClient):
        pdf_bytes = _create_sample_pdf_bytes()
        response = test_client.post(
            "/api/documents/upload",
            data={"title": "Unauthenticated Paper"},
            files={"file": ("paper.pdf", pdf_bytes, "application/pdf")},
        )
        assert response.status_code == 401


class TestDocumentManagement:
    def test_list_and_search_documents(self, test_client: TestClient):
        token = register_and_login(test_client, "researcher@example.com")
        pdf1 = _create_sample_pdf_bytes("Quantum Computing Survey")
        pdf2 = _create_sample_pdf_bytes("Neural Networks Overview")

        test_client.post(
            "/api/documents/upload",
            headers=auth_headers(token),
            data={"title": "Quantum Computing Survey"},
            files={"file": ("quantum.pdf", pdf1, "application/pdf")},
        )
        test_client.post(
            "/api/documents/upload",
            headers=auth_headers(token),
            data={"title": "Neural Networks Overview"},
            files={"file": ("neural.pdf", pdf2, "application/pdf")},
        )

        # List all
        resp = test_client.get("/api/documents", headers=auth_headers(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

        # Search by keyword
        resp_search = test_client.get(
            "/api/documents?search=Quantum",
            headers=auth_headers(token),
        )
        assert resp_search.status_code == 200
        search_data = resp_search.json()
        assert search_data["total"] == 1
        assert "Quantum" in search_data["items"][0]["title"]

    def test_get_document_by_id(self, test_client: TestClient):
        token = register_and_login(test_client, "single_doc@example.com")
        pdf_bytes = _create_sample_pdf_bytes("Single Document Test")
        upload_resp = test_client.post(
            "/api/documents/upload",
            headers=auth_headers(token),
            data={"title": "Single Document Test"},
            files={"file": ("single.pdf", pdf_bytes, "application/pdf")},
        )
        doc_id = upload_resp.json()["_id"]

        resp = test_client.get(f"/api/documents/{doc_id}", headers=auth_headers(token))
        assert resp.status_code == 200
        assert resp.json()["_id"] == doc_id
        assert resp.json()["title"] == "Single Document Test"

    def test_user_cannot_access_other_users_document(self, test_client: TestClient):
        token_a = register_and_login(test_client, "user_a@example.com")
        token_b = register_and_login(test_client, "user_b@example.com")

        pdf_bytes = _create_sample_pdf_bytes("User A Confidential Paper")
        upload_resp = test_client.post(
            "/api/documents/upload",
            headers=auth_headers(token_a),
            data={"title": "User A Confidential Paper"},
            files={"file": ("confidential.pdf", pdf_bytes, "application/pdf")},
        )
        doc_id = upload_resp.json()["_id"]

        # User B attempts to access User A's document
        forbidden_resp = test_client.get(
            f"/api/documents/{doc_id}",
            headers=auth_headers(token_b),
        )
        assert forbidden_resp.status_code == 404

        # User B attempts to delete User A's document
        forbidden_del = test_client.delete(
            f"/api/documents/{doc_id}",
            headers=auth_headers(token_b),
        )
        assert forbidden_del.status_code == 404

    def test_delete_document_success(self, test_client: TestClient):
        token = register_and_login(test_client, "delete_doc@example.com")
        pdf_bytes = _create_sample_pdf_bytes("Document To Be Deleted")
        upload_resp = test_client.post(
            "/api/documents/upload",
            headers=auth_headers(token),
            data={"title": "Document To Be Deleted"},
            files={"file": ("to_delete.pdf", pdf_bytes, "application/pdf")},
        )
        doc_id = upload_resp.json()["_id"]

        del_resp = test_client.delete(f"/api/documents/{doc_id}", headers=auth_headers(token))
        assert del_resp.status_code == 200
        assert del_resp.json()["deleted"] is True

        # Ensure it is gone
        get_resp = test_client.get(f"/api/documents/{doc_id}", headers=auth_headers(token))
        assert get_resp.status_code == 404
