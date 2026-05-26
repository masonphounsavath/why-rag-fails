"""
Embedding cache.

Saves and loads chunk embeddings to/from disk so the corpus doesn't need
to be re-embedded on every run. Embeddings are stored as .npy files
(numpy binary format). Chunk metadata is stored alongside as JSON.

Cache layout:
    data/embeddings/{ticker}_{year}_{strategy}.npy    — vectors
    data/embeddings/{ticker}_{year}_{strategy}.json   — chunk metadata

The .npy file and .json file are always written and read together.
If either is missing, the cache is treated as invalid.
"""

import json
import logging
import numpy as np
from pathlib import Path

from src.chunking.base import Chunk

logger = logging.getLogger(__name__)

CACHE_DIR = Path("data/embeddings")


def cache_key(ticker: str, year: int, strategy: str) -> str:
    return f"{ticker}_{year}_{strategy}"


def save(chunks: list[Chunk], vectors: np.ndarray, ticker: str, year: int, strategy: str) -> None:
    """
    Saves embeddings and chunk metadata to disk.

    Args:
        chunks:   The chunks that were embedded (in the same order as vectors).
        vectors:  Float32 array of shape (N, D).
        ticker:   Company ticker.
        year:     Filing year.
        strategy: Chunking strategy name.
    """
    assert len(chunks) == len(vectors), "chunks and vectors must have the same length"

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    key = cache_key(ticker, year, strategy)

    npy_path  = CACHE_DIR / f"{key}.npy"
    json_path = CACHE_DIR / f"{key}.json"

    np.save(npy_path, vectors)

    metadata = [
        {
            "chunk_id": c.chunk_id,
            "ticker":   c.ticker,
            "company":  c.company,
            "year":     c.year,
            "strategy": c.strategy,
            "text":     c.text,
            "metadata": c.metadata,
        }
        for c in chunks
    ]
    json_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    logger.info(f"Cached {len(chunks)} embeddings -> {npy_path}")


def load(ticker: str, year: int, strategy: str) -> tuple[list[Chunk], np.ndarray] | None:
    """
    Loads cached embeddings from disk.

    Returns:
        (chunks, vectors) if the cache exists, None otherwise.
    """
    key = cache_key(ticker, year, strategy)
    npy_path  = CACHE_DIR / f"{key}.npy"
    json_path = CACHE_DIR / f"{key}.json"

    if not npy_path.exists() or not json_path.exists():
        return None

    vectors = np.load(npy_path)
    raw = json.loads(json_path.read_text(encoding="utf-8"))

    chunks = [
        Chunk(
            chunk_id=r["chunk_id"],
            ticker=r["ticker"],
            company=r["company"],
            year=r["year"],
            strategy=r["strategy"],
            text=r["text"],
            metadata=r["metadata"],
        )
        for r in raw
    ]

    logger.info(f"Loaded {len(chunks)} cached embeddings from {npy_path}")
    return chunks, vectors


def exists(ticker: str, year: int, strategy: str) -> bool:
    key = cache_key(ticker, year, strategy)
    return (CACHE_DIR / f"{key}.npy").exists() and (CACHE_DIR / f"{key}.json").exists()
