"""
Chunk embedder.

Converts Chunk objects into dense vector representations using a
sentence-transformers model. Vectors are used by the retrieval layer
to find chunks semantically similar to a query.

Model choice: all-MiniLM-L6-v2
    - 384-dimensional embeddings
    - Fast on CPU, no GPU required
    - Strong general-purpose semantic similarity performance
    - ~80MB download, cached locally after first use

The model is loaded once at module level and reused across calls.
"""

import logging
import numpy as np
from sentence_transformers import SentenceTransformer

from src.chunking.base import Chunk

logger = logging.getLogger(__name__)

MODEL_NAME = "all-MiniLM-L6-v2"
_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        logger.info(f"Loading embedding model: {MODEL_NAME}")
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed_chunks(chunks: list[Chunk], batch_size: int = 64) -> np.ndarray:
    """
    Embeds a list of chunks and returns a matrix of shape (N, D).

    Args:
        chunks:     List of Chunk objects to embed.
        batch_size: Number of chunks to encode in one forward pass.
                    Reduce if you run into memory issues.

    Returns:
        Float32 numpy array of shape (len(chunks), embedding_dim).
        Row i corresponds to chunks[i].
    """
    if not chunks:
        return np.empty((0, 384), dtype=np.float32)

    model = _get_model()
    texts = [c.text for c in chunks]

    logger.info(f"Embedding {len(chunks)} chunks in batches of {batch_size}...")
    vectors = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,  # L2-normalize for cosine similarity via dot product
    )

    return vectors.astype(np.float32)


def embed_query(query: str) -> np.ndarray:
    """
    Embeds a single query string.

    Returns:
        Float32 numpy array of shape (embedding_dim,).
    """
    model = _get_model()
    vector = model.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    return vector[0].astype(np.float32)
