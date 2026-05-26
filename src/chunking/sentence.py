"""
Sentence-aware chunker.

Accumulates sentences until a chunk reaches the target character count,
then starts a new chunk. This avoids splitting mid-sentence, which the
fixed-size chunker does constantly.

Sentence detection uses a regex heuristic rather than a full NLP library.
This is intentional — it keeps the dependency footprint small and makes
the logic transparent. The tradeoff is that edge cases (e.g. "Inc." or
"Fig. 1") will occasionally produce false splits, which is itself a
documented failure mode.
"""

import re
from .base import Chunk

# Split on punctuation followed by whitespace and an uppercase letter.
# This is a heuristic, not a proper sentence tokenizer.
_SENTENCE_SPLIT = re.compile(r'(?<=[.!?])\s+(?=[A-Z])')


def _split_sentences(text: str) -> list[str]:
    return _SENTENCE_SPLIT.split(text)


def chunk(
    text: str,
    ticker: str,
    company: str,
    year: int,
    max_chars: int = 1000,
    overlap_sentences: int = 1,
) -> list[Chunk]:
    """
    Splits text into chunks that respect sentence boundaries.

    Args:
        text:               The full document text.
        ticker:             Company ticker.
        company:            Company name.
        year:               Filing year.
        max_chars:          Soft max character count per chunk. A chunk
                            will exceed this only if a single sentence is
                            longer than max_chars.
        overlap_sentences:  Number of sentences from the end of the previous
                            chunk to prepend to the next chunk.

    Returns:
        List of Chunk objects in document order.
    """
    if not text:
        return []

    sentences = _split_sentences(text)
    sentences = [s.strip() for s in sentences if s.strip()]

    chunks = []
    current: list[str] = []
    current_len = 0
    index = 0

    for sentence in sentences:
        sentence_len = len(sentence)

        # If adding this sentence would exceed the limit and we already
        # have content, flush the current chunk first.
        if current_len + sentence_len > max_chars and current:
            chunk_text = " ".join(current)
            chunks.append(Chunk(
                chunk_id=f"{ticker}_{year}_sentence_{index}",
                ticker=ticker,
                company=company,
                year=year,
                strategy="sentence",
                text=chunk_text,
                metadata={
                    "chunk_index": index,
                    "sentence_count": len(current),
                    "max_chars": max_chars,
                },
            ))
            index += 1

            # Carry the last N sentences into the next chunk as overlap.
            current = current[-overlap_sentences:] if overlap_sentences else []
            current_len = sum(len(s) for s in current)

        current.append(sentence)
        current_len += sentence_len

    # Flush any remaining sentences.
    if current:
        chunk_text = " ".join(current)
        chunks.append(Chunk(
            chunk_id=f"{ticker}_{year}_sentence_{index}",
            ticker=ticker,
            company=company,
            year=year,
            strategy="sentence",
            text=chunk_text,
            metadata={
                "chunk_index": index,
                "sentence_count": len(current),
                "max_chars": max_chars,
            },
        ))

    return chunks
