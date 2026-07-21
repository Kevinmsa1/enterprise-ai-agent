"""Question-answering chain for the Enterprise AI Agent RAG flow."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from src.rag.embeddings import create_google_embeddings
from src.rag.prompt import NO_ANSWER_MESSAGE, create_rag_prompt
from src.rag.retriever import DEFAULT_RETRIEVER_K, create_retriever
from src.rag.vector_store import DEFAULT_COLLECTION_NAME, DEFAULT_VECTOR_STORE_PATH

if TYPE_CHECKING:
    from langchain_core.documents import Document
    from langchain_core.language_models.chat_models import BaseChatModel
    from langchain_core.prompts import ChatPromptTemplate


DEFAULT_CHAT_MODEL = "gemini-3.5-flash"
DEPRECATED_CHAT_MODELS = {
    "gemini-2.5-flash": DEFAULT_CHAT_MODEL,
    "models/gemini-2.5-flash": DEFAULT_CHAT_MODEL,
}


class ChatModelConfigurationError(RuntimeError):
    """Raised when the Gemini chat model cannot be configured."""


@dataclass(frozen=True)
class Source:
    """Source metadata returned with a RAG answer."""

    file: str
    page: int
    chunk_id: str


@dataclass(frozen=True)
class RAGResponse:
    """Answer and source documents produced by the RAG chain."""

    answer: str
    sources: list[Source]


@dataclass
class RAGQAChain:
    """Small reusable RAG chain composed of retriever, prompt, and Gemini."""

    retriever: Any
    llm: "BaseChatModel"
    prompt: "ChatPromptTemplate"

    def invoke(self, question: str) -> RAGResponse:
        """Answer a question using retrieved context and return sources."""
        normalized_question = question.strip()
        if not normalized_question:
            raise ValueError("question must not be empty.")

        documents = _retrieve(self.retriever, normalized_question)
        if not documents:
            return RAGResponse(answer=NO_ANSWER_MESSAGE, sources=[])

        context = format_documents_for_prompt(documents)
        answer_chain = self.prompt | self.llm | _string_output_parser()
        answer = answer_chain.invoke(
            {"context": context, "question": normalized_question}
        )

        return RAGResponse(
            answer=answer.strip(),
            sources=extract_sources(documents),
        )


def create_rag_qa_chain(
    persist_directory: str | Path = DEFAULT_VECTOR_STORE_PATH,
    collection_name: str = DEFAULT_COLLECTION_NAME,
    k: int = DEFAULT_RETRIEVER_K,
    chat_model: str | None = None,
    embedding_model: str | None = None,
) -> RAGQAChain:
    """Create a reusable RAG question-answering chain."""
    embeddings = _create_query_embeddings(model=embedding_model)
    retriever = create_retriever(
        embeddings=embeddings,
        persist_directory=persist_directory,
        collection_name=collection_name,
        k=k,
    )
    llm = create_gemini_llm(model=chat_model)
    return RAGQAChain(
        retriever=retriever,
        llm=llm,
        prompt=create_rag_prompt(),
    )


def create_gemini_llm(
    model: str | None = None,
    temperature: float = 0.0,
) -> "BaseChatModel":
    """Create the Gemini chat model used to generate grounded answers."""
    _load_environment()
    _ensure_google_credentials()

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ModuleNotFoundError as exc:
        raise ChatModelConfigurationError(
            "Missing dependency: langchain-google-genai. "
            "Install project dependencies before running RAG."
        ) from exc

    return ChatGoogleGenerativeAI(
        model=_resolve_chat_model(model),
        temperature=temperature,
    )


def format_documents_for_prompt(documents: list["Document"]) -> str:
    """Format retrieved documents as a compact context block."""
    sections: list[str] = []

    for index, document in enumerate(documents, start=1):
        metadata = document.metadata
        file_name = str(metadata.get("file") or metadata.get("source") or "unknown")
        page = _coerce_page(metadata.get("page"))
        chunk_id = str(metadata.get("chunk_id") or document.id or f"chunk-{index}")
        sections.append(
            "\n".join(
                [
                    f"[Documento {index}]",
                    f"Archivo: {file_name}",
                    f"Pagina: {page}",
                    f"Chunk ID: {chunk_id}",
                    "Contenido:",
                    document.page_content,
                ]
            )
        )

    return "\n\n---\n\n".join(sections)


def extract_sources(documents: list["Document"]) -> list[Source]:
    """Extract unique source references from retrieved documents."""
    sources: list[Source] = []
    seen: set[tuple[str, int, str]] = set()

    for document in documents:
        metadata = document.metadata
        file_name = str(metadata.get("file") or metadata.get("source") or "unknown")
        page = _coerce_page(metadata.get("page"))
        chunk_id = str(metadata.get("chunk_id") or document.id or "")
        key = (file_name, page, chunk_id)

        if key in seen:
            continue

        seen.add(key)
        sources.append(Source(file=file_name, page=page, chunk_id=chunk_id))

    return sources


def _create_query_embeddings(model: str | None = None) -> Any:
    return create_google_embeddings(
        model=model,
        task_type=None,
    )


def _resolve_chat_model(model: str | None = None) -> str:
    selected_model = model or os.getenv("MODEL_NAME", DEFAULT_CHAT_MODEL)
    return DEPRECATED_CHAT_MODELS.get(selected_model, selected_model)


def _retrieve(retriever: Any, question: str) -> list["Document"]:
    if hasattr(retriever, "invoke"):
        return list(retriever.invoke(question))

    return list(retriever.get_relevant_documents(question))


def _string_output_parser() -> Any:
    try:
        from langchain_core.output_parsers import StrOutputParser
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Missing dependency: langchain-core. Install project dependencies."
        ) from exc

    return StrOutputParser()


def _coerce_page(value: Any) -> int:
    if value is None:
        return 0

    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _ensure_google_credentials() -> None:
    if os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"):
        return

    raise ChatModelConfigurationError(
        "Set GOOGLE_API_KEY or GEMINI_API_KEY before running RAG."
    )


def _load_environment() -> None:
    try:
        from dotenv import load_dotenv
    except ModuleNotFoundError:
        return

    load_dotenv()
