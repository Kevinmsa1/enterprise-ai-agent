"""Embedding model factory for the RAG indexing pipeline."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from langchain_core.embeddings import Embeddings


DEFAULT_EMBEDDING_MODEL = "models/gemini-embedding-001"
DEFAULT_DOCUMENT_TASK_TYPE = "RETRIEVAL_DOCUMENT"


class EmbeddingConfigurationError(RuntimeError):
    """Raised when the embedding model cannot be configured."""


def create_google_embeddings(
    model: str | None = None,
    task_type: str | None = DEFAULT_DOCUMENT_TASK_TYPE,
    output_dimensionality: int | None = None,
) -> "Embeddings":
    """Create a Gemini embedding model for document indexing.

    The returned object implements LangChain's ``Embeddings`` interface and can
    be reused by Chroma or by retrievers that need query embeddings later.
    """
    _load_environment()
    _ensure_google_credentials()

    try:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
    except ModuleNotFoundError as exc:
        raise EmbeddingConfigurationError(
            "Missing dependency: langchain-google-genai. "
            "Install project dependencies before building the vector store."
        ) from exc

    kwargs: dict[str, object] = {
        "model": model or os.getenv("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL),
    }

    if task_type:
        kwargs["task_type"] = task_type

    if output_dimensionality is not None:
        kwargs["output_dimensionality"] = output_dimensionality

    return GoogleGenerativeAIEmbeddings(**kwargs)


def _ensure_google_credentials() -> None:
    """Validate that the Gemini API credentials are available."""
    if os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"):
        return

    raise EmbeddingConfigurationError(
        "Set GOOGLE_API_KEY or GEMINI_API_KEY before generating embeddings."
    )


def _load_environment() -> None:
    """Load local environment variables when python-dotenv is available."""
    try:
        from dotenv import load_dotenv
    except ModuleNotFoundError:
        return

    load_dotenv()
