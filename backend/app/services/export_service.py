"""
app/services/export_service.py
───────────────────────────────
Generate TXT and PDF exports of analysis results.

PDF exports use ReportLab (pure-Python, no external tools required).
TXT exports are plain-text UTF-8.
Includes Stage 1 additions:
- Section-wise intelligent summaries
- Research methodology & findings extraction with verified evidence
"""

import logging
from datetime import datetime, timezone
from io import BytesIO
from typing import Literal

logger = logging.getLogger(__name__)


def generate_txt_export(analysis: dict) -> bytes:
    """
    Generate a formatted plain-text export of an analysis result.

    :param analysis: Analysis document dict from MongoDB.
    :returns: UTF-8 encoded bytes.
    """
    lines: list[str] = []
    sep = "=" * 60

    lines.append(sep)
    lines.append("RESEARCHLENS — ACADEMIC PAPER ANALYSIS REPORT")
    lines.append(sep)
    lines.append(f"Title:            {analysis.get('title', 'Untitled')}")
    lines.append(f"Summary Type:     {analysis.get('summary_type', 'medium').capitalize()}")
    lines.append(f"Analysed On:      {_fmt_dt(analysis.get('created_at'))}")
    lines.append(f"Processing Status:{analysis.get('processing_status', 'unknown').capitalize()}")
    lines.append("")

    # Statistics
    stats = analysis.get("statistics") or {}
    if stats:
        lines.append("─" * 40)
        lines.append("DOCUMENT STATISTICS")
        lines.append("─" * 40)
        lines.append(f"  Words:               {stats.get('word_count', 0):,}")
        lines.append(f"  Characters:          {stats.get('character_count', 0):,}")
        lines.append(f"  Sentences:           {stats.get('sentence_count', 0):,}")
        lines.append(f"  Paragraphs:          {stats.get('paragraph_count', 0):,}")
        lines.append(f"  Est. Reading Time:   {stats.get('estimated_reading_time_minutes', 0):.1f} min")
        lines.append(f"  Summary Words:       {stats.get('summary_word_count', 0):,}")
        lines.append(f"  Summary/Source Ratio:{stats.get('summary_to_source_ratio', 0):.1%}")
        lines.append("")

    # Overall Summary
    lines.append("─" * 40)
    lines.append("OVERALL EXTRACTIVE SUMMARY")
    lines.append("─" * 40)
    lines.append(analysis.get("summary_text") or "(No summary generated)")
    lines.append("")

    # Source-Linked Evidence for Summary Sentences
    evidence_items = analysis.get("summary_sentences_with_evidence") or []
    if evidence_items:
        lines.append("─" * 40)
        lines.append("SUMMARY SENTENCES & EVIDENCE PROVENANCE")
        lines.append("─" * 40)
        for ev in evidence_items:
            sec_name = ev.get("section", "Body")
            score = ev.get("score", 0.0)
            idx = ev.get("index", 0)
            lines.append(f"  [Sentence #{idx + 1} | Section: {sec_name} | Salience: {score:.4f}]")
            lines.append(f'  "{ev.get("text", "")}"')
            lines.append("")

    # Research Methodology & Findings
    meth_findings = analysis.get("methodology_findings") or {}
    dimensions = meth_findings.get("dimensions") or []
    if dimensions:
        lines.append("─" * 40)
        lines.append(f"RESEARCH METHODOLOGY & FINDINGS ({meth_findings.get('total_found', 0)}/{meth_findings.get('total_dimensions', 9)} Extracted)")
        lines.append("─" * 40)
        for d in dimensions:
            status_tag = "FOUND" if d.get("found") else "NOT EXPLICITLY STATED"
            lines.append(f"• {d.get('label', '')} [{status_tag}]:")
            lines.append(f"  Statement: {d.get('summary', '')}")
            if d.get("found") and d.get("evidence"):
                sec_str = f" (Section: {d.get('section')})" if d.get("section") else ""
                lines.append(f'  Verified Excerpt{sec_str}: "{d.get("evidence")}"')
            lines.append("")

    # Section-Wise Intelligent Summaries
    sec_summaries = analysis.get("section_summaries") or []
    lines.append("─" * 40)
    lines.append("SECTION-WISE INTELLIGENT SUMMARIES")
    lines.append("─" * 40)
    if sec_summaries:
        for s in sec_summaries:
            lines.append(f"▶ Section: {s.get('name', 'Untitled')} ({s.get('word_count', 0)} words)")
            lines.append(f"  {s.get('summary_text') or '(No section summary)'}")
            lines.append("")
    else:
        lines.append("  (No discrete section headings detected; overall summary provided above.)")
        lines.append("")

    # Key phrases
    phrases = analysis.get("key_phrases") or []
    if phrases:
        lines.append("─" * 40)
        lines.append("KEY PHRASES (YAKE)")
        lines.append("(Scores are algorithmic relevance estimates, not verified importance)")
        lines.append("─" * 40)
        for p in phrases:
            lines.append(f"  {p.get('rank', '?'):>2}. {p.get('phrase', '')}  (score: {p.get('score', 0):.4f})")
        lines.append("")

    # Warnings
    warnings = analysis.get("warnings") or []
    if warnings:
        lines.append("─" * 40)
        lines.append("PROCESSING NOTES")
        lines.append("─" * 40)
        for w in warnings:
            lines.append(f"  ⚠  {w}")
        lines.append("")

    lines.append(sep)
    lines.append("Note: This report was generated by an automated NLP system.")
    lines.append("Summaries, methodology extractions, and key phrases are machine-generated.")
    lines.append("Please review the original document before citing results.")
    lines.append(sep)

    return "\n".join(lines).encode("utf-8")


