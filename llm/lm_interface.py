from typing import List, Dict, Any, Optional
from openai import OpenAI

from config import OPENAI_API_KEY, OPENAI_MODEL

_client = OpenAI(api_key=OPENAI_API_KEY)


def chat_completion(
    system_prompt: str,
    user_prompt: str,
    tools: Optional[List[Dict[str, Any]]] = None,
) -> str:
    # Swap to an alternative client (e.g., Ollama) here by reading config settings if you prefer local inference.
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    resp = _client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        tools=tools,
        temperature=0.2,
    )
    return resp.choices[0].message.content or ""
