from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central configuration for all LLM / embedding / auth settings.
    Support both Enterprise (Azure/Gemini) and Local (Ollama) modes.
    """

    # --- Mode Selection ---
    llm_provider: str = Field(default="ollama", alias="LLM_PROVIDER")

    # --- Auth / JWT (Enterprise) ---
    service_account: str = Field(default="", alias="SERVICE_ACCOUNT")
    service_account_pass: str = Field(default="", alias="SERVICE_ACCOUNT_PASS")
    auth_url: str = Field(default="", alias="AUTH_URL")

    # --- Azure OpenAI-like chat gateway (Enterprise) ---
    llm_api_base: str = Field(default="", alias="LLM_API_BASE")
    llm_deployment_name: str = Field(default="", alias="LLM_DEPLOYMENT_NAME")
    llm_api_version: str = Field(
        default="2024-06-01",
        alias="LLM_API_VERSION",
        description="API version for chat completions (Azure/OpenAI).",
    )

    # --- One-way Embedding gateway (Enterprise) ---
    embedding_api_base: str = Field(default="", alias="EMBEDDING_API_BASE")
    embedding_deployment_name: str = Field(default="", alias="EMBEDDING_DEPLOYMENT_NAME")
    embedding_api_version: str = Field(
        default="2024-06-01",
        alias="EMBEDDING_API_VERSION",
        description="API version for embeddings.",
    )

    # --- Gemini / Vertex gateway (Enterprise) ---
    base_url: str = Field(default="", alias="BASE_URL")
    chat_suffix: str = Field(default="genai/vertexai/gemini-2.5-pro/generateContent", alias="CHAT_SUFFIX")

    # --- Ollama Settings (Local) ---
    ollama_api_base: str = Field(default="http://localhost:11434/v1", alias="OLLAMA_API_BASE")
    ollama_chat_model: str = Field(default="llama3.2", alias="OLLAMA_CHAT_MODEL")
    ollama_embed_model: str = Field(default="nomic-embed-text", alias="OLLAMA_EMBED_MODEL")

    # --- Application-level settings ---
    chroma_path: str = Field(default="./chroma_store", alias="CHROMA_PATH")
    collection_name: str = Field(default="ai_usecases", alias="COLLECTION_NAME")
    environment: str = Field(default="dev", alias="ENVIRONMENT")

    # --- Data Source Configuration ---
    data_source: str = Field(
        default="excel",
        alias="DATA_SOURCE",
        description="Data source type: 'excel' or 'mysql'"
    )

    # --- MySQL Configuration ---
    mysql_host: str = Field(default="localhost", alias="MYSQL_HOST")
    mysql_port: int = Field(default=3306, alias="MYSQL_PORT")
    mysql_database: str = Field(default="ai_insights", alias="MYSQL_DATABASE")
    mysql_user: str = Field(default="root", alias="MYSQL_USER")
    mysql_password: str = Field(default="", alias="MYSQL_PASSWORD")
    mysql_table: str = Field(default="ai_usecases", alias="MYSQL_TABLE")
    mysql_ssl_enabled: bool = Field(default=False, alias="MYSQL_SSL_ENABLED")
    mysql_connection_pool_size: int = Field(default=5, alias="MYSQL_CONNECTION_POOL_SIZE")

    # --- Query Observability ---
    enable_sql_logging: bool = Field(default=True, alias="ENABLE_SQL_LOGGING")
    show_generated_sql: bool = Field(default=True, alias="SHOW_GENERATED_SQL")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        populate_by_name=True,
    )


settings = Settings()
