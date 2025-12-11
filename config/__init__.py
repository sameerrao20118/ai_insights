"""Central configuration for LLMs and storage.

Exports environment-driven settings for:
- OpenAI (API key, chat model, embedding model)
- Ollama (chat and embedding models; optional server URL)
- Chroma storage path and collection names
"""
from .settings import settings

__all__ = ["settings"]
