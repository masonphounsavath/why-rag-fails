"""
Fixed-size chunker.

Splits text into chunks of a fixed character length with a configurable
overlap. This is the simplest possible chunking strategy and serves as
the baseline for comparison.

The overlap ensures that sentences split at a chunk boundary appear in
both adjacent chunks, reducing (but not eliminating) boundary failures.
"""

from .base import Chunk


def chunk(
    text: str,
    ticker: str,
    company: str,
    year: int,
    chunk_size: int = 1000,
    overlap: int = 200,
) -> list[Chunk]:
    """
    Splits text into fixed-size character chunks with overlap.

    Args:
        text:       The full document text.
        ticker:     Company ticker (e.g. "AAPL").
        company:    Company name (e.g. "Apple").
        year:       Filing year.
        chunk_size: Target character count per chunk.
        overlap:    Number of characters to repeat between adjacent chunks.

    Returns:
        List of Chunk objects in document order.
    """
    if not text:
        return []

    chunks = []
    start = 0
    index = 0
    step = chunk_size - overlap

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk_text = text[start:end].strip()

        if chunk_text:
            chunks.append(Chunk(
                chunk_id=f"{ticker}_{year}_fixed_{index}",
                ticker=ticker,
                company=company,
                year=year,
                strategy="fixed",
                text=chunk_text,
                metadata={
                    "chunk_index": index,
                    "char_start": start,
                    "char_end": end,
                    "chunk_size": chunk_size,
                    "overlap": overlap,
                },
            ))
            index += 1

        start += step

    return chunks
