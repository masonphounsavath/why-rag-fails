"""
Download and parse SEC 10-K filings for all companies in the corpus.

Usage:
    python scripts/download_corpus.py
    python scripts/download_corpus.py --tickers AAPL MSFT   # subset
    python scripts/download_corpus.py --start 2022 --end 2023

Output:
    data/raw/{ticker}/{year}.txt   — clean plaintext per filing
    data/raw/manifest.json         — metadata for all downloaded filings
"""

import json
import logging
import argparse
from pathlib import Path

from src.ingestion.downloader import COMPANIES, get_10k_filings, download_filing
from src.ingestion.parser import parse_html

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

DATA_DIR = Path("data/raw")


def main():
    parser = argparse.ArgumentParser(description="Download SEC 10-K corpus")
    parser.add_argument(
        "--tickers",
        nargs="+",
        default=list(COMPANIES.keys()),
        help="Tickers to download (default: all)",
    )
    parser.add_argument("--start", type=int, default=2021, help="Start year (inclusive)")
    parser.add_argument("--end",   type=int, default=2023, help="End year (inclusive)")
    args = parser.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    manifest = []

    for ticker in args.tickers:
        if ticker not in COMPANIES:
            logger.warning(f"Unknown ticker '{ticker}', skipping.")
            continue

        logger.info(f"=== {ticker} ===")
        filings = get_10k_filings(ticker, start_year=args.start, end_year=args.end)

        if not filings:
            logger.warning(f"No 10-K filings found for {ticker} in {args.start}-{args.end}")
            continue

        ticker_dir = DATA_DIR / ticker
        ticker_dir.mkdir(exist_ok=True)

        for meta in filings:
            out_path = ticker_dir / f"{meta.year}.txt"

            if out_path.exists():
                logger.info(f"  {ticker} {meta.year} already exists, skipping download.")
                manifest.append({
                    "ticker": meta.ticker,
                    "company": meta.company,
                    "year": meta.year,
                    "filed_date": meta.filed_date,
                    "path": str(out_path),
                    "skipped": True,
                })
                continue

            try:
                html = download_filing(meta)
                parsed = parse_html(
                    html,
                    ticker=meta.ticker,
                    company=meta.company,
                    year=meta.year,
                    filed_date=meta.filed_date,
                )
            except Exception as e:
                logger.error(f"  Failed to download/parse {ticker} {meta.year}: {e}")
                continue

            out_path.write_text(parsed.text, encoding="utf-8")
            logger.info(f"  Saved {ticker} {meta.year} -> {out_path} ({parsed.char_count:,} chars)")

            manifest.append({
                "ticker": meta.ticker,
                "company": meta.company,
                "year": meta.year,
                "filed_date": meta.filed_date,
                "accession_number": meta.accession_number,
                "document_url": meta.document_url,
                "char_count": parsed.char_count,
                "path": str(out_path),
                "skipped": False,
            })

    manifest_path = DATA_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    logger.info(f"\nDone. {len(manifest)} filings written to manifest at {manifest_path}")


if __name__ == "__main__":
    main()
