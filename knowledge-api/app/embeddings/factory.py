from __future__ import annotations

from langchain_core.embeddings import Embeddings

from app.config import settings


def create_embedding_provider() -> tuple[Embeddings, str]:
    """
    Return a (LangChain Embeddings instance, human-readable name) pair.

    WHY a tuple? The LangChain Embeddings interface has no standard .provider_name
    property, so we carry the name alongside the object for logging and API responses.

    To add a new provider:
      1. pip install langchain-<provider>
      2. Add a branch below
      3. Set EMBEDDING_PROVIDER=<value> in .env — no other code changes needed.
    """
    provider = settings.embedding_provider.lower()

    if provider == "openai":
        from langchain_openai import OpenAIEmbeddings
        emb = OpenAIEmbeddings(
            model=settings.openai_embedding_model,
            api_key=settings.openai_api_key,
        )
        return emb, f"openai/{settings.openai_embedding_model}"

    if provider == "ollama":
        from langchain_ollama import OllamaEmbeddings
        emb = OllamaEmbeddings(
            model=settings.ollama_embedding_model,
            base_url=settings.ollama_base_url,
        )
        return emb, f"ollama/{settings.ollama_embedding_model}"

    raise ValueError(
        f"Unknown embedding provider: '{provider}'. "
        f"Supported values: openai, ollama"
    )
