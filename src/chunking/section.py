"""
Section-aware chunker (10-K specific).

10-K filings follow a standardized structure mandated by the SEC.
Each filing contains numbered Items (Item 1, Item 1A, Item 2, etc.)
with consistent names across all companies and years.

This chunker detects those section headers and splits the document at
section boundaries rather than at arbitrary character counts. This
preserves the natural semantic units of the document.

When a section is too long to embed in a single chunk, it is sub-chunked
using the same fixed-size logic as fixed.py, with each sub-chunk
retaining the section name in its metadata.

Why this matters:
    A question about "risk factors" should retrieve chunks from Item 1A,
    not random paragraphs that happen to mention the word "risk". Chunking
    by section makes that retrieval alignment much more reliable — and the
    contrast with fixed/sentence chunking is a measurable, documentable
    finding.
"""

import re
from .base import Chunk

# SEC-mandated 10-K section headers. Matches patterns like:
#   "Item 1.", "ITEM 1A.", "Item 7A. Quantitative...", "ITEM 1A"
# Matches lines like "Item 1.", "ITEM 1A.", "Item 7A. Quantitative..."
# Uses [^\S\n]* (spaces/tabs only, not newlines) so the match stays on one line.
_SECTION_RE = re.compile(
    r'^(ITEM\s+\d+[A-Z]?\b\.?[^\S\n]*[^\n]{0,80})$',
    re.IGNORECASE | re.MULTILINE,
)

# If a section exceeds this, sub-chunk it.
_MAX_SECTION_CHARS = 3000
_SUBCHUNK_SIZE = 1000
_SUBCHUNK_OVERLAP = 150


def _detect_sections(text: str) -> list[tuple[str, str]]:
    """
    Splits text into (section_name, section_text) pairs.
    Text before the first recognized header is labeled "preamble".
    """
    matches = list(_SECTION_RE.finditer(text))

    if not matches:
        return [("preamble", text)]

    sections = []

    # Text before the first match.
    preamble = text[:matches[0].start()].strip()
    if preamble:
        sections.append(("preamble", preamble))

    for i, match in enumerate(matches):
        section_name = match.group(0).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        section_text = text[start:end].strip()
        if section_text:
            sections.append((section_name, section_text))

    return sections


def _fixed_subchunk(
    text: str,
    ticker: str,
    company: str,
    year: int,
    section_name: str,
    start_index: int,
    chunk_size: int = _SUBCHUNK_SIZE,
    overlap: int = _SUBCHUNK_OVERLAP,
) -> list[Chunk]:
    """Splits a long section into fixed-size sub-chunks."""
    sub_chunks = []
    start = 0
    step = chunk_size - overlap
    i = start_index

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk_text = text[start:end].strip()
        if chunk_text:
            sub_chunks.append(Chunk(
                chunk_id=f"{ticker}_{year}_section_{i}",
                ticker=ticker,
                company=company,
                year=year,
                strategy="section",
                text=chunk_text,
                metadata={
                    "section_name": section_name,
                    "chunk_index": i,
                    "is_subchunk": True,
                },
            ))
            i += 1
        start += step

    return sub_chunks


def chunk(
    text: str,
    ticker: str,
    company: str,
    year: int,
) -> list[Chunk]:
    """
    Splits a 10-K filing into chunks aligned to SEC section boundaries.

    Each Item section becomes one chunk. Sections longer than
    _MAX_SECTION_CHARS are sub-chunked with fixed-size splitting while
    retaining the section name in metadata.

    Returns:
        List of Chunk objects in document order.
    """
    if not text:
        return []

    sections = _detect_sections(text)
    chunks = []
    index = 0

    for section_name, section_text in sections:
        if len(section_text) <= _MAX_SECTION_CHARS:
            chunks.append(Chunk(
                chunk_id=f"{ticker}_{year}_section_{index}",
                ticker=ticker,
                company=company,
                year=year,
                strategy="section",
                text=section_text,
                metadata={
                    "section_name": section_name,
                    "chunk_index": index,
                    "is_subchunk": False,
                },
            ))
            index += 1
        else:
            sub_chunks = _fixed_subchunk(
                section_text, ticker, company, year, section_name, start_index=index
            )
            chunks.extend(sub_chunks)
            index += len(sub_chunks)

    return chunks
