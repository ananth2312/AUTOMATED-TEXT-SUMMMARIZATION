# API Documentation

## Base URL
- Development: `http://localhost:8000/api`
- Interactive Docs: `http://localhost:8000/docs` (Swagger UI)
- ReDoc: `http://localhost:8000/redoc`

## Authentication
All protected endpoints require a `Bearer` JWT token in the `Authorization` header.

```
Authorization: Bearer <access_token>
```

---

## Endpoints

### System

#### `GET /api/health`
Health check. No authentication required.

**Response 200:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "database": "connected"
}
```

---

### Authentication

#### `POST /api/auth/register`
Create a new user account.

**Request:**
```json
{
  "name": "Jane Smith",
  "email": "jane@university.edu",
  "password": "Secure123"
}
```

**Response 201:**
```json
{
  "_id": "6748abc123...",
  "name": "Jane Smith",
  "email": "jane@university.edu",
  "created_at": "2026-10-01T12:00:00Z"
}
```

**Errors:** `409` duplicate email · `422` validation failed

---

#### `POST /api/auth/login`
Authenticate and receive a JWT.

**Request:** `{ "email": "...", "password": "..." }`

**Response 200:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Errors:** `401` invalid credentials

---

#### `GET /api/auth/me` 🔒
Return the current user's profile.

#### `PATCH /api/auth/profile` 🔒
Update name. Body: `{ "name": "New Name" }`

#### `POST /api/auth/change-password` 🔒
Body: `{ "current_password": "...", "new_password": "..." }`

---

### Documents

#### `POST /api/documents/upload` 🔒
Upload a PDF (multipart/form-data).

**Form fields:**
- `file` — PDF file (max 20 MB)
- `title` — Document title (string)

**Response 201:** DocumentMetadata object including `extraction_status`.

**Errors:** `413` too large · `415` wrong format · `422` validation

---

#### `GET /api/documents` 🔒
List user's documents. Query: `?page=1&page_size=20&search=...`

#### `GET /api/documents/{id}` 🔒
Get single document metadata.

#### `DELETE /api/documents/{id}` 🔒
Delete document, its file, and all analyses. Returns:
```json
{ "deleted": true, "document_id": "...", "analyses_deleted": 2 }
```

---

### Analyses

#### `POST /api/analyses/text` 🔒
Analyse directly pasted text.

**Request:**
```json
{
  "title": "My Paper",
  "text": "Abstract. This paper presents...",
  "summary_type": "medium"
}
```

`summary_type`: `"concise"` | `"medium"` | `"detailed"`

**Response 201:** Full AnalysisResult object.

---

#### `POST /api/documents/{id}/analyze` 🔒
Run analysis on an uploaded document.

**Request:** `{ "summary_type": "medium" }`

**Response 201:** Full AnalysisResult.

---

#### `GET /api/analyses` 🔒
List user analyses. Query: `?page=1&page_size=20`

#### `GET /api/analyses/{id}` 🔒
Get full analysis result (all three summary levels, key phrases, sections, statistics).

---

#### `GET /api/analyses/{id}/export` 🔒
Download analysis as TXT or PDF.

Query: `?format=txt` or `?format=pdf`

Returns file download with appropriate Content-Disposition header.

---

#### `GET /api/dashboard` 🔒
Dashboard statistics for the current user.

**Response:**
```json
{
  "total_documents": 12,
  "total_analyses": 18,
  "total_words_processed": 145000,
  "recent_analyses": [...],
  "analyses_by_day": [
    { "date": "2026-09-28", "count": 3 }
  ]
}
```

---

## Response Schema: AnalysisResult

```json
{
  "_id": "...",
  "user_id": "...",
  "document_id": "...",
  "title": "Paper Title",
  "summary_type": "medium",
  "summary_text": "Selected sentences from source...",
  "concise_summary": "...",
  "medium_summary": "...",
  "detailed_summary": "...",
  "key_phrases": [
    { "phrase": "machine learning", "score": 0.9821, "rank": 1 }
  ],
  "detected_sections": [
    { "name": "Abstract", "start_char": 0, "end_char": 850, "word_count": 120, "content_preview": "..." }
  ],
  "statistics": {
    "word_count": 5420,
    "character_count": 34100,
    "sentence_count": 187,
    "paragraph_count": 42,
    "estimated_reading_time_minutes": 27.1,
    "summary_word_count": 342,
    "summary_to_source_ratio": 0.063,
    "words_per_minute_assumption": 200
  },
  "processing_status": "success",
  "warnings": [],
  "algorithm_versions": {
    "preprocessor": "1.0",
    "summarizer": "textrank-tfidf-1.0",
    "keyword_extractor": "yake-1.0",
    "section_detector": "regex-heuristic-1.0"
  },
  "source_text_preview": "First 500 chars...",
  "created_at": "2026-10-01T12:00:00Z"
}
```

> **Note on key phrase scores:** Scores (0-1) are algorithmic relevance estimates from the YAKE algorithm. 1.0 = top-ranked phrase. These are machine-estimated rankings, not scientifically verified measures of importance.
