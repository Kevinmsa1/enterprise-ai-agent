"""Document parsing utilities for the ingestion pipeline.

This module intentionally stays independent from LangChain or vector stores.
It returns plain Python data structures that can later feed an embeddings
pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class DocumentParsingError(RuntimeError):
    """Raised when a document cannot be parsed into text."""


class UnsupportedDocumentTypeError(ValueError):
    """Raised when a document extension has no parser."""


@dataclass(frozen=True)
class DocumentPage:
    """Text extracted from a single document page."""

    page_number: int
    text: str

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation of the page."""
        return {
            "page_number": self.page_number,
            "text": self.text,
        }


@dataclass(frozen=True)
class ParsedDocument:
    """A parsed source document with text and lightweight metadata."""

    source_path: Path
    pages: list[DocumentPage]
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def text(self) -> str:
        """Return all page text as a single string."""
        return "\n\n".join(page.text for page in self.pages if page.text).strip()

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation of the document."""
        return {
            "source_path": str(self.source_path),
            "metadata": self.metadata,
            "pages": [page.to_dict() for page in self.pages],
        }


def parse_document(path: str | Path) -> ParsedDocument:
    """Parse a supported document file into text and metadata."""
    document_path = Path(path)

    if document_path.suffix.lower() == ".pdf":
        return parse_pdf(document_path)

    raise UnsupportedDocumentTypeError(
        f"Unsupported document type: {document_path.suffix or '<none>'}"
    )


def parse_pdf(path: str | Path) -> ParsedDocument:
    """Extract text from a PDF file using PyMuPDF."""
    pdf_path = Path(path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    if not pdf_path.is_file():
        raise DocumentParsingError(f"PDF path is not a file: {pdf_path}")

    try:
        import fitz  # type: ignore[import-not-found]
    except ModuleNotFoundError as exc:
        raise DocumentParsingError(
            "PyMuPDF is required to parse PDFs. Install it with: pip install PyMuPDF"
        ) from exc

    try:
        with fitz.open(str(pdf_path)) as pdf_document:
            if pdf_document.needs_pass:
                raise DocumentParsingError(f"Encrypted PDF is not supported: {pdf_path}")

            pages = [
                DocumentPage(
                    page_number=page_number,
                    text=_normalize_page_text(page.get_text("text")),
                )
                for page_number, page in enumerate(pdf_document, start=1)
            ]

            metadata = {
                "source": str(pdf_path),
                "filename": pdf_path.name,
                "extension": pdf_path.suffix.lower(),
                "page_count": pdf_document.page_count,
            }
    except DocumentParsingError:
        raise
    except Exception as exc:
        raise DocumentParsingError(f"Could not parse PDF {pdf_path}: {exc}") from exc

    return ParsedDocument(
        source_path=pdf_path,
        pages=pages,
        metadata=metadata,
    )


def _normalize_page_text(text: str) -> str:
    """Normalize page text while preserving paragraph boundaries."""
    lines = [line.strip() for line in text.splitlines()]
    paragraphs: list[str] = []
    current_paragraph: list[str] = []

    for line in lines:
        if line:
            current_paragraph.append(line)
            continue

        if current_paragraph:
            paragraphs.append(" ".join(current_paragraph))
            current_paragraph = []

    if current_paragraph:
        paragraphs.append(" ".join(current_paragraph))

    return "\n\n".join(paragraphs).strip()
