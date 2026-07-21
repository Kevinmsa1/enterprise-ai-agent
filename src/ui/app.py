import streamlit as st

st.set_page_config(
    page_title="Enterprise AI Agent",
    page_icon="🤖",
    layout="wide",
)

st.title("🤖 Enterprise AI Agent")

st.subheader("Santo Pegasus Soluciones")

st.markdown(
    """
Ask questions about the company's internal documentation using AI.

The assistant searches the knowledge base and answers using only the indexed documents.
"""
)

st.divider()

question = st.text_area(
    "Ask a question",
    placeholder="Example: What is the incident response protocol?",
    height=120,
)

if st.button("Ask", use_container_width=True):
    if not question.strip():
        st.warning("Please enter a question.")
    else:
        with st.spinner("Searching documentation..."):
            st.info("RAG integration will be connected in the next step.")