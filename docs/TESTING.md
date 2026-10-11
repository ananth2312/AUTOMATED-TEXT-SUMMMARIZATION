# Verification and Testing Report

This document records the testing strategy, test suites, actual execution logs, and verified outcomes for the **ResearchLens** automated academic paper summarization application.

---

## 1. Testing Strategy

The quality assurance strategy comprises four verification layers:
1. **Backend Unit Tests:** Isolated algorithmic verification of preprocessing, TextRank sentence graph construction, PageRank scoring, YAKE keyphrase extraction, and statistics calculation.
2. **Backend API & Integration Tests:** End-to-end verification of FastAPI endpoints using `starlette.testclient.TestClient`, real MongoDB queries, JWT authentication, and file upload processing.
3. **Frontend Component & Integration Tests:** Automated UI testing using Vitest, jsdom, and React Testing Library verifying form validation, navigation guards, and responsible-use notices.
4. **NLP Benchmarking Suite:** Quantitative evaluation of summarization (ROUGE-1, ROUGE-2, ROUGE-L) and keyword extraction against peer-reviewed landmark papers.

---

## 2. Verified Test Execution Results

### 2.1 Backend Pytest Suite Summary
- **Test Runner:** `pytest 8.3.4` (Python 3.12.5, Windows 11)
- **Total Tests:** 64
- **Passed:** **64 (100%)**
- **Failed:** 0
- **Duration:** 12.08 seconds

