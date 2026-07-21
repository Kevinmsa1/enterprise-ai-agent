"""Build a persistent Chroma vector store from processed document chunks."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.rag.embeddings import (  # noqa: E402
    DEFAULT_EMBEDDING_MODEL,
    create_google_embeddings,
)
from src.rag.vector_store import (  # noqa: E402
    DEFAULT_CHUNKS_PATH,
    DEFAULT_BATCH_DELAY_SECONDS,
    DEFAULT_COLLECTION_NAME,
    DEFAULT_INDEX_BATCH_SIZE,
    DEFAULT_MAX_RETRIES,
    DEFAULT_VECTOR_STORE_PATH,
    IndexProgress,
    build_vector_store_from_chunks,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Embed processed chunks and persist them in ChromaDB."
    )
    parser.add_argument(
        "--chunks-file",
        type=Path,
        default=DEFAULT_CHUNKS_PATH,
        help="Path to the processed chunks JSON file.",
    )
    parser.add_argument(
        "--persist-dir",
        type=Path,
        default=DEFAULT_VECTOR_STORE_PATH,
        help="Directory where ChromaDB will persist the vector store.",
    )
    parser.add_argument(
        "--collection-name",
        default=DEFAULT_COLLECTION_NAME,
        help="Chroma collection name to create or update.",
    )
    parser.add_argument(
        "--embedding-model",
        default=DEFAULT_EMBEDDING_MODEL,
        help="Gemini embedding model passed to GoogleGenerativeAIEmbeddings.",
    )
    parser.add_argument(
        "--output-dimensionality",
        type=int,
        default=None,
        help="Optional Gemini embedding output dimensionality.",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append to the existing collection instead of rebuilding it.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_INDEX_BATCH_SIZE,
        help="Number of chunks to embed per batch.",
    )
    parser.add_argument(
        "--batch-delay-seconds",
        type=float,
        default=DEFAULT_BATCH_DELAY_SECONDS,
        help="Seconds to wait between embedding batches.",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=DEFAULT_MAX_RETRIES,
        help="Retries per batch when Gemini returns a quota/rate-limit error.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the vector store build command."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        embeddings = create_google_embeddings(
            model=args.embedding_model,
            output_dimensionality=args.output_dimensionality,
        )
        result = build_vector_store_from_chunks(
            chunks_file=args.chunks_file,
            embeddings=embeddings,
            persist_directory=args.persist_dir,
            collection_name=args.collection_name,
            reset_collection=not args.append,
            batch_size=args.batch_size,
            batch_delay_seconds=args.batch_delay_seconds,
            max_retries=args.max_retries,
            progress_callback=_print_progress,
        )
    except Exception as exc:
        print(f"Error building vector store: {exc}", file=sys.stderr)
        return 1

    print(f"Indexed {result.document_count} documents.")
    print(f"Collection: {result.collection_name}")
    print(f"Vector store: {result.persist_directory}")
    return 0


def _print_progress(progress: IndexProgress) -> None:
    message = (
        f"Indexed {progress.indexed_count}/{progress.total_count} documents "
        f"(batch {progress.batch_number}/{progress.batch_count})."
    )

    if progress.next_delay_seconds > 0:
        message += f" Waiting {progress.next_delay_seconds:.0f}s before next batch."

    print(message, flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
