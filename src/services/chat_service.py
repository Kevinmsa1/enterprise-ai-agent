"""Application service for asking questions through the RAG backend."""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from src.rag.qa_chain import RAGResponse, Source, create_rag_qa_chain
from src.rag.retriever import DEFAULT_RETRIEVER_K
from src.rag.vector_store import DEFAULT_COLLECTION_NAME, DEFAULT_VECTOR_STORE_PATH


class ChatServiceError(RuntimeError):
    """Raised when the chat service cannot complete a request."""


@dataclass(frozen=True)
class ChatSource:
    """Source information prepared for presentation in the UI."""

    file: str
    page: int
    chunk_id: str
    pages: tuple[int, ...] = ()
    chunk_ids: tuple[str, ...] = ()

    @property
    def page_label(self) -> str:
        """Return a readable page label for the UI."""
        pages = self.pages or ((self.page,) if self.page > 0 else ())
        return ", ".join(str(page) for page in pages) if pages else "no disponible"

    @property
    def chunk_label(self) -> str:
        """Return a readable chunk label for the UI."""
        chunk_ids = self.chunk_ids or ((self.chunk_id,) if self.chunk_id else ())
        return ", ".join(chunk_ids) if chunk_ids else "no disponible"


@dataclass(frozen=True)
class ChatAnswer:
    """Answer returned by the chat service."""

    answer: str
    sources: list[ChatSource]


@dataclass
class _GroupedSource:
    file: str
    first_page: int
    first_chunk_id: str
    pages: list[int] = field(default_factory=list)
    chunk_ids: list[str] = field(default_factory=list)


class ChatService:
    """Facade that hides RAG internals from the UI layer."""

    def __init__(
        self,
        persist_directory: str | Path = DEFAULT_VECTOR_STORE_PATH,
        collection_name: str = DEFAULT_COLLECTION_NAME,
        k: int = DEFAULT_RETRIEVER_K,
        chat_model: str | None = None,
        embedding_model: str | None = None,
    ) -> None:
        self._chain = create_rag_qa_chain(
            persist_directory=persist_directory,
            collection_name=collection_name,
            k=k,
            chat_model=chat_model,
            embedding_model=embedding_model,
        )

    def ask(self, question: str) -> ChatAnswer:
        """Ask a question to the RAG backend."""
        normalized_question = question.strip()
        if not normalized_question:
            raise ValueError("question must not be empty.")

        try:
            response = self._chain.invoke(normalized_question)
        except Exception as exc:
            raise ChatServiceError(f"Could not generate an answer: {exc}") from exc

        return _to_chat_answer(response)


@lru_cache(maxsize=1)
def get_chat_service(
    persist_directory: str | Path = DEFAULT_VECTOR_STORE_PATH,
    collection_name: str = DEFAULT_COLLECTION_NAME,
    k: int = DEFAULT_RETRIEVER_K,
    chat_model: str | None = None,
    embedding_model: str | None = None,
) -> ChatService:
    """Return a cached chat service instance for repeated UI calls."""
    return ChatService(
        persist_directory=persist_directory,
        collection_name=collection_name,
        k=k,
        chat_model=chat_model,
        embedding_model=embedding_model,
    )


def _to_chat_answer(response: RAGResponse) -> ChatAnswer:
    return ChatAnswer(
        answer=response.answer,
        sources=_deduplicate_sources(response.sources),
    )


def _deduplicate_sources(sources: list[Source]) -> list[ChatSource]:
    grouped_sources: dict[str, _GroupedSource] = {}

    for source in sources:
        source_key = source.file
        grouped_source = grouped_sources.setdefault(
            source_key,
            _GroupedSource(
                file=source.file,
                first_page=source.page,
                first_chunk_id=source.chunk_id,
            ),
        )

        if source.page > 0 and source.page not in grouped_source.pages:
            grouped_source.pages.append(source.page)

        if source.chunk_id and source.chunk_id not in grouped_source.chunk_ids:
            grouped_source.chunk_ids.append(source.chunk_id)

    return [
        ChatSource(
            file=grouped_source.file,
            page=grouped_source.first_page,
            chunk_id=grouped_source.first_chunk_id,
            pages=tuple(grouped_source.pages),
            chunk_ids=tuple(grouped_source.chunk_ids),
        )
        for grouped_source in grouped_sources.values()
    ]