```
============================= test session starts =============================
platform win32 -- Python 3.12.5, pytest-8.3.4, pluggy-1.6.0
rootdir: D:\S7_Project(New)\academic-research-summarizer\backend
configfile: pytest.ini
collected 64 items

tests/test_analyses.py::TestTextAnalysis::test_analyse_text_success PASSED
tests/test_analyses.py::TestTextAnalysis::test_analyse_requires_auth PASSED
tests/test_analyses.py::TestTextAnalysis::test_analyse_text_too_short PASSED
tests/test_analyses.py::TestTextAnalysis::test_analyse_invalid_summary_type PASSED
tests/test_analyses.py::TestTextAnalysis::test_all_summary_types_present PASSED
tests/test_analyses.py::TestAnalysisList::test_list_analyses PASSED
tests/test_analyses.py::TestAnalysisList::test_list_empty PASSED
tests/test_analyses.py::TestUserIsolation::test_cannot_access_other_users_analysis PASSED
tests/test_analyses.py::TestExport::test_txt_export PASSED
tests/test_analyses.py::TestDashboard::test_dashboard_stats PASSED
tests/test_auth.py::test_health_endpoint PASSED
tests/test_auth.py::TestRegistration::test_register_success PASSED
tests/test_auth.py::TestRegistration::test_register_duplicate_email PASSED
tests/test_auth.py::TestRegistration::test_register_weak_password_no_uppercase PASSED
tests/test_auth.py::TestRegistration::test_register_weak_password_no_digit PASSED
tests/test_auth.py::TestRegistration::test_register_missing_email PASSED
tests/test_auth.py::TestRegistration::test_register_short_name PASSED
tests/test_auth.py::TestLogin::test_login_success PASSED
tests/test_auth.py::TestLogin::test_login_wrong_password PASSED
tests/test_auth.py::TestLogin::test_login_unknown_email PASSED
tests/test_auth.py::TestProtectedRoutes::test_get_me_requires_auth PASSED
tests/test_auth.py::TestProtectedRoutes::test_get_me_with_valid_token PASSED
tests/test_auth.py::TestProtectedRoutes::test_get_me_with_invalid_token PASSED
tests/test_auth.py::TestProtectedRoutes::test_update_profile PASSED
tests/test_auth.py::TestProtectedRoutes::test_change_password PASSED
tests/test_auth.py::TestProtectedRoutes::test_change_password_wrong_current PASSED
tests/test_documents.py::TestDocumentUpload::test_upload_pdf_success PASSED
tests/test_documents.py::TestDocumentUpload::test_upload_non_pdf_rejected PASSED
tests/test_documents.py::TestDocumentUpload::test_upload_empty_pdf_rejected PASSED
tests/test_documents.py::TestDocumentUpload::test_upload_unauthenticated PASSED
tests/test_documents.py::TestDocumentManagement::test_list_and_search_documents PASSED
tests/test_documents.py::TestDocumentManagement::test_get_document_by_id PASSED
tests/test_documents.py::TestDocumentManagement::test_user_cannot_access_other_users_document PASSED
tests/test_documents.py::TestDocumentManagement::test_delete_document_success PASSED
tests/test_nlp.py::TestPreprocessor::test_basic_preprocessing PASSED
tests/test_nlp.py::TestPreprocessor::test_empty_text PASSED
tests/test_nlp.py::TestPreprocessor::test_soft_hyphen_removal PASSED
tests/test_nlp.py::TestPreprocessor::test_hyphenated_line_break_fix PASSED
tests/test_nlp.py::TestPreprocessor::test_sentences_minimum_word_count PASSED
tests/test_nlp.py::TestSectionDetector::test_detects_abstract PASSED
tests/test_nlp.py::TestSectionDetector::test_detects_introduction PASSED
tests/test_nlp.py::TestSectionDetector::test_detects_methodology PASSED
tests/test_nlp.py::TestSectionDetector::test_detects_conclusion PASSED
tests/test_nlp.py::TestSectionDetector::test_empty_text PASSED
tests/test_nlp.py::TestSectionDetector::test_sections_in_document_order PASSED
tests/test_nlp.py::TestSectionDetector::test_no_duplicate_section_names PASSED
tests/test_nlp.py::TestSummarizer::test_concise_summary_shorter_than_detailed PASSED
tests/test_nlp.py::TestSummarizer::test_sentences_in_document_order PASSED
tests/test_nlp.py::TestSummarizer::test_summary_not_empty PASSED
tests/test_nlp.py::TestSummarizer::test_single_sentence_input PASSED
tests/test_nlp.py::TestSummarizer::test_empty_sentences PASSED
tests/test_nlp.py::TestSummarizer::test_all_summary_types_returned PASSED
tests/test_nlp.py::TestKeywordExtractor::test_returns_phrases PASSED
tests/test_nlp.py::TestKeywordExtractor::test_max_phrases_respected PASSED
tests/test_nlp.py::TestKeywordExtractor::test_scores_in_range PASSED
tests/test_nlp.py::TestKeywordExtractor::test_ranks_sequential PASSED
tests/test_nlp.py::TestKeywordExtractor::test_no_empty_phrases PASSED
tests/test_nlp.py::TestKeywordExtractor::test_empty_text_returns_empty PASSED
tests/test_nlp.py::TestKeywordExtractor::test_scores_best_first PASSED
tests/test_nlp.py::TestStatistics::test_word_count_positive PASSED
tests/test_nlp.py::TestStatistics::test_summary_word_count PASSED
tests/test_nlp.py::TestStatistics::test_reading_time_positive PASSED
tests/test_nlp.py::TestStatistics::test_ratio_between_0_and_1_for_summary PASSED
tests/test_nlp.py::TestStatistics::test_empty_text PASSED

======================== 64 passed, 6 warnings in 12.08s =======================
```

---

### 2.2 Frontend Vitest Suite Summary
- **Test Runner:** `vitest 2.1.9` + `@testing-library/react` (jsdom, Windows)
- **Total Tests:** 9
- **Passed:** **9 (100%)**
- **Failed:** 0
- **Duration:** 2.39 seconds

```
 ✓ src/test/RegisterPage.test.jsx (3 tests) 253ms
 ✓ src/test/LoginPage.test.jsx (3 tests) 205ms
 ✓ src/test/LandingPage.test.jsx (3 tests) 226ms

 Test Files  3 passed (3)
      Tests  9 passed (9)
   Duration  2.39s
```

---

