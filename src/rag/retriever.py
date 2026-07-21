"""Retriever helpers for the persistent Chroma RAG index."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from src.rag.embeddings import create_google_embeddings
from src.rag.vector_store import (
    DEFAULT_COLLECTION_NAME,
    DEFAULT_VECTOR_STORE_PATH,
    get_vector_store,
)

if TYPE_CHECKING:
    from langchain_core.documents import Document
    from langchain_core.embeddings import Embeddings


DEFAULT_RETRIEVER_K = 5


def create_retriever(
    embeddings: "Embeddings | None" = None,
    persist_directory: str | Path = DEFAULT_VECTOR_STORE_PATH,
    collection_name: str = DEFAULT_COLLECTION_NAME,
    k: int = DEFAULT_RETRIEVER_K,
) -> Any:
    """Create a LangChain retriever backed by the persistent Chroma index."""
    if k <= 0:
        raise ValueError("k must be greater than 0.")

    validate_vector_store(persist_directory, collection_name)
    vector_store = get_vector_store(
        embeddings=embeddings or create_google_embeddings(task_type=None),
        persist_directory=persist_directory,
        collection_name=collection_name,
    )
    return vector_store.as_retriever(search_kwargs={"k": k})


def retrieve_relevant_documents(retriever: Any, question: str) -> list["Document"]:
    """Retrieve documents relevant to a question using a LangChain retriever."""
    normalized_question = question.strip()
    if not normalized_question:
        raise ValueError("question must not be empty.")

    if hasattr(retriever, "invoke"):
        return list(retriever.invoke(normalized_question))

    return list(retriever.get_relevant_documents(normalized_question))


def validate_vector_store(
    persist_directory: str | Path = DEFAULT_VECTOR_STORE_PATH,
    collection_name: str = DEFAULT_COLLECTION_NAME,
) -> None:
    """Validate that the persistent Chroma collection exists and has documents."""
    persist_path = Path(persist_directory)
    if not persist_path.exists():
        raise FileNotFoundError(f"Vector store directory not found: {persist_path}")

    try:
        import chromadb
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Missing dependency: chromadb. Install project dependencies."
        ) from exc

    try:
        collection = chromadb.PersistentClient(path=str(persist_path)).get_collection(
            collection_name
        )
    except Exception as exc:
        raise RuntimeError(
            f"Chroma collection '{collection_name}' was not found in {persist_path}."
        ) from exc

    if collection.count() == 0:
        raise RuntimeError(
            f"Chroma collection '{collection_name}' exists but contains no documents."
        )
