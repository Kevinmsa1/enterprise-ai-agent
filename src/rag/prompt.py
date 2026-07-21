"""Prompt templates for strict context-grounded RAG answers."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from langchain_core.prompts import ChatPromptTemplate


NO_ANSWER_MESSAGE = "No encontr\u00e9 esa informaci\u00f3n en los documentos."

RAG_SYSTEM_PROMPT = f"""Eres un asistente de conocimiento interno.

Responde unicamente con la informacion incluida en el contexto proporcionado.
No uses conocimiento externo, suposiciones ni informacion no presente en el contexto.
Si el contexto no contiene informacion suficiente para responder la pregunta,
responde exactamente: "{NO_ANSWER_MESSAGE}"

Contexto:
{{context}}"""


def create_rag_prompt() -> "ChatPromptTemplate":
    """Create the chat prompt used by the RAG QA chain."""
    try:
        from langchain_core.prompts import ChatPromptTemplate
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Missing dependency: langchain-core. Install project dependencies."
        ) from exc

    return ChatPromptTemplate.from_messages(
        [
            ("system", RAG_SYSTEM_PROMPT),
            ("human", "Pregunta: {question}"),
        ]
    )
