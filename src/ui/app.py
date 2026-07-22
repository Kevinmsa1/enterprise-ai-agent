"""Streamlit chat interface for the Enterprise AI Agent."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.chat_service import ChatAnswer, ChatServiceError, get_chat_service


st.set_page_config(
    page_title="Enterprise AI Agent",
    layout="wide",
)


@st.cache_resource(show_spinner=False)
def _get_chat_service() -> Any:
    return get_chat_service()


def _render_sources(response: ChatAnswer) -> None:
    if not response.sources:
        st.caption("Fuentes: sin fuentes recuperadas.")
        return

    with st.expander("Fuentes utilizadas"):
        for source in response.sources:
            st.markdown(f"- `{source.file}` | pagina {source.page_label}")
            if source.chunk_label != "no disponible":
                st.caption(f"Chunks: {source.chunk_label}")


def main() -> None:
    """Render the Streamlit application."""
    st.title("Enterprise AI Agent")
    st.caption("Santo Pegasus Soluciones")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            response = message.get("response")
            if isinstance(response, ChatAnswer):
                _render_sources(response)

    question = st.chat_input("Pregunta sobre la documentacion")
    if not question:
        return

    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    try:
        with st.spinner("Consultando documentos..."):
            response = _get_chat_service().ask(question)
    except Exception as exc:
        st.error(str(exc))
        return

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response.answer,
            "response": response,
        }
    )
    with st.chat_message("assistant"):
        st.markdown(response.answer)
        _render_sources(response)


if __name__ == "__main__":
    main()
