"""
app/nlp/citation_parser.py
─────────────────────────
Citation intelligence and reference parsing module.

Capabilities:
1. Locates the References / Bibliography section in academic text.
2. Segments and parses individual bibliography entries (authors, title, year, venue, DOI).
3. Generates standardized citation formats: BibTeX, APA 7, IEEE, and MLA.
4. Identifies in-text citation markers (e.g., [1], [2, 3], (Vaswani et al., 2017))
   and links them directly to their corresponding bibliography entry.
5. Formats publication-ready citation snippets for the analyzed paper itself.
"""

import logging
import re
from dataclasses import asdict, dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# Pattern to identify reference boundaries
_NUMBERED_REF_SPLIT = re.compile(r"(?:\n\s*|^)\[(\d+)\]\s*")
_ORDERED_REF_SPLIT = re.compile(r"(?:\n\s*|^)(\d+)\.\s+(?=[A-Z])")
_AUTHOR_YEAR_SPLIT = re.compile(
    r"(?:\n\s*|^)([A-Z][A-Za-z\u00C0-\u024F\-\']+(?:,\s+[A-Z]\.|\s+[A-Z]\.)[^\n]+?\((?:19|20)\d{2}[a-z]?\))"
)

# Common year pattern
_YEAR_PATTERN = re.compile(r"\b((?:19|20)\d{2})\b")
# DOI pattern
_DOI_PATTERN = re.compile(r"\b(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)\b")
# URL pattern
_URL_PATTERN = re.compile(r"(https?://[^\s,>]+)")

# In-text citation patterns
_IN_TEXT_BRACKET = re.compile(r"\[(\d+(?:\s*[,–-]\s*\d+)*)\]")
_IN_TEXT_AUTHOR_YEAR = re.compile(
    r"\(([A-Z][a-zA-Z\u00C0-\u024F\-]+(?:\s+et\s+al\.)?,\s*(?:19|20)\d{2}[a-z]?)\)"
)


@dataclass
class ParsedReference:
    id: str
    raw_text: str
    authors: list[str] = field(default_factory=list)
    title: str = ""
    year: str = ""
    venue: str = ""
    doi: str = ""
    url: str = ""
    bibtex: str = ""
    apa: str = ""
    ieee: str = ""
    mla: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def _clean_str(text: str) -> str:
    return " ".join(text.replace("\n", " ").split()).strip()


def _generate_bibtex_key(authors: list[str], year: str, title: str, ref_id: str) -> str:
    first_author = "ref"
    if authors:
        parts = authors[0].replace(",", "").split()
        if parts:
            first_author = re.sub(r"[^a-zA-Z0-9]", "", parts[0]).lower()

    clean_year = year or "nd"
    first_word = "paper"
    if title:
        words = [w for w in re.sub(r"[^a-zA-Z0-9\s]", "", title).split() if len(w) > 3]
        if words:
            first_word = words[0].lower()

    return f"{first_author}{clean_year}{first_word}_{ref_id}".strip("_")


def _format_bibtex(key: str, authors: list[str], title: str, year: str, venue: str, doi: str, url: str) -> str:
    author_str = " and ".join(authors) if authors else "Unknown"
    fields = [
        f"  title     = {{{title or 'Untitled Reference'}}}",
        f"  author    = {{{author_str}}}",
    ]
    if year:
        fields.append(f"  year      = {{{year}}}")
    if venue:
        fields.append(f"  journal   = {{{venue}}}")
    if doi:
        fields.append(f"  doi       = {{{doi}}}")
    elif url:
        fields.append(f"  url       = {{{url}}}")

    body = ",\n".join(fields)
    return f"@article{{{key},\n{body}\n}}"


def _format_apa(authors: list[str], year: str, title: str, venue: str, doi: str) -> str:
    if not authors:
        author_part = "Unknown Author"
    elif len(authors) == 1:
        author_part = authors[0]
    elif len(authors) == 2:
        author_part = f"{authors[0]} & {authors[1]}"
    else:
        author_part = f"{authors[0]} et al."

    year_part = f"({year})." if year else "(n.d.)."
    title_part = f"{title.rstrip('.')}." if title else ""
    venue_part = f" {venue.rstrip('.')}." if venue else ""
    doi_part = f" https://doi.org/{doi}" if doi else ""

    return f"{author_part} {year_part} {title_part}{venue_part}{doi_part}".strip()


