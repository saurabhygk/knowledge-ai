from __future__ import annotations
from openai import AsyncOpenAI
from app.config import settings
from app.embeddings.base import EmbeddingProvider


class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self):
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_embedding_model

    @property
    def provider_name(self) -> str:
        return f"openai/{self._model}"

    async def embed(self, text: str) -> list[float]:
        resp = await self._client.embeddings.create(
            model=self._model,
            input=[text],
            encoding_format="float",
        )
        return resp.data[0].embedding
