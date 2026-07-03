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

    log_level: str = "INFO"
    port: int = 8080
    max_upload_size_bytes: int = 52_428_800  # 50 MB


settings = Settings()
