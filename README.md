# ResearchLens — Academic Research Paper Summarizer & Analysis Tool

> **Final-Year Project** — Automated Text Summarization and Key-Phrase Extraction Tool for Academic Research Papers  
> **Status:** Production-Ready Stage 1 Complete & Verified (74/74 Backend Tests Passed, 12/12 Frontend Tests Passed)

---

## Overview

**ResearchLens** is a full-stack, local-first academic research assistant that ingests scientific research papers in PDF format or raw text, cleans and preprocesses academic text, heuristically detects paper sections, generates multi-length extractive summaries via **TextRank**, extracts and ranks domain-specific key phrases via **YAKE**, generates section-wise intelligent summaries, extracts structured methodology & findings across 9 academic dimensions with verified source evidence, and provides comprehensive document statistics with export capabilities (TXT and publication-grade PDF via ReportLab).

The entire system runs natively on **Windows (PowerShell)** without requiring GPU hardware, paid third-party APIs, or Docker containerization.

---

## Key Features

1. **Authentication & Security:** Secure registration, login, and profile management using direct **bcrypt** hashing and signed **JWT** access tokens with strict per-user data isolation.
2. **Flexible Document Ingestion:** Drag-and-drop PDF upload (up to 20 MB) with PyMuPDF text and metadata extraction, or direct text pasting.
3. **Robust Preprocessing:** Soft-hyphen removal, line-break hyphenation repair, whitespace normalization, and repeated header/footer suppression.
4. **Academic Section Detection:** Standalone line and inline run-in identification of common headings (*Abstract*, *Introduction*, *Methodology*, *Results*, *Discussion*, *Conclusion*, *References*) and document offsets.
5. **Multi-Length Extractive Summarization:** Custom PageRank-based TextRank algorithm generating **Concise** (top ~15%), **Medium** (top ~30%), and **Detailed** (top ~50%) verbatim summaries in document order.
6. **Source-Linked Summary Evidence:** Interactive sentence-by-sentence evidence provenance tracking original sentence index, character spans, enclosing section, and TextRank salience score.
7. **Section-Wise Intelligent Summaries:** Targeted extractive summaries generated individually for each detected section to accelerate focused reading.
8. **Research Methodology & Findings Extractor:** Evidence-based extraction of 9 academic dimensions (*Research Problem*, *Objectives*, *Methodology*, *Datasets*, *Tools/Hardware*, *Evaluation Metrics*, *Main Findings*, *Limitations*, *Future Work*) with verbatim quotes and honest "not explicitly stated" fallbacks.
9. **Ranked Key-Phrase Extraction:** Unsupervised YAKE keyphrase extractor scoring 1- to 3-gram candidate phrases with token-overlap deduplication.
10. **Document & Analysis Statistics:** Source word/character/sentence/paragraph counts, estimated reading time, summary word count, and compression ratio.
11. **Personal Research Library:** Searchable, paginated, and sortable history of user-analyzed documents with cascade deletion.
12. **One-Click Comprehensive Export:** Download comprehensive structured reports in plain text (TXT) or publication-ready formatted PDF containing executive summaries, findings matrix, section summaries, and keyphrases.
13. **Responsible AI Disclosure:** Clear UI badges reminding researchers that output is machine-generated and grounded in source text.

---

## Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 19, Vite 6, Tailwind CSS 3, React Router 7, Axios, Lucide React, Recharts |
| **Backend** | Python 3.12, FastAPI, Pydantic v2, Uvicorn, PyMongo, bcrypt, python-jose |
| **NLP Engine** | PyMuPDF (fitz), NLTK (Punkt), TextRank (TF-IDF + PageRank), YAKE |
| **Database** | MongoDB Community Server (local Windows service on port 27017) |
| **Document Export** | ReportLab (vector PDF generation) & plain text |
| **Testing** | pytest & pytest-asyncio (Backend), Vitest & React Testing Library (Frontend) |

---

## Quick Start on Windows PowerShell

### Prerequisites
- Python 3.11 or 3.12 installed (`python --version`)
- Node.js v18+ installed (`node -v`)
- MongoDB Community Server installed and running as a Windows service

Verify MongoDB status:
```powershell
Get-Service MongoDB
# If Stopped: Start-Service MongoDB
```

---

### 1. Backend Setup & Startup
In Windows PowerShell (Window 1):
```powershell
cd d:\S7_Project(New)\academic-research-summarizer\backend

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run backend test suite (74 automated tests)
pytest -v

# Start FastAPI backend server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- API Base: `http://localhost:8000/api`
- Interactive OpenAPI Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/api/health`

---

### 2. Frontend Setup & Startup
In Windows PowerShell (Window 2):
```powershell
cd d:\S7_Project(New)\academic-research-summarizer\frontend

# Install dependencies
npm install

# Run frontend test suite (12 automated tests)
npm test

# Build for production (verifies bundling)
npm run build

# Start Vite development server
npm run dev
```
- Web Application URL: `http://localhost:5173`

---

## Verified Evaluation & Quality Metrics

Evaluated across peer-reviewed landmark papers (*Attention Is All You Need*, *TextRank*, *BERT*):

### Summarization Accuracy (ROUGE Metrics)
- **ROUGE-1 F1:** **0.5897** (Recall: 0.6449, Precision: 0.5495)
- **ROUGE-2 F1:** **0.4495** (Recall: 0.4829, Precision: 0.4257)
- **ROUGE-L F1:** **0.4818** (Recall: 0.5189, Precision: 0.4552)

### Keyphrase Extraction Accuracy (YAKE)
- **Soft / Token-Overlap Match F1:** **0.9259** (Recall: 1.0000, Precision: 0.8333)
- **Exact Match F1:** 0.1111

### Latency Benchmarks (Local Windows Execution)
- **TextRank Summarization:** **2.17 ms** median
- **YAKE Keyphrase Extraction:** **97.49 ms** median
- **Total Pipeline Execution:** **99.65 ms** median (P95: 361.44 ms)

---

## Comprehensive Project Documentation

Detailed project documentation is available in the `docs/` folder:
- [SRS.md](file:///d:/S7_Project(New)/academic-research-summarizer/docs/SRS.md) — Complete Software Requirements Specification
- [ARCHITECTURE.md](file:///d:/S7_Project(New)/academic-research-summarizer/docs/ARCHITECTURE.md) — System Architecture, Component Details, and Mermaid Diagrams
- [API.md](file:///d:/S7_Project(New)/academic-research-summarizer/docs/API.md) — RESTful API Endpoint Reference with request/response schemas
- [TESTING.md](file:///d:/S7_Project(New)/academic-research-summarizer/docs/TESTING.md) — Testing Strategy, Verified Test Results (73 tests passed), and E2E Checklist
- [USER_GUIDE.md](file:///d:/S7_Project(New)/academic-research-summarizer/docs/USER_GUIDE.md) — Step-by-Step User & Windows Setup Guide with Troubleshooting
- [FINAL_PROJECT_REPORT.md](file:///d:/S7_Project(New)/academic-research-summarizer/docs/FINAL_PROJECT_REPORT.md) — Comprehensive 24-Section Academic Final-Year Project Report
- [evaluation_summary.md](file:///d:/S7_Project(New)/academic-research-summarizer/evaluation/results/evaluation_summary.md) — Quantitative NLP Benchmarks & Latency Measurements

---

## License & Responsible Use

> **Academic AI Disclosure:** All summaries and key phrases generated by ResearchLens are produced by unsupervised extractive algorithms. They are computational aids designed to accelerate literature reviews and must be verified against original sources before scientific citation.
