# System Architecture

## Architecture Diagram

```mermaid
graph TB
    subgraph Frontend["Frontend (React + Vite)"]
        UI[Pages & Components]
        AuthCtx[AuthContext]
        ApiSvc[Axios API Service]
    end

    subgraph Backend["Backend (FastAPI + Python 3.12)"]
        Auth[Auth Routes]
        Docs[Document Routes]
        Ana[Analysis Routes]
        
        subgraph Services["Service Layer"]
            AuthSvc[Auth Service]
            DocSvc[Document Service]
            AnaSvc[Analysis Service]
            ExportSvc[Export Service]
        end

        subgraph NLP["NLP Pipeline"]
            Ext[PDF Extractor\nPyMuPDF]
            Pre[Preprocessor\nNLTK]
            Sec[Section Detector\nRegex Heuristics]
            Sum[Summarizer\nTextRank TF-IDF]
            KW[Keyword Extractor\nYAKE]
            Stat[Statistics]
        end

        Core[Core: Security\nJWT + bcrypt]
        Config[Config\npydantic-settings]
    end

    subgraph Storage["Data Layer"]
        MongoDB[(MongoDB)]
        Files[Local File Storage\n/storage UUID.pdf]
    end

    UI --> AuthCtx
    UI --> ApiSvc
    ApiSvc --> |HTTP REST + JWT| Auth
    ApiSvc --> Docs
    ApiSvc --> Ana

    Auth --> AuthSvc --> Core
    Docs --> DocSvc
    Ana --> AnaSvc

    DocSvc --> Ext
    AnaSvc --> Pre --> Sec
    Pre --> Sum
    Pre --> KW
    Pre --> Stat

    DocSvc --> Files
    AuthSvc --> MongoDB
    DocSvc --> MongoDB
    AnaSvc --> MongoDB
    ExportSvc --> MongoDB
```

## Component Responsibilities

| Component | Responsibility |
|-----------|---------------|
| **React Pages** | UI rendering, user input, navigation |
| **AuthContext** | JWT storage, token validation on startup |
| **Axios Service** | Token injection, 401 handling, typed API helpers |
| **FastAPI Routes** | HTTP endpoint definitions, request validation |
| **Auth Service** | Registration, login, password hashing, JWT creation |
| **Document Service** | File validation, UUID storage, PDF text extraction |
| **Analysis Service** | NLP pipeline orchestration, MongoDB persistence |
| **Export Service** | TXT/PDF report generation |
| **NLP: Extractor** | PyMuPDF PDF text extraction, quality detection |
| **NLP: Preprocessor** | Normalisation, sentence/paragraph splitting |
| **NLP: Section Detector** | Regex-based heading detection |
| **NLP: Summarizer** | TextRank PageRank + TF-IDF extractive summarisation |
| **NLP: Keyword Extractor** | YAKE phrase ranking + deduplication |
| **NLP: Statistics** | Word/sentence/reading-time calculation |
| **MongoDB** | User profiles, document metadata, analysis results |
| **File Storage** | Uploaded PDFs stored with opaque UUID filenames |

## Processing Workflow

```mermaid
sequenceDiagram
    actor User
    participant Frontend
    participant FastAPI
    participant NLP
    participant MongoDB
    participant Storage

    User->>Frontend: Upload PDF + set title + summary type
    Frontend->>FastAPI: POST /api/documents/upload
    FastAPI->>Storage: Save PDF as UUID.pdf
    FastAPI->>NLP: extract_text_from_pdf()
    NLP-->>FastAPI: text, page_count, status, warnings
    FastAPI->>MongoDB: Insert document record
    FastAPI-->>Frontend: document_id + extraction_status

    Frontend->>FastAPI: POST /api/documents/{id}/analyze
    FastAPI->>MongoDB: Fetch extracted_text
    FastAPI->>NLP: preprocess() → detect_sections()
    FastAPI->>NLP: summarize() → extract_key_phrases()
    FastAPI->>NLP: compute_statistics()
    FastAPI->>MongoDB: Insert analysis record
    FastAPI-->>Frontend: analysis_id + full results

    Frontend->>User: Display tabs: Summary, Phrases, Sections, Stats
```

## Security Design

- **Passwords**: bcrypt via passlib (never stored in plaintext)
- **Auth**: JWT Bearer tokens, validated on every protected route
- **Ownership**: Every document/analysis query includes `user_id` filter
- **File storage**: Opaque UUID filenames; storage paths never returned to clients
- **Input validation**: Pydantic schemas on all endpoints
- **CORS**: Restricted to configured origins
- **Error messages**: Generic for auth failures (no email enumeration)
