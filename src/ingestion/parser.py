"""
Filing parser.

Converts raw SEC EDGAR HTML filings into clean, structured plaintext.

10-K filings are large HTML documents with a lot of noise:
- Inline XBRL tags (ix:nonfraction, ix:nonnumeric, etc.)
- Repeated boilerplate headers/footers
- Navigation tables and page break artifacts
- Empty lines and excessive whitespace

This parser strips all of that and returns readable text that is
suitable for chunking and embedding.
"""

import re
import logging
from dataclasses import dataclass

from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)

# Known SEC boilerplate patterns to strip after text extraction.
_BOILERPLATE_PATTERNS = [
    r"Table of Contents",
    r"^\s*\d+\s*$",          # Standalone page numbers
    r"^\s*[-–—]+\s*$",       # Divider lines
]
_BOILERPLATE_RE = re.compile(
    "|".join(_BOILERPLATE_PATTERNS), re.MULTILINE
)


@dataclass
class ParsedFiling:
    ticker: str
    company: str
    year: int
    filed_date: str
    text: str
    char_count: int


def parse_html(
    html: str,
    ticker: str,
    company: str,
    year: int,
    filed_date: str,
) -> ParsedFiling:
    """
    Parses a raw 10-K HTML filing into clean plaintext.

    Steps:
        1. Remove script, style, and XBRL-specific tags.
        2. Extract visible text with newline separators.
        3. Strip boilerplate and normalize whitespace.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Remove tags that never contain readable content.
    _TAGS_TO_REMOVE = ["script", "style", "meta", "link", "ix:header", "ix:hidden"]
    for tag_name in _TAGS_TO_REMOVE:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    # Unwrap inline XBRL tags — keep their text content, drop the tags.
    for tag in soup.find_all(re.compile(r"^ix:")):
        tag.unwrap()

    raw_text = soup.get_text(separator="\n")
    cleaned = _clean_text(raw_text)

    logger.info(
        f"Parsed {ticker} {year}: {len(html):,} chars HTML -> {len(cleaned):,} chars text"
    )

    return ParsedFiling(
        ticker=ticker,
        company=company,
        year=year,
        filed_date=filed_date,
        text=cleaned,
        char_count=len(cleaned),
    )


def _clean_text(text: str) -> str:
    """Normalizes whitespace and strips boilerplate from extracted text."""
    # Replace non-breaking spaces with regular spaces before any other processing.
    text = text.replace("\xa0", " ")

    lines = text.splitlines()

    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if _BOILERPLATE_RE.fullmatch(line):
            continue
        cleaned_lines.append(line)

    # Collapse runs of 3+ blank-ish lines into a single blank line.
    result = "\n".join(cleaned_lines)
    result = re.sub(r"\n{3,}", "\n\n", result)

    return result.strip()
