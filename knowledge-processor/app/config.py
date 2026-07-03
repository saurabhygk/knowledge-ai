from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Literal


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # PostgreSQL
    database_url: str = "postgresql://knowledgeai:secret@localhost:5432/knowledgeai"

    # Redis
    redis_url: str = "redis://localhost:6379"
    redis_stream: str = "knowledge-ai:document-processing"
    redis_consumer_group: str = "processor-group"
    redis_consumer_name: str = "processor-1"
    redis_block_ms: int = 5000
    redis_batch_size: int = 10

    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "knowledge-ai-docs"
    minio_secure: bool = False

    # Embeddings
    embedding_provider: Literal["openai", "ollama"] = "openai"
    openai_api_key: str = "change-me"
    openai_embedding_model: str = "text-embedding-3-small"
    ollama_base_url: str = "http://localhost:11434"
    ollama_embedding_model: str = "nomic-embed-text"

    # Chunking
    chunk_size: int = 512
    chunk_overlap: int = 64
    chunking_strategy: Literal["recursive", "element_aware"] = "recursive"

    # App
    log_level: str = "INFO"
    port: int = 8001


settings = Settings()
