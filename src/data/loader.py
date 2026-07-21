"""Document loading helpers for local source files."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from src.data.parser import ParsedDocument, parse_document


DEFAULT_DOCUMENTS_PATH = Path("data/raw")
SUPPORTED_EXTENSIONS = frozenset({".pdf"})


def get_pdf_files(documents_path: str | Path = DEFAULT_DOCUMENTS_PATH) -> list[Path]:
    """Return all PDF files found in a directory, sorted by filename."""
    base_path = Path(documents_path)

    if not base_path.exists():
        raise FileNotFoundError(f"Documents directory not found: {base_path}")

    if not base_path.is_dir():
        raise NotADirectoryError(f"Documents path is not a directory: {base_path}")

    return sorted(
        path
        for path in base_path.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )


def load_documents(documents_path: str | Path = DEFAULT_DOCUMENTS_PATH) -> list[ParsedDocument]:
    """Parse all supported source documents from a directory."""
    return load_document_files(get_pdf_files(documents_path))


def load_document_files(paths: Iterable[str | Path]) -> list[ParsedDocument]:
    """Parse an explicit collection of document paths."""
    return [parse_document(Path(path)) for path in paths]
