from __future__ import annotations
from app.config import settings
from app.llm.base import LLMProvider


def create_llm_provider() -> LLMProvider:
    """
    Return the configured LLM provider.
    To add a new provider:
      1. Create app/llm/<name>_provider.py implementing LLMProvider
      2. Add a branch below
      3. Set LLM_PROVIDER=<name> in .env
    """
    provider = settings.llm_provider.lower()

    if provider == "ollama":
        from app.llm.ollama_provider import OllamaLLMProvider
        return OllamaLLMProvider()

    if provider == "openai":
        from app.llm.openai_provider import OpenAILLMProvider
        return OpenAILLMProvider()

    raise ValueError(
        f"Unknown LLM provider: '{provider}'. "
        f"Supported values: ollama, openai"
    )
