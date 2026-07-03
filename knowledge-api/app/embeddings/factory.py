from __future__ import annotations
from app.config import settings
from app.embeddings.base import EmbeddingProvider


def create_embedding_provider() -> EmbeddingProvider:
    """
    Return the configured embedding provider.
    To add a new provider:
      1. Create app/embeddings/<name>_provider.py implementing EmbeddingProvider
      2. Add a branch below
      3. Set EMBEDDING_PROVIDER=<name> in .env
    """
    provider = settings.embedding_provider.lower()

    if provider == "openai":
        from app.embeddings.openai_provider import OpenAIEmbeddingProvider
        return OpenAIEmbeddingProvider()

    if provider == "ollama":
        from app.embeddings.ollama_provider import OllamaEmbeddingProvider
        return OllamaEmbeddingProvider()

    raise ValueError(
        f"Unknown embedding provider: '{provider}'. "
        f"Supported values: openai, ollama"
    )
