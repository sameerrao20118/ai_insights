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

"""
LLM configuration notes:

1) Running LOCALLY on your laptop with OLLAMA  (recommended for experiments)
---------------------------------------------------------------------------
- Install Ollama from https://ollama.com
- In a terminal, pull the required models:

    ollama pull llama3.2          # chat model
    ollama pull nomic-embed-text  # embedding model (for future use)

- In your .env (in the project root), set:

    LLM_PROVIDER=ollama
    OLLAMA_API_BASE=http://localhost:11434
    OLLAMA_CHAT_MODEL=llama3.2
    OLLAMA_EMBED_MODEL=nomic-embed-text

- OPENAI_API_KEY can be left empty in this mode for chat.
  (Vector DB still uses OpenAI embeddings today; that can be migrated later.)

2) Running on OFFICE MACHINE via ENTERPRISE GATEWAY
---------------------------------------------------
- When you move this repo to your office machine, you will have:
    - Service account + password
    - JWT auth URL
    - Gateway chat and embedding endpoints

- In that scenario, you will typically set:

    LLM_PROVIDER=enterprise

    # Below are EXAMPLE names only. Replace the values with your bank's
    # gateway configuration and/or hook them into your existing auth.py + JWT flow.
    # For example, these often look like:
    #   https://<gateway-host>/genai/openai/gpt4x
    #   https://<gateway-host>/genai/openai/ada-embeddings

    ENTERPRISE_CHAT_BASE_URL="https://<change-me-on-office>/"
    ENTERPRISE_CHAT_MODEL="gpt4x-bank-deployment"
    ENTERPRISE_EMBED_BASE_URL="https://<change-me-on-office>/"
    ENTERPRISE_EMBED_MODEL="ada-bank-embeddings"

- The application code in llm/lm_interface.py already has a placeholder
  for client='enterprise'. On your office machine you can plug in the
  existing JWT + Azure/Gateway code (like the auth.py / LLMInterface
  pattern from your other project) inside that branch WITHOUT changing
  the rest of this app.
"""

# --- Which LLM to use? ---
# Options:
#   "ollama"     -> local llama model via Ollama (recommended for laptop experiments)
#   "openai"     -> direct OpenAI API (requires OPENAI_API_KEY)
#   "enterprise" -> bank gateway / JWT-based setup (to be used on office machine)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")

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
