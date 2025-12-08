from pathlib import Path
import os

try:
    from dotenv import load_dotenv
except ModuleNotFoundError as exc:
    raise ModuleNotFoundError(
        "python-dotenv is not installed. Install dependencies with the SAME interpreter you use to run Streamlit, "
        "e.g. `python -m pip install -r requirements.txt`."
    ) from exc

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)

# --- LLM defaults (OpenAI) ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

# --- LLM defaults (Ollama) ---
OLLAMA_API_BASE = os.getenv("OLLAMA_API_BASE", "http://localhost:11434")
OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "llama3.2")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")

# --- Storage / Chroma ---
CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_store")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "ai_usecases")

ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")
