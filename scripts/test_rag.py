"""Run an interactive RAG query against the persistent Chroma index."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.rag.qa_chain import create_rag_qa_chain  # noqa: E402
from src.rag.retriever import DEFAULT_RETRIEVER_K  # noqa: E402
from src.rag.vector_store import (  # noqa: E402
    DEFAULT_COLLECTION_NAME,
    DEFAULT_VECTOR_STORE_PATH,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Ask a question using the Enterprise AI Agent RAG flow."
    )
    parser.add_argument(
        "question",
        nargs="?",
        help="Question to answer. If omitted, the script prompts for one.",
    )
    parser.add_argument(
        "--persist-dir",
        type=Path,
        default=DEFAULT_VECTOR_STORE_PATH,
        help="Directory containing the persistent ChromaDB index.",
    )
    parser.add_argument(
        "--collection-name",
        default=DEFAULT_COLLECTION_NAME,
        help="Chroma collection name to query.",
    )
    parser.add_argument(
        "--k",
        type=int,
        default=DEFAULT_RETRIEVER_K,
        help="Number of relevant chunks to retrieve.",
    )
    parser.add_argument(
        "--chat-model",
        default=None,
        help="Gemini chat model used to answer.",
    )
    parser.add_argument(
        "--embedding-model",
        default=None,
        help="Gemini embedding model used for query embeddings.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run a RAG query and print the answer with sources."""
    parser = build_parser()
    args = parser.parse_args(argv)
    question = args.question or input("Pregunta: ").strip()

    try:
        chain = create_rag_qa_chain(
            persist_directory=args.persist_dir,
            collection_name=args.collection_name,
            k=args.k,
            chat_model=args.chat_model,
            embedding_model=args.embedding_model,
        )
        response = chain.invoke(question)
    except Exception as exc:
        print(f"Error running RAG: {exc}", file=sys.stderr)
        return 1

    print("\nRespuesta:")
    print(response.answer)
    print("\nFuentes:")

    if not response.sources:
        print("- Sin fuentes recuperadas.")
    else:
        for source in response.sources:
            page = str(source.page) if source.page > 0 else "no disponible"
            print(f"- {source.file} | pagina {page}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