def generate_pdf_export(analysis: dict) -> bytes:
    """
    Generate a PDF export using ReportLab.

    :param analysis: Analysis document dict.
    :returns: PDF bytes.
    :raises ImportError: If ReportLab is not installed.
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            HRFlowable,
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )
    except ImportError:
        raise ImportError(
            "ReportLab is required for PDF export. "
            "Install it with: pip install reportlab"
        )

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.8 * cm,
        leftMargin=1.8 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
    )

    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        fontSize=15,
        spaceAfter=6,
        textColor=colors.HexColor("#1e1b4b"),
    )
    story.append(Paragraph("ResearchLens — Academic Paper Analysis Report", title_style))
    story.append(Spacer(1, 0.2 * cm))

    # Metadata table
    meta_data = [
        ["Title", analysis.get("title", "Untitled")],
        ["Summary Type", analysis.get("summary_type", "medium").capitalize()],
        ["Analysed On", _fmt_dt(analysis.get("created_at"))],
        ["Processing Status", analysis.get("processing_status", "").capitalize()],
    ]
    meta_table = Table(meta_data, colWidths=[4 * cm, 12 * cm])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e0e7ff")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (1, 0), (1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("PADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 0.4 * cm))

    # Statistics
    stats = analysis.get("statistics") or {}
    if stats:
        story.append(Paragraph("Document Statistics", styles["Heading2"]))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#94a3b8")))
        stat_rows = [
            ["Words", f"{stats.get('word_count', 0):,}",
             "Sentences", f"{stats.get('sentence_count', 0):,}"],
            ["Characters", f"{stats.get('character_count', 0):,}",
             "Paragraphs", f"{stats.get('paragraph_count', 0):,}"],
            ["Reading Time", f"{stats.get('estimated_reading_time_minutes', 0):.1f} min",
             "Summary Words", f"{stats.get('summary_word_count', 0):,}"],
        ]
        stat_table = Table(stat_rows, colWidths=[4 * cm, 4 * cm, 4 * cm, 4 * cm])
        stat_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("PADDING", (0, 0), (-1, -1), 3.5),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ]))
        story.append(stat_table)
        story.append(Spacer(1, 0.4 * cm))

    # Overall Summary
    summary_text = analysis.get("summary_text") or "(No summary generated)"
    story.append(Paragraph("Overall Extractive Summary", styles["Heading2"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#94a3b8")))
    story.append(Paragraph(summary_text, styles["BodyText"]))
    story.append(Spacer(1, 0.4 * cm))

    # Methodology & Findings
    meth_findings = analysis.get("methodology_findings") or {}
    dims = meth_findings.get("dimensions") or []
    if dims:
        story.append(Paragraph(
            f"Methodology & Findings ({meth_findings.get('total_found', 0)}/{meth_findings.get('total_dimensions', 9)} Identified)",
            styles["Heading2"],
        ))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#94a3b8")))
        meth_rows = [["Dimension", "Status", "Extracted Statement / Evidence"]]
        for d in dims:
            status_text = "Found" if d.get("found") else "Not Stated"
            summary_p = d.get("summary", "")
            if d.get("found") and d.get("section"):
                summary_p += f" [Source: {d.get('section')}]"
            meth_rows.append([
                d.get("label", ""),
                status_text,
                Paragraph(summary_p, styles["Normal"]),
            ])
        meth_table = Table(meth_rows, colWidths=[4.2 * cm, 2.2 * cm, 9.6 * cm])
        meth_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4338ca")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("PADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(meth_table)
        story.append(Spacer(1, 0.4 * cm))

    # Section-Wise Summaries
    sec_summaries = analysis.get("section_summaries") or []
    if sec_summaries:
        story.append(Paragraph("Section-Wise Intelligent Summaries", styles["Heading2"]))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#94a3b8")))
        for s in sec_summaries:
            sec_heading = f"<b>{s.get('name', '')}</b> ({s.get('word_count', 0)} words)"
            story.append(Paragraph(sec_heading, styles["Normal"]))
            story.append(Paragraph(s.get("summary_text", ""), styles["BodyText"]))
            story.append(Spacer(1, 0.2 * cm))
        story.append(Spacer(1, 0.3 * cm))

    # Key phrases
    phrases = analysis.get("key_phrases") or []
    if phrases:
        story.append(Paragraph("Key Phrases (YAKE)", styles["Heading2"]))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#94a3b8")))
        note = ParagraphStyle("SmallNote", parent=styles["Normal"], fontSize=7, textColor=colors.grey)
        story.append(Paragraph(
            "Scores are algorithmic relevance estimates — not verified measures of importance.",
            note,
        ))
        story.append(Spacer(1, 0.15 * cm))

        phrase_rows = [["#", "Phrase", "Score"]] + [
            [str(p.get("rank", "")), p.get("phrase", ""), f"{p.get('score', 0):.4f}"]
            for p in phrases[:15]
        ]
        phrase_table = Table(phrase_rows, colWidths=[1 * cm, 12 * cm, 3 * cm])
        phrase_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#312e81")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("PADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(phrase_table)
        story.append(Spacer(1, 0.4 * cm))

    # Footer disclaimer
    disclaimer = ParagraphStyle(
        "Disclaimer", parent=styles["Normal"], fontSize=7,
        textColor=colors.grey, borderPad=4,
    )
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Spacer(1, 0.15 * cm))
    story.append(Paragraph(
        "Responsible Academic AI Disclosure: This report was generated by automated extractive algorithms. "
        "Summaries, methodology dimensions, and key phrases are machine-generated estimates. "
        "Always review the original publication before citation.",
        disclaimer,
    ))

    doc.build(story)
    return buffer.getvalue()


# ── Helper ────────────────────────────────────────────────────────────────────

def _fmt_dt(dt) -> str:
    if dt is None:
        return "—"
    if isinstance(dt, datetime):
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    return str(dt)
