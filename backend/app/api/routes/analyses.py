"""
app/api/routes/analyses.py
───────────────────────────
Analysis endpoints:
  POST /api/analyses/text                         – analyse pasted text
  POST /api/documents/{document_id}/analyze       – analyse uploaded PDF
  GET  /api/analyses                              – list user analyses
  GET  /api/analyses/{analysis_id}                – get one analysis
  GET  /api/analyses/{analysis_id}/export         – download TXT or PDF
  GET  /api/dashboard                             – dashboard statistics
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from pymongo.database import Database

from app.core.dependencies import CurrentUser, get_db
from app.schemas import (
    AnalysisListResponse,
    AnalysisResult,
    AnalyzeDocumentRequest,
    DashboardStats,
    TextInputRequest,
)
from app.services import (
    generate_pdf_export,
    generate_txt_export,
    get_extracted_text,
    run_analysis,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Analyses"])


# ── Analyse pasted text ───────────────────────────────────────────────────────

@router.post(
    "/analyses/text",
    status_code=status.HTTP_201_CREATED,
    summary="Analyse directly pasted academic text",
)
def analyse_text(
    body: TextInputRequest,
    current_user: CurrentUser = None,
    db: Database = Depends(get_db),
):
    user_id = str(current_user["_id"])
    try:
        result = run_analysis(
            db=db,
            user_id=user_id,
            title=body.title,
            raw_text=body.text,
            summary_type=body.summary_type,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return _serialise_analysis(result)


# ── Analyse uploaded document ─────────────────────────────────────────────────

@router.post(
    "/documents/{document_id}/analyze",
    status_code=status.HTTP_201_CREATED,
    summary="Run NLP analysis on an uploaded document",
)
def analyse_document(
    document_id: str,
    body: AnalyzeDocumentRequest,
    current_user: CurrentUser = None,
    db: Database = Depends(get_db),
):
    user_id = str(current_user["_id"])

    # Verify ownership and get title
    try:
        oid = ObjectId(document_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Document not found.")
    doc = db.documents.find_one({"_id": oid, "user_id": ObjectId(user_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    raw_text = get_extracted_text(db, document_id=document_id, user_id=user_id)
    warnings = list(doc.get("extraction_warnings") or [])

    try:
        result = run_analysis(
            db=db,
            user_id=user_id,
            title=doc.get("title", "Untitled"),
            raw_text=raw_text,
            summary_type=body.summary_type,
            document_id=document_id,
            existing_warnings=warnings,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return _serialise_analysis(result)


# ── List analyses ─────────────────────────────────────────────────────────────

@router.get(
    "/analyses",
    response_model=AnalysisListResponse,
    summary="List the current user's analyses (paginated)",
)
def list_analyses(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: CurrentUser = None,
    db: Database = Depends(get_db),
):
    user_id = str(current_user["_id"])
    query = {"user_id": ObjectId(user_id)}
    total = db.analyses.count_documents(query)
    skip = (page - 1) * page_size
    projection = {
        "_id": 1, "document_id": 1, "title": 1,
        "summary_type": 1, "processing_status": 1,
        "statistics": 1, "created_at": 1,
    }
    cursor = (
        db.analyses.find(query, projection)
        .sort("created_at", -1)
        .skip(skip)
        .limit(page_size)
    )
    items = []
    for a in cursor:
        stats = a.get("statistics") or {}
        items.append({
            "_id": str(a["_id"]),
            "document_id": str(a["document_id"]) if a.get("document_id") else None,
            "title": a.get("title", ""),
            "summary_type": a.get("summary_type", "medium"),
            "processing_status": a.get("processing_status", ""),
            "word_count": stats.get("word_count", 0),
            "created_at": a.get("created_at"),
        })
    return {"items": items, "total": total, "page": page, "page_size": page_size}


# ── Get single analysis ───────────────────────────────────────────────────────

@router.get(
    "/analyses/{analysis_id}",
    summary="Get a full analysis result by ID",
)
def get_analysis(
    analysis_id: str,
    current_user: CurrentUser = None,
    db: Database = Depends(get_db),
):
    user_id = str(current_user["_id"])
    try:
        oid = ObjectId(analysis_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Analysis not found.")

    a = db.analyses.find_one({"_id": oid, "user_id": ObjectId(user_id)})
    if not a:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    return _serialise_analysis(a)


# ── Export ────────────────────────────────────────────────────────────────────

@router.get(
    "/analyses/{analysis_id}/export",
    summary="Export an analysis as TXT or PDF",
)
def export_analysis(
    analysis_id: str,
    format: str = Query("txt", pattern="^(txt|pdf)$", description="Export format: txt or pdf"),
    current_user: CurrentUser = None,
    db: Database = Depends(get_db),
):
    user_id = str(current_user["_id"])
    try:
        oid = ObjectId(analysis_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Analysis not found.")

    a = db.analyses.find_one({"_id": oid, "user_id": ObjectId(user_id)})
    if not a:
        raise HTTPException(status_code=404, detail="Analysis not found.")

    safe_title = "".join(c if c.isalnum() or c in " _-" else "_" for c in a.get("title", "analysis"))[:50]
    filename = f"{safe_title}.{format}"

    if format == "pdf":
        try:
            content = generate_pdf_export(a)
        except ImportError as exc:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail=str(exc),
            )
        return Response(
            content=content,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    else:
        content = generate_txt_export(a)
        return Response(
            content=content,
            media_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )


# ── Dashboard stats ───────────────────────────────────────────────────────────

@router.get(
    "/dashboard",
    summary="Dashboard statistics for the current user",
)
def dashboard_stats(
    current_user: CurrentUser = None,
    db: Database = Depends(get_db),
):
    user_id = str(current_user["_id"])
    uid_oid = ObjectId(user_id)

    total_documents = db.documents.count_documents({"user_id": uid_oid})
    total_analyses = db.analyses.count_documents({"user_id": uid_oid})

    # Sum up words processed
    pipeline = [
        {"$match": {"user_id": uid_oid}},
        {"$group": {"_id": None, "total_words": {"$sum": "$statistics.word_count"}}},
    ]
    agg = list(db.analyses.aggregate(pipeline))
    total_words = agg[0]["total_words"] if agg else 0

    # Recent analyses (last 5)
    recent_cursor = (
        db.analyses.find(
            {"user_id": uid_oid},
            {"_id": 1, "document_id": 1, "title": 1, "summary_type": 1,
             "processing_status": 1, "statistics": 1, "created_at": 1},
        )
        .sort("created_at", -1)
        .limit(5)
    )
    recent = []
    for a in recent_cursor:
        stats = a.get("statistics") or {}
        recent.append({
            "_id": str(a["_id"]),
            "document_id": str(a["document_id"]) if a.get("document_id") else None,
            "title": a.get("title", ""),
            "summary_type": a.get("summary_type", "medium"),
            "processing_status": a.get("processing_status", ""),
            "word_count": stats.get("word_count", 0),
            "created_at": a.get("created_at"),
        })

    # Analyses per day (last 30 days)
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    day_pipeline = [
        {"$match": {"user_id": uid_oid, "created_at": {"$gte": thirty_days_ago}}},
        {
            "$group": {
                "_id": {
                    "year": {"$year": "$created_at"},
                    "month": {"$month": "$created_at"},
                    "day": {"$dayOfMonth": "$created_at"},
                },
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"_id.year": 1, "_id.month": 1, "_id.day": 1}},
    ]
    day_agg = list(db.analyses.aggregate(day_pipeline))
    analyses_by_day = [
        {
            "date": f"{r['_id']['year']}-{r['_id']['month']:02d}-{r['_id']['day']:02d}",
            "count": r["count"],
        }
        for r in day_agg
    ]

    return {
        "total_documents": total_documents,
        "total_analyses": total_analyses,
        "total_words_processed": total_words,
        "recent_analyses": recent,
        "analyses_by_day": analyses_by_day,
    }


# ── Internal serialiser ───────────────────────────────────────────────────────

def _serialise_analysis(a: dict) -> dict:
    """Convert ObjectIds to strings for JSON serialisation."""
    a = dict(a)
    a["_id"] = str(a.get("_id", ""))
    a["user_id"] = str(a.get("user_id", ""))
    if a.get("document_id"):
        a["document_id"] = str(a["document_id"])
    return a
