from __future__ import annotations

from typing import List, Dict, Any, Optional

import requests
from openai import OpenAI

from config.settings import (
    LLM_PROVIDER,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    OLLAMA_API_BASE,
    OLLAMA_CHAT_MODEL,
)


# NOTE:
# - Provider is selected via LLM_PROVIDER from config/settings.py
# - Public API is chat_completion(...); call sites do not change.


def _chat_openai(
    system_prompt: str,
    user_prompt: str,
    tools: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """Chat completion using direct OpenAI API."""
    if not OPENAI_API_KEY:
        raise RuntimeError(
            "OPENAI_API_KEY is missing but LLM_PROVIDER is 'openai'. "
            "Set OPENAI_API_KEY in your .env or switch LLM_PROVIDER to 'ollama'."
        )
    client = OpenAI(api_key=OPENAI_API_KEY)
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        tools=tools,
        temperature=0.2,
    )
    # For this app we expect a simple string reply, not tool calls.
    return resp.choices[0].message.content or ""


def _chat_ollama(
    system_prompt: str,
    user_prompt: str,
    tools: Optional[List[Dict[str, Any]]] = None,  # tools are currently ignored for Ollama
) -> str:
    """Chat completion using a local Ollama model (llama3.2 by default)."""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    payload = {
        "model": OLLAMA_CHAT_MODEL,
        "messages": messages,
        # Options tuned for stable, JSON-friendly output. Adjust if needed.
        "options": {"temperature": 0.2},
        # Disable streaming so we get a single JSON object back.
        "stream": False,
    }
    resp = requests.post(
        f"{OLLAMA_API_BASE.rstrip('/')}/api/chat",
        json=payload,
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    # Non-streaming /api/chat returns: {"message": {"role": "...", "content": "..."}}
    return data["message"]["content"]


def _chat_enterprise(
    system_prompt: str,
    user_prompt: str,
    tools: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """
    Placeholder for enterprise gateway behaviour.

    IMPORTANT:
    - On the developer's laptop this branch is NOT used.
    - When LLM_PROVIDER='enterprise' on the office machine, you can
      replace this body with your existing JWT + gateway code:

        * Use service account + password to get a JWT (auth.py).
        * Call the bank's OpenAI-compatible / Azure gateway endpoint.
        * Preserve the same input and output format as _chat_openai.

    For now we just raise to make it obvious if it is accidentally selected.
    """
    raise RuntimeError(
        "LLM_PROVIDER is set to 'enterprise' but the enterprise gateway "
        "client is not wired yet in llm/lm_interface.py. "
        "On the office machine, plug in your auth.py + gateway call here."
    )


def chat_completion(
    system_prompt: str,
    user_prompt: str,
    tools: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """
    Unified chat entrypoint used by the rest of the app.

    - Reads LLM_PROVIDER from config/settings.py
    - Dispatches to the appropriate backend:
        'ollama'     -> local Ollama (default for laptop)
        'openai'     -> direct OpenAI API
        'enterprise' -> placeholder for bank gateway (to be filled on office machine)
    """
    provider = (LLM_PROVIDER or "ollama").lower()

    if provider == "openai":
        return _chat_openai(system_prompt, user_prompt, tools)
    elif provider == "ollama":
        return _chat_ollama(system_prompt, user_prompt, tools)
    elif provider == "enterprise":
        return _chat_enterprise(system_prompt, user_prompt, tools)
    else:
        raise ValueError(
            f"Unknown LLM_PROVIDER={LLM_PROVIDER!r}. "
            "Use one of: 'ollama', 'openai', 'enterprise'."
        )
