from __future__ import annotations
import math
from typing import Any, Dict, List, Optional

try:
    import chromadb
    from chromadb.utils import embedding_functions
    from chromadb import errors as chroma_errors
except ModuleNotFoundError as exc:  # noqa: F401 - used in __init__ guard
    chromadb = None  # type: ignore[assignment]
    embedding_functions = None  # type: ignore[assignment]
    chroma_errors = None  # type: ignore[assignment]

from config import CHROMA_PATH, COLLECTION_NAME, OPENAI_EMBEDDING_MODEL, OPENAI_API_KEY


class VectorDBManager:
    """Thin wrapper around ChromaDB with OpenAI embeddings."""

    def __init__(self) -> None:
        if chromadb is None or embedding_functions is None:
            raise RuntimeError(
                "chromadb is not installed in this Python environment. "
                "Install dependencies with the SAME interpreter you run Streamlit under, e.g.: "
                "`python3 -m pip install -r requirements.txt`"
            )
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is missing. Set it in .env or your environment before starting Streamlit.")
        self.embedding_api_base: Optional[str] = None
        self.embedding_deployment: Optional[str] = None
        # Embeddings use the centrally configured OpenAI model; swap here if moving to Ollama/local embeddings.
        self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
            api_key=OPENAI_API_KEY,
            model_name=OPENAI_EMBEDDING_MODEL,
        )
        self.persistent_client = chromadb.PersistentClient(path=CHROMA_PATH)
        self.collection = self.persistent_client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=self.embedding_function,
            metadata={"description": "AI Use Case Catalogue"},
        )

    def _refresh_collection(self) -> None:
        """Recreate the collection handle (useful if it was deleted externally)."""
        self.collection = self.persistent_client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=self.embedding_function,
            metadata={"description": "AI Use Case Catalogue"},
        )

    def _execute_with_retry(self, db_operation, *args, **kwargs):
        try:
            return db_operation(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001 - intentional broad catch for Chroma retries
            # If the collection was dropped externally, refresh and retry once.
            if chroma_errors and isinstance(exc, chroma_errors.NotFoundError):
                self._refresh_collection()
                return db_operation(*args, **kwargs)
            raise

    def _clean_metadata(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        """Flatten metadata to types accepted by Chroma (str|int|float|bool|None)."""
        cleaned: Dict[str, Any] = {}
        for k, v in meta.items():
            if v is None:
                cleaned[k] = None
            elif isinstance(v, float) and math.isnan(v):
                cleaned[k] = None
            elif isinstance(v, list):
                cleaned[k] = ", ".join(str(item) for item in v)
            elif isinstance(v, dict):
                cleaned[k] = str(v)
            else:
                cleaned[k] = v
        return cleaned

    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        ids = [d["id"] for d in documents]
        docs = [d["content"] for d in documents]
        metas = [self._clean_metadata(d.get("metadata", {})) for d in documents]

        def _op():
            self.collection.upsert(ids=ids, documents=docs, metadatas=metas)

        self._execute_with_retry(_op)

    def check_title_exists(self, normalized_title: str) -> bool:
        results = self.collection.get(
            where={"title": {"$eq": normalized_title}},
            include=["metadatas"],
        )
        return len(results.get("ids", [])) > 0

    def search_similar(self, query: str, k: int = 5):
        res = self.collection.query(query_texts=[query], n_results=k)
        final_results = []
        if not res["ids"]:
            return final_results
        for i in range(len(res["ids"][0])):
            final_results.append(
                {
                    "id": res["ids"][0][i],
                    "document": res["documents"][0][i],
                    "metadata": res["metadatas"][0][i],
                    "distance": res["distances"][0][i],
                }
            )
        return final_results

    def get_document_by_id(self, doc_id: str):
        res = self.collection.get(ids=[doc_id], include=["documents", "metadatas"])
        if not res["ids"]:
            return None
        return {
            "id": res["ids"][0],
            "document": res["documents"][0],
            "metadata": res["metadatas"][0],
        }

    def update_document(self, doc_id: str, metadata_update: Dict[str, Any]) -> None:
        existing = self.get_document_by_id(doc_id)
        if not existing:
            return
        updated_metadata = {**existing["metadata"], **metadata_update}

        def _op():
            self.collection.update(
                ids=[doc_id],
                metadatas=[updated_metadata],
                documents=[existing["document"]],
            )

        self._execute_with_retry(_op)

    def purge_all(self) -> None:
        """Delete all documents from the collection."""
        def _op():
            self.collection.delete(where={})
        self._execute_with_retry(_op)