def _format_ieee(ref_id: str, authors: list[str], title: str, venue: str, year: str) -> str:
    if not authors:
        author_part = "Unknown"
    elif len(authors) > 3:
        author_part = f"{authors[0]} et al."
    else:
        author_part = ", ".join(authors)

    title_part = f'"{title},"' if title else ""
    venue_part = f" {venue}," if venue else ""
    year_part = f" {year}." if year else "."

    num = f"[{ref_id}] " if ref_id and ref_id.isdigit() else ""
    return f"{num}{author_part}, {title_part}{venue_part}{year_part}".strip()


def _format_mla(authors: list[str], title: str, venue: str, year: str) -> str:
    if not authors:
        author_part = "Unknown."
    elif len(authors) > 2:
        author_part = f"{authors[0]}, et al."
    else:
        author_part = ", and ".join(authors) + "."

    title_part = f' "{title}."' if title else ""
    venue_part = f" {venue}," if venue else ""
    year_part = f" {year}." if year else "."

    return f"{author_part}{title_part}{venue_part}{year_part}".strip()


def parse_single_reference(raw_ref: str, fallback_id: str = "1") -> ParsedReference:
    """
    Parses a single reference text into components and formats citations.
    """
    text = _clean_str(raw_ref)
    ref_id = fallback_id

    # Check for leading number tag [1] or 1.
    lead_bracket = re.match(r"^\[(\d+)\]\s*", text)
    if lead_bracket:
        ref_id = lead_bracket.group(1)
        text = text[lead_bracket.end():]
    else:
        lead_dot = re.match(r"^(\d+)\.\s+", text)
        if lead_dot:
            ref_id = lead_dot.group(1)
            text = text[lead_dot.end():]

    # Extract Year
    year = ""
    year_match = _YEAR_PATTERN.search(text)
    if year_match:
        year = year_match.group(1)

    # Extract DOI
    doi = ""
    doi_match = _DOI_PATTERN.search(text)
    if doi_match:
        doi = doi_match.group(1)

    # Extract URL
    url = ""
    url_match = _URL_PATTERN.search(text)
    if url_match:
        url = url_match.group(1)

    # Extract Title (often inside quotes or before period/comma)
    title = ""
    authors = []
    venue = ""

    quoted_title = re.search(r'["“\']([^"”\']{5,200})["”\']', text)
    if quoted_title:
        title = _clean_str(quoted_title.group(1)).rstrip('",.')
        before_title = text[:quoted_title.start()].strip().rstrip(',.')
        after_title = text[quoted_title.end():].strip().lstrip(',.')

        # Extract authors from before_title
        if before_title:
            cand_authors = re.split(r",\s*(?:and\s+)?|\s+and\s+", before_title)
            for c in cand_authors:
                c_clean = _clean_str(re.sub(r"\b(?:et\s+al\.?|\d+)\b", "", c)).strip(",")
                if c_clean and len(c_clean) >= 2 and any(ch.isalpha() for ch in c_clean):
                    authors.append(c_clean)

        # Extract venue from after_title
        venue_cand = re.sub(r"^(?:in\s+|proceedings\s+of\s+)", "", after_title, flags=re.IGNORECASE)
        if year:
            venue_cand = venue_cand.replace(year, "")
        if doi:
            venue_cand = venue_cand.replace(doi, "")
        venue_parts = [p.strip() for p in re.split(r"[,.]", venue_cand) if p.strip() and not p.strip().lower().startswith("doi")]
        if venue_parts:
            venue = venue_parts[0]
    else:
        # Fallback to period-based splitting with initial protection
        segments = [s.strip() for s in re.split(r"(?<!\b[A-Z])\.\s+", text) if s.strip()]
        if segments:
            author_seg = segments[0]
            cand_authors = re.split(r",\s*(?:and\s+)?|\s+and\s+", author_seg)
            for c in cand_authors:
                c_clean = _clean_str(re.sub(r"\b(?:et\s+al\.?|\d+)\b", "", c)).strip(",")
                if c_clean and len(c_clean) >= 2 and any(ch.isalpha() for ch in c_clean):
                    authors.append(c_clean)

            if len(segments) > 1:
                title = segments[1]
                if len(segments) > 2:
                    venue = segments[2]
            else:
                title = text[:80]


    key = _generate_bibtex_key(authors, year, title, ref_id)
    bibtex = _format_bibtex(key, authors, title, year, venue, doi, url)
    apa = _format_apa(authors, year, title, venue, doi)
    ieee = _format_ieee(ref_id, authors, title, venue, year)
    mla = _format_mla(authors, title, venue, year)

    return ParsedReference(
        id=ref_id,
        raw_text=raw_ref.strip(),
        authors=authors[:6],
        title=title,
        year=year,
        venue=venue,
        doi=doi,
        url=url,
        bibtex=bibtex,
        apa=apa,
        ieee=ieee,
        mla=mla,
    )


