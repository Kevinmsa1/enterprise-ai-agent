from pathlib import Path

from dotenv import load_dotenv
import os

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parents[1]
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-3.5-flash")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "models/gemini-embedding-001")

DOCUMENTS_PATH = os.getenv(
    "DOCUMENTS_PATH",
    str(REPO_ROOT / "data" / "raw")
)

CHROMA_DB_PATH = os.getenv(
    "CHROMA_DB_PATH",
    str(REPO_ROOT / "data" / "vector_store")
)
