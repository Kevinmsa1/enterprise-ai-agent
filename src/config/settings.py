from dotenv import load_dotenv
import os

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.5-flash")

DOCUMENTS_PATH = os.getenv(
    "DOCUMENTS_PATH",
    "data/documents"
)

CHROMA_DB_PATH = os.getenv(
    "CHROMA_DB_PATH",
    "vectorstore"
)