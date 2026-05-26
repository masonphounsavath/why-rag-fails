"""
Shared types for the chunking module.

Every chunker returns a list of Chunk objects. Keeping the interface
consistent means the embedding and retrieval layers don't need to know
which chunking strategy produced a given chunk.
"""

from dataclasses import dataclass, field


@dataclass
class Chunk:
    chunk_id: str         # Unique ID: "{ticker}_{year}_{strategy}_{index}"
    ticker: str
    company: str
    year: int
    strategy: str         # "fixed" | "sentence" | "section"
    text: str
    metadata: dict = field(default_factory=dict)
    # metadata keys vary by strategy:
    #   fixed:    char_start, char_end, chunk_index
    #   sentence: chunk_index, sentence_count
    #   section:  section_name, chunk_index, is_subchunk
