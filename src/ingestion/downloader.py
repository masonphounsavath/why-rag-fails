"""
SEC EDGAR downloader.

Fetches 10-K annual report filings for a set of companies using the
public EDGAR REST API. No authentication required, but EDGAR requires
a descriptive User-Agent header and a polite request rate (<= 10 req/s).

Flow:
    1. Fetch the company's submission history JSON from EDGAR.
    2. Filter to 10-K filings within the target year range.
    3. For each filing, resolve the primary HTML document URL.
    4. Download and return the raw HTML.
"""

import time
import logging
from dataclasses import dataclass

import requests

logger = logging.getLogger(__name__)

# EDGAR requires identifying yourself in the User-Agent header.
# Format: "Company/App contact@email.com"
HEADERS = {
    "User-Agent": "why-rag-fails mason@example.com",
    "Accept-Encoding": "gzip, deflate",
}

EDGAR_BASE = "https://data.sec.gov"
EDGAR_ARCHIVES = "https://www.sec.gov/Archives/edgar/data"

# Companies to include in the corpus.
# CIKs are zero-padded to 10 digits for the EDGAR API.
COMPANIES: dict[str, dict] = {
    "AAPL":  {"name": "Apple",        "cik": "0000320193"},
    "MSFT":  {"name": "Microsoft",    "cik": "0000789019"},
    "NVDA":  {"name": "Nvidia",       "cik": "0001045810"},
    "GOOGL": {"name": "Alphabet",     "cik": "0001652044"},
    "JPM":   {"name": "JPMorgan",     "cik": "0000019617"},
    "GS":    {"name": "Goldman Sachs","cik": "0000886982"},
    "META":  {"name": "Meta",         "cik": "0001326801"},
    "AMZN":  {"name": "Amazon",       "cik": "0001018724"},
}


@dataclass
class FilingMeta:
    ticker: str
    company: str
    cik: str
    year: int
    filed_date: str
    accession_number: str
    document_url: str


def _get(url: str, delay: float = 0.15) -> requests.Response:
    """GET with a polite delay to respect EDGAR rate limits."""
    time.sleep(delay)
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response


def get_10k_filings(ticker: str, start_year: int = 2021, end_year: int = 2023) -> list[FilingMeta]:
    """
    Returns metadata for all 10-K filings for a company within the year range.
    """
    company = COMPANIES[ticker]
    cik = company["cik"]
    cik_stripped = cik.lstrip("0")

    url = f"{EDGAR_BASE}/submissions/CIK{cik}.json"
    logger.info(f"Fetching submission history for {ticker} ({cik})")

    data = _get(url).json()
    filings = data["filings"]["recent"]

    results = []
    for i, form in enumerate(filings["form"]):
        if form != "10-K":
            continue

        filed_date = filings["filingDate"][i]
        filing_year = int(filed_date[:4])

        if not (start_year <= filing_year <= end_year):
            continue

        accession_raw = filings["accessionNumber"][i]
        accession_dashed = accession_raw  # e.g. "0000320193-23-000064"
        accession_nodash = accession_raw.replace("-", "")

        # The submissions JSON includes the primary document filename directly.
        primary_doc = filings["primaryDocument"][i]
        doc_url = f"{EDGAR_ARCHIVES}/{cik_stripped}/{accession_nodash}/{primary_doc}"

        results.append(FilingMeta(
            ticker=ticker,
            company=company["name"],
            cik=cik,
            year=filing_year,
            filed_date=filed_date,
            accession_number=accession_dashed,
            document_url=doc_url,
        ))
        logger.info(f"  Found 10-K: {ticker} {filed_date} -> {doc_url}")

    return results



def download_filing(meta: FilingMeta) -> str:
    """Downloads a filing and returns the raw HTML content."""
    logger.info(f"Downloading {meta.ticker} {meta.year} from {meta.document_url}")
    response = _get(meta.document_url, delay=0.2)
    return response.text