### 2.3 Production Build Verification
- **Command:** `npm run build`
- **Output:**
```
vite v6.4.3 building for production...
transforming...
✓ 2286 modules transformed.
rendering chunks...
dist/index.html                   1.01 kB │ gzip:   0.54 kB
dist/assets/index-vTCKyE4H.css   32.81 kB │ gzip:   5.80 kB
dist/assets/index-CLyrdyll.js   837.42 kB │ gzip: 248.35 kB
✓ built in 36.78s
```

---

## 3. Quantitative NLP Evaluation Results

Evaluated on 3 ground-truth benchmark academic papers:
1. *Attention Is All You Need* (Vaswani et al., NeurIPS 2017)
2. *TextRank: Bringing Order into Texts* (Mihalcea & Tarau, EMNLP 2004)
3. *BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding* (Devlin et al., NAACL 2019)

### 3.1 Summarization Performance (ROUGE Metrics)
| Metric | Precision | Recall | F1 Score | Description |
|---|---|---|---|---|
| **ROUGE-1** | 0.5495 | 0.6449 | **0.5897** | Unigram lexical overlap with reference summary |
| **ROUGE-2** | 0.4257 | 0.4829 | **0.4495** | Bigram sequence overlap with reference summary |
| **ROUGE-L** | 0.4552 | 0.5189 | **0.4818** | Longest Common Subsequence sentence flow |

### 3.2 Keyphrase Extraction Performance (YAKE)
| Metric | Precision | Recall | F1 Score | Description |
|---|---|---|---|---|
| **Exact Match** | 0.1000 | 0.1250 | **0.1111** | Exact string match with author-defined keyphrases |
| **Soft / Overlap Match** | 0.8333 | 1.0000 | **0.9259** | Semantic token-overlap with author-defined keyphrases |

### 3.3 Latency & Performance Benchmarks
| Pipeline Stage | Mean (ms) | Median (ms) | Min (ms) | Max (ms) | P95 (ms) |
|---|---|---|---|---|---|
| **Preprocessor** | 29.16 | 0.35 | 0.28 | 432.25 | 130.09 |
| **Summarizer (TextRank)** | 2.25 | 2.17 | 1.85 | 3.11 | 3.05 |
| **Keyword Extractor (YAKE)** | 130.58 | 97.49 | 75.12 | 392.77 | 229.13 |
| **Total Pipeline** | **161.99** | **99.65** | **78.00** | **828.04** | **361.44** |

---

## 4. End-to-End Workflow Checklist

| # | Step | Method / Endpoint | Expected Outcome | Actual Result |
|---|---|---|---|---|
| 1 | Register user | `POST /api/auth/register` | Returns 201 Created and user record | **PASS** |
| 2 | Authenticate | `POST /api/auth/login` | Returns 200 OK and JWT access token | **PASS** |
| 3 | Upload paper | `POST /api/documents/upload` | Validates PDF, extracts text, returns metadata | **PASS** |
| 4 | Extract text | PyMuPDF pipeline | Extracts text without losing structure | **PASS** |
| 5 | Generate summary | `POST /api/analyses/text` | Computes concise, medium, detailed summaries | **PASS** |
| 6 | Extract key phrases | YAKE pipeline | Deduplicated, ranked keyphrases with scores | **PASS** |
| 7 | Calculate statistics | Statistics pipeline | Word count, reading time, summary ratio | **PASS** |
| 8 | View in UI | React Dashboard & Analysis | Overview, summary tabs, phrase badges, source view | **PASS** |
| 9 | Search library | `GET /api/documents?search=` | Case-insensitive title filtering | **PASS** |
| 10 | Export results | `GET /api/analyses/{id}/export?format=txt` | Formatted TXT file download | **PASS** |
| 11 | Export PDF | `GET /api/analyses/{id}/export?format=pdf` | Formatted ReportLab PDF download | **PASS** |
| 12 | Isolation check | Cross-user query | Returns 404 for non-owned documents and analyses | **PASS** |
| 13 | Delete document | `DELETE /api/documents/{id}` | Cascades deletion of doc, PDF file, and analyses | **PASS** |