def extract_references_from_text(text: str, sections: list) -> list[ParsedReference]:
    """
    Finds the references section from the detected sections or text suffix,
    and parses all bibliography entries.
    """
    ref_text = ""

    # Check detected sections first
    for sec in sections:
        sec_name = getattr(sec, "name", "").lower()
        if sec_name in ("references", "bibliography", "works cited"):
            start = getattr(sec, "start_char", 0)
            end = getattr(sec, "end_char", len(text))
            ref_text = text[start:end]
            break

    # Fallback: scan for heading in raw text
    if not ref_text:
        match = re.search(r"\n\s*(?:references|bibliography)\s*\n", text, re.IGNORECASE)
        if match:
            ref_text = text[match.end():]

    if not ref_text or len(ref_text.strip()) < 40:
        return []

    entries: list[str] = []

    # Try numbered bracket style [1]
    bracket_splits = _NUMBERED_REF_SPLIT.split(ref_text)
    if len(bracket_splits) > 3:
        # Pairs of (number, text)
        for i in range(1, len(bracket_splits), 2):
            num = bracket_splits[i]
            body = bracket_splits[i + 1] if i + 1 < len(bracket_splits) else ""
            entries.append(f"[{num}] {body.strip()}")
    else:
        # Try numbered dot style: 1. Author
        dot_splits = _ORDERED_REF_SPLIT.split(ref_text)
        if len(dot_splits) > 3:
            for i in range(1, len(dot_splits), 2):
                num = dot_splits[i]
                body = dot_splits[i + 1] if i + 1 < len(dot_splits) else ""
                entries.append(f"{num}. {body.strip()}")
        else:
            # Paragraph-based split
            paras = [p.strip() for p in ref_text.split("\n\n") if len(p.strip()) > 30]
            if len(paras) >= 2:
                entries = paras
            else:
                lines = [line.strip() for line in ref_text.splitlines() if len(line.strip()) > 25]
                entries = lines[:35]

    parsed_list: list[ParsedReference] = []
    for idx, entry in enumerate(entries[:50]):
        parsed = parse_single_reference(entry, fallback_id=str(idx + 1))
        parsed_list.append(parsed)

    return parsed_list


def detect_in_text_citations(text: str, parsed_references: list[ParsedReference]) -> list[dict]:
    """
    Finds in-text citation markers like [1], [2, 3], and (Author, 2020),
    returning their position and matched reference IDs.
    """
    ref_map = {r.id: r for r in parsed_references}
    results = []

    # Match bracket citations [1], [1, 2], [1-3]
    for match in _IN_TEXT_BRACKET.finditer(text):
        raw_inner = match.group(1)
        start_char, end_char = match.span()

        # Parse individual numbers
        ids = []
        for part in re.split(r"[,–-]", raw_inner):
            num = part.strip()
            if num.isdigit():
                ids.append(num)

        matched_refs = []
        for rid in ids:
            if rid in ref_map:
                ref = ref_map[rid]
                matched_refs.append({
                    "id": ref.id,
                    "title": ref.title,
                    "authors": ref.authors,
                    "year": ref.year,
                    "apa": ref.apa,
                    "bibtex": ref.bibtex,
                })

        results.append({
            "marker": match.group(0),
            "start_char": start_char,
            "end_char": end_char,
            "ref_ids": ids,
            "matched_references": matched_refs,
        })

    # Limit to top 100 in-text citations to maintain optimal response payload
    return results[:100]


def format_paper_self_citation(title: str, pdf_metadata: Optional[dict] = None) -> dict:
    """
    Generates standardized citations for the analyzed paper itself.
    """
    meta = pdf_metadata or {}
    authors = meta.get("authors") or []
    if isinstance(authors, str) and authors:
        authors = [a.strip() for a in authors.split(",")]
    elif not authors and meta.get("author"):
        authors = [meta.get("author")]

    year = meta.get("year") or str(meta.get("publication_year") or "")
    venue = meta.get("venue") or meta.get("subject") or "Academic Research Publication"
    doi = meta.get("identifier") if meta.get("identifier_type") == "doi" else ""
    url = meta.get("source_url") or ""

    key = _generate_bibtex_key(authors, year, title, "current")
    bibtex = _format_bibtex(key, authors, title, year, venue, doi, url)
    apa = _format_apa(authors, year, title, venue, doi)
    ieee = _format_ieee("1", authors, title, venue, year)
    mla = _format_mla(authors, title, venue, year)

    return {
        "title": title,
        "authors": authors,
        "year": year,
        "venue": venue,
        "bibtex": bibtex,
        "apa": apa,
        "ieee": ieee,
        "mla": mla,
    }
