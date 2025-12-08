"""Central configuration for LLMs and storage.

Exports environment-driven settings for:
- OpenAI (API key, chat model, embedding model)
- Ollama (chat and embedding models; optional server URL)
- Chroma storage path and collection names
"""
from .settings import (
    OPENAI_API_KEY,
    OPENAI_MODEL,
    OPENAI_EMBEDDING_MODEL,
    OLLAMA_API_BASE,
    OLLAMA_CHAT_MODEL,
    OLLAMA_EMBED_MODEL,
    CHROMA_PATH,
    COLLECTION_NAME,
    ENVIRONMENT,
)

__all__ = [
    "OPENAI_API_KEY",
    "OPENAI_MODEL",
    "OPENAI_EMBEDDING_MODEL",
    "OLLAMA_API_BASE",
    "OLLAMA_CHAT_MODEL",
    "OLLAMA_EMBED_MODEL",
    "CHROMA_PATH",
    "COLLECTION_NAME",
    "ENVIRONMENT",
]
