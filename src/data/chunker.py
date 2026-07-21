"""Simple text chunking utilities for parsed documents."""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha1
from typing import Any

from src.data.parser import ParsedDocument


DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200


@dataclass(frozen=True)
class TextChunk:
    """A text fragment ready to be embedded later."""

    id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation of the chunk."""
        return {
            "id": self.id,
            "text": self.text,
            "metadata": self.metadata,
        }


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[tuple[str, int, int]]:
    """Split text into character chunks with a fixed overlap."""
    _validate_chunking_config(chunk_size=chunk_size, overlap=overlap)

    normalized_text = text.strip()
    if not normalized_text:
        return []

    chunks: list[tuple[str, int, int]] = []
    step = chunk_size - overlap
    start = 0

    while start < len(normalized_text):
        end = min(start + chunk_size, len(normalized_text))
        chunk = normalized_text[start:end]

        if chunk:
            chunks.append((chunk, start, end))

        if end == len(normalized_text):
            break

        start += step

    return chunks


def chunk_document(
    document: ParsedDocument,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[TextChunk]:
    """Split a parsed document into text chunks with source metadata."""
    source_id = _source_id(document)
    chunks = chunk_text(document.text, chunk_size=chunk_size, overlap=overlap)

    return [
        TextChunk(
            id=f"{source_id}-{index:04d}",
            text=chunk,
            metadata={
                **document.metadata,
                "chunk_index": index,
                "start_char": start,
                "end_char": end,
                "chunk_size": len(chunk),
            },
        )
        for index, (chunk, start, end) in enumerate(chunks)
    ]


def chunk_documents(
    documents: list[ParsedDocument],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[TextChunk]:
    """Split multiple parsed documents into a flat chunk list."""
    all_chunks: list[TextChunk] = []

    for document in documents:
        all_chunks.extend(
            chunk_document(document, chunk_size=chunk_size, overlap=overlap)
        )

    return all_chunks


def _source_id(document: ParsedDocument) -> str:
    """Build a stable, compact id for chunks from one source document."""
    source = str(document.source_path)
    digest = sha1(source.encode("utf-8")).hexdigest()[:12]
    return f"{document.source_path.stem}-{digest}"


def _validate_chunking_config(chunk_size: int, overlap: int) -> None:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")

    if overlap < 0:
        raise ValueError("overlap must be greater than or equal to 0")

    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")
