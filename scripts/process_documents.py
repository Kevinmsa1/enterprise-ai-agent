"""Process local source documents into text chunks.

This script extracts text from PDFs and writes JSON chunks that can later be
used by an embeddings pipeline.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data.chunker import (  # noqa: E402
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    TextChunk,
    chunk_documents,
)
from src.data.loader import DEFAULT_DOCUMENTS_PATH, load_documents  # noqa: E402


DEFAULT_OUTPUT_PATH = Path("data/processed/chunks.json")


def process_documents(
    input_dir: str | Path = DEFAULT_DOCUMENTS_PATH,
    output_file: str | Path = DEFAULT_OUTPUT_PATH,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[TextChunk]:
    """Load, parse, chunk, and persist documents from a local directory."""
    input_path = Path(input_dir)
    output_path = Path(output_file)

    documents = load_documents(input_path)
    chunks = chunk_documents(documents, chunk_size=chunk_size, overlap=overlap)
    write_chunks(
        chunks=chunks,
        output_file=output_path,
        metadata={
            "input_dir": str(input_path),
            "document_count": len(documents),
            "chunk_count": len(chunks),
            "chunk_size": chunk_size,
            "overlap": overlap,
        },
    )

    return chunks


def write_chunks(
    chunks: list[TextChunk],
    output_file: str | Path,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Write chunk data to a JSON file."""
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "metadata": metadata or {},
        "chunks": [chunk.to_dict() for chunk in chunks],
    }
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Extract PDF text and create simple overlapping chunks."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=DEFAULT_DOCUMENTS_PATH,
        help="Directory containing source PDF files.",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Path where the chunks JSON file will be written.",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=DEFAULT_CHUNK_SIZE,
        help="Maximum number of characters per chunk.",
    )
    parser.add_argument(
        "--overlap",
        type=int,
        default=DEFAULT_CHUNK_OVERLAP,
        help="Number of characters shared between consecutive chunks.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the document processing command."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        chunks = process_documents(
            input_dir=args.input_dir,
            output_file=args.output_file,
            chunk_size=args.chunk_size,
            overlap=args.overlap,
        )
    except Exception as exc:
        print(f"Error processing documents: {exc}", file=sys.stderr)
        return 1

    print(f"Processed {len(chunks)} chunks.")
    print(f"Output written to {Path(args.output_file)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
