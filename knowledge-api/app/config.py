from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql://knowledgeai:secret@localhost:5432/knowledgeai"

    redis_url: str = "redis://localhost:6379"
    redis_stream: str = "knowledge-ai:document-processing"

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "knowledge-ai-docs"
    minio_secure: bool = False

    # ── Embedding provider ────────────────────────────────────────────
    # Supported values: openai | ollama
    # Add new provider: add a branch in app/embeddings/factory.py, set this var.
    embedding_provider: str = "openai"
    openai_api_key: str = "change-me"
    openai_embedding_model: str = "text-embedding-3-small"
    ollama_base_url: str = "http://localhost:11434"
    ollama_embedding_model: str = "nomic-embed-text"

    # ── LLM provider ──────────────────────────────────────────────────
    # Supported values: ollama | openai | anthropic
    # Add new provider: add a branch in app/llm/factory.py, set this var.
    llm_provider: str = "ollama"
    ollama_chat_model: str = "llama3.2"
    openai_chat_model: str = "gpt-4o-mini"
    anthropic_api_key: str = ""
    anthropic_chat_model: str = "claude-sonnet-4-6"

    log_level: str = "INFO"
    port: int = 8080
    max_upload_size_bytes: int = 52_428_800  # 50 MB


settings = Settings()
