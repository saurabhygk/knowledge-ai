from __future__ import annotations

from langchain_core.language_models import BaseChatModel

from app.config import settings


def create_llm_provider() -> tuple[BaseChatModel, str]:
    """
    Return a (LangChain BaseChatModel instance, human-readable name) pair.

    WHY BaseChatModel? It is LangChain's universal interface for any chat LLM.
    Every provider — OpenAI, Anthropic, Ollama, Bedrock, Cohere — implements it.
    The caller never needs to know which concrete class it is.

    To add a new provider:
      1. pip install langchain-<provider>
      2. Add a branch below
      3. Set LLM_PROVIDER=<value> in .env — no other code changes needed.
    """
    provider = settings.llm_provider.lower()

    if provider == "ollama":
        from langchain_ollama import ChatOllama
        llm = ChatOllama(
            model=settings.ollama_chat_model,
            base_url=settings.ollama_base_url,
        )
        return llm, f"ollama/{settings.ollama_chat_model}"

    if provider == "openai":
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(
            model=settings.openai_chat_model,
            api_key=settings.openai_api_key,
            temperature=0.2,
        )
        return llm, f"openai/{settings.openai_chat_model}"

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        llm = ChatAnthropic(
            model=settings.anthropic_chat_model,
            api_key=settings.anthropic_api_key,
            temperature=0.2,
        )
        return llm, f"anthropic/{settings.anthropic_chat_model}"

    raise ValueError(
        f"Unknown LLM provider: '{provider}'. "
        f"Supported values: ollama, openai, anthropic"
    )
