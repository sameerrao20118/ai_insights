from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Literal, Optional

import requests

# Try modern langchain-core, fallback to legacy schema
try:
    from langchain_core.messages import HumanMessage, SystemMessage
except ImportError:
    from langchain.schema import HumanMessage, SystemMessage

try:
    from langchain_openai import AzureChatOpenAI, ChatOpenAI
except ImportError:
    # Helpful error for user debug
    raise ImportError("Please run 'pip install langchain-openai' to use this app.")

from openai import OpenAI
from pydantic import BaseModel, Field

# Local imports
try:
    from auth import delete_token_cache, get_cached_or_new_token
except ImportError:
    # Fallback if auth.py is missing/broken in local mode
    def get_cached_or_new_token(): return "dummy"
    def delete_token_cache(): pass

from config.settings import settings

logger = logging.getLogger(__name__)


# -------------------------------------------------------------------
#  Pydantic models for JSON-style answers (FinOps / Talk-to-Data)
# -------------------------------------------------------------------

class LeaderInsightAnswer(BaseModel):
    """LLM answer for portfolio-level 'leader insights' questions."""
    answer: str = Field(description="Concise, leader-friendly answer.")
    explanation: Optional[str] = Field(
        default=None,
        description="Brief explanation of how metrics and weights were used.",
    )

class CatalogueChatAnswer(BaseModel):
    """LLM answer for catalogue / 'talk to data' questions."""
    answer: str = Field(description="User-facing explanation / result.")
    explanation: Optional[str] = Field(
        default=None,
        description="Short reasoning, referring to filters, metrics, and weights.",
    )

# -------------------------------------------------------------------
#  Main Interface  
# -------------------------------------------------------------------

class LLMInterface:
    """
    Central LLM interface supporting both Enterprise (Azure OpenAI) and Local (Ollama).
    """

    def __init__(self) -> None:
        self.client_llm: Any = None
        self.embedding_client: Any = None
        self._initialize_client()
        logger.info(f"LLMInterface initialized in mode: {settings.llm_provider}")

    def _initialize_client(self) -> None:
        """Initializes clients based on LLM_PROVIDER settings."""
        if settings.llm_provider.lower() == "ollama":
            # --- Ollama Mode ---
            # We use standard ChatOpenAI pointing to localhost
            self.client_llm = ChatOpenAI(
                base_url=settings.ollama_api_base,
                api_key="ollama",
                model=settings.ollama_chat_model,
                temperature=0.2,
            )
            # Embeddings: Local OpenAI client to generate embeddings
            self.embedding_client = OpenAI(
                base_url=settings.ollama_api_base,
                api_key="ollama",
            )
        else:
            # --- Enterprise Mode ---
            self._init_enterprise_clients()

    def _init_enterprise_clients(self) -> None:
        """Initializes Azure/Enterprise clients with Auth."""
        token = get_cached_or_new_token()
        
        # Chat Client - Azure OpenAI format
        # Your gateway expects: {azure_endpoint}/openai/deployments/{deployment}/chat/completions
        if settings.llm_api_base:
            # The LLM_API_BASE should be just the base URL without /openai/deployments/
            # AzureChatOpenAI will construct the full path
            self.client_llm = AzureChatOpenAI(
                azure_endpoint=settings.llm_api_base,
                api_key=token,
                deployment_name=settings.llm_deployment_name,
                api_version=settings.llm_api_version,
                temperature=0.2,
            )
            logger.info(f"Enterprise Azure LLM client initialized")
        else:
            logger.warning("Enterprise mode selected but LLM_API_BASE not set.")

        # Embedding Client setup handled in embed_texts directly via requests 
        # for consistent Enterprise usage pattern.


    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 4000,
    ) -> str:
        """
        Generic chat completion helper.
        """
        from langchain_core.messages import SystemMessage, HumanMessage
        
        # Convert dict messages to LangChain messages
        lc_messages = []
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            if role == "system":
                lc_messages.append(SystemMessage(content=content))
            else:
                lc_messages.append(HumanMessage(content=content))

        # Invoke
        try:
            if not self.client_llm:
                self._initialize_client()
            
            result = self.client_llm.invoke(lc_messages)
            
            if hasattr(result, "content"):
                return str(result.content)
            return str(result)
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise



    # ----- JSON-oriented methods ----------

    def _parse_json_safely(self, raw_text: str) -> Dict[str, Any]:
        text = raw_text.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].lstrip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"answer": raw_text, "explanation": None}

    def chat_completion_json(
        self,
        system_prompt: str,
        payload: Dict[str, Any],
        answer_model: type[BaseModel] = LeaderInsightAnswer,
    ) -> BaseModel:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(payload)},
        ]
        raw = self.chat_completion(messages)
        data = self._parse_json_safely(raw)
        return answer_model.model_validate(data)


    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Gets embeddings. Dispatches to Local or Enterprise logic.
        """
        if not texts:
            return []

        if settings.llm_provider.lower() == "ollama":
            # Use local OpenAI client (Ollama)
            try:
                resp = self.embedding_client.embeddings.create(
                    model=settings.ollama_embed_model,
                    input=texts
                )
                return [d.embedding for d in resp.data]
            except Exception as e:
                logger.error(f"Local embedding failed: {e}")
                # Return dummy embeddings to allow ChromaDB to initialize
                # Using 1536 dimensions (standard for OpenAI embeddings)
                return [[0.0] * 1536 for _ in texts]
        else:
            # Enterprise Mode (Requests)
            return self._embed_texts_enterprise(texts)

    def _embed_texts_enterprise(self, texts: List[str]) -> List[List[float]]:
        token = get_cached_or_new_token()
        url = (
            f"{settings.embedding_api_base.rstrip('/')}//"
            f"{settings.embedding_deployment_name}/embeddings"
            f"?api-version={settings.embedding_api_version}"
        )
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.embedding_deployment_name,
            "input": texts,
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, verify=False, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            return [item["embedding"] for item in data["data"]]
        except Exception as e:
            logger.error(f"Enterprise embedding failed: {e}")
            logger.warning("Returning dummy embeddings to allow ChromaDB initialization. Fix your EMBEDDING_API_BASE and EMBEDDING_DEPLOYMENT_NAME in .env")
            # Return dummy embeddings to allow ChromaDB to initialize
            # Using 1536 dimensions (standard for OpenAI embeddings)
            return [[0.0] * 1536 for _ in texts]

# Backwards compatibility function for existing code
_interface = None

def chat_completion(system_prompt: str, user_prompt: str, tools=None) -> str:
    global _interface
    if not _interface:
        _interface = LLMInterface()
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    return _interface.chat_completion(messages)

