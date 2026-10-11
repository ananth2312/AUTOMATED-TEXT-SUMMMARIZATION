"""
tests/test_analyses.py
──────────────────────
Integration tests for the analysis endpoints:
  - Text analysis (pasted text)
  - Listing analyses
  - Fetching a single analysis
  - Export (TXT)
  - Dashboard stats
  - User isolation (cannot access another user's analyses)
"""

from fastapi.testclient import TestClient
from tests.conftest import auth_headers, register_and_login

SAMPLE_TEXT = (
    "Abstract. This paper presents a study of machine learning algorithms. "
    "We compare several approaches including decision trees, random forests, "
    "and neural networks. The experiments show that deep learning models "
    "outperform classical methods on large datasets. "
    "Introduction. Machine learning has become ubiquitous in modern computing. "
    "Applications range from natural language processing to computer vision. "
    "Methodology. We collected 10,000 samples from publicly available datasets. "
    "Each model was trained for 50 epochs with early stopping. "
    "Results. The neural network achieved 94% accuracy on the test set. "
    "Classical models peaked at 87% accuracy. "
    "Conclusion. Deep learning is effective for classification tasks at scale. "
    "Future work will explore semi-supervised learning approaches."
)


class TestTextAnalysis:
    def test_analyse_text_success(self, test_client: TestClient):
        token = register_and_login(test_client, "analyser@example.com")
        resp = test_client.post(
            "/api/analyses/text",
            json={"title": "ML Comparison", "text": SAMPLE_TEXT, "summary_type": "medium"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["title"] == "ML Comparison"
        assert data["summary_text"]
        assert len(data["key_phrases"]) > 0
        assert data["statistics"]["word_count"] > 0

    def test_analyse_requires_auth(self, test_client: TestClient):
        resp = test_client.post("/api/analyses/text", json={
            "title": "No auth", "text": SAMPLE_TEXT, "summary_type": "medium"
        })
        assert resp.status_code == 401

    def test_analyse_text_too_short(self, test_client: TestClient):
        token = register_and_login(test_client, "short@example.com")
        resp = test_client.post(
            "/api/analyses/text",
            json={"title": "Short", "text": "Too short.", "summary_type": "medium"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 422

    def test_analyse_invalid_summary_type(self, test_client: TestClient):
        token = register_and_login(test_client, "badtype@example.com")
        resp = test_client.post(
            "/api/analyses/text",
            json={"title": "Test", "text": SAMPLE_TEXT, "summary_type": "invalid"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 422

    def test_all_summary_types_present(self, test_client: TestClient):
        token = register_and_login(test_client, "types@example.com")
        resp = test_client.post(
            "/api/analyses/text",
            json={"title": "Types", "text": SAMPLE_TEXT, "summary_type": "detailed"},
            headers=auth_headers(token),
        )
        data = resp.json()
        assert data.get("concise_summary")
        assert data.get("medium_summary")
        assert data.get("detailed_summary")

    def test_stage1_fields_returned(self, test_client: TestClient):
        token = register_and_login(test_client, "stage1@example.com")
        resp = test_client.post(
            "/api/analyses/text",
            json={"title": "Stage 1 Paper", "text": SAMPLE_TEXT, "summary_type": "medium"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "summary_sentences_with_evidence" in data
        assert isinstance(data["summary_sentences_with_evidence"], list)
        assert len(data["summary_sentences_with_evidence"]) > 0

        assert "section_summaries" in data
        assert isinstance(data["section_summaries"], list)
        assert len(data["section_summaries"]) > 0

        assert "methodology_findings" in data
        mf = data["methodology_findings"]
        assert "dimensions" in mf
        assert mf["total_dimensions"] == 9
        assert mf["total_found"] > 0


class TestAnalysisList:
    def test_list_analyses(self, test_client: TestClient):
        token = register_and_login(test_client, "list@example.com")
        # Create one analysis
        test_client.post(
            "/api/analyses/text",
            json={"title": "Paper 1", "text": SAMPLE_TEXT, "summary_type": "medium"},
            headers=auth_headers(token),
        )
        resp = test_client.get("/api/analyses", headers=auth_headers(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1

    def test_list_empty(self, test_client: TestClient):
        token = register_and_login(test_client, "empty@example.com")
        resp = test_client.get("/api/analyses", headers=auth_headers(token))
        assert resp.status_code == 200
        assert resp.json()["total"] == 0


class TestUserIsolation:
    def test_cannot_access_other_users_analysis(self, test_client: TestClient):
        token_a = register_and_login(test_client, "usera@example.com")
        token_b = register_and_login(test_client, "userb@example.com")

        resp = test_client.post(
            "/api/analyses/text",
            json={"title": "User A Paper", "text": SAMPLE_TEXT, "summary_type": "medium"},
            headers=auth_headers(token_a),
        )
        analysis_id = resp.json()["_id"]

        # User B should not be able to access User A's analysis
        resp_b = test_client.get(
            f"/api/analyses/{analysis_id}",
            headers=auth_headers(token_b),
        )
        assert resp_b.status_code == 404


class TestExport:
    def test_txt_export(self, test_client: TestClient):
        token = register_and_login(test_client, "export@example.com")
        resp = test_client.post(
            "/api/analyses/text",
            json={"title": "Export Test", "text": SAMPLE_TEXT, "summary_type": "medium"},
            headers=auth_headers(token),
        )
        analysis_id = resp.json()["_id"]

        export_resp = test_client.get(
            f"/api/analyses/{analysis_id}/export?format=txt",
            headers=auth_headers(token),
        )
        assert export_resp.status_code == 200
        assert export_resp.headers["content-type"].startswith("text/plain")
        content = export_resp.content.decode("utf-8")
        assert "Export Test" in content
        assert "OVERALL EXTRACTIVE SUMMARY" in content
        assert "RESEARCH METHODOLOGY & FINDINGS" in content
        assert "SECTION-WISE INTELLIGENT SUMMARIES" in content
        assert "KEY PHRASES" in content

    def test_pdf_export(self, test_client: TestClient):
        token = register_and_login(test_client, "pdfexport@example.com")
        resp = test_client.post(
            "/api/analyses/text",
            json={"title": "PDF Test", "text": SAMPLE_TEXT, "summary_type": "medium"},
            headers=auth_headers(token),
        )
        analysis_id = resp.json()["_id"]

        export_resp = test_client.get(
            f"/api/analyses/{analysis_id}/export?format=pdf",
            headers=auth_headers(token),
        )
        assert export_resp.status_code == 200
        assert export_resp.headers["content-type"] == "application/pdf"
        assert len(export_resp.content) > 1000
        assert export_resp.content.startswith(b"%PDF")



class TestDashboard:
    def test_dashboard_stats(self, test_client: TestClient):
        token = register_and_login(test_client, "dash@example.com")
        test_client.post(
            "/api/analyses/text",
            json={"title": "Dash Paper", "text": SAMPLE_TEXT, "summary_type": "medium"},
            headers=auth_headers(token),
        )
        resp = test_client.get("/api/dashboard", headers=auth_headers(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_analyses"] == 1
        assert data["total_words_processed"] > 0
        assert isinstance(data["recent_analyses"], list)
