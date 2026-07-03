import asyncio

import structlog
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from openai import AsyncOpenAI, RateLimitError, APIConnectionError

from app.embeddings.base import EmbeddingProvider
from app.config import settings

log = structlog.get_logger()

# Reduced from 512 — free-tier keys have ~1 TPM quota, smaller batches avoid 429s
_MAX_BATCH = 50
# Pause between batches to stay under TPM limits
_INTER_BATCH_SLEEP = 1.0


class OpenAIEmbeddingProvider(EmbeddingProvider):

    def __init__(self):
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_embedding_model
        # text-embedding-3-small → 1536 dims, text-embedding-3-large → 3072 dims
        self._dims = 3072 if "large" in self._model else 1536

    @property
    def dimensions(self) -> int:
        return self._dims

    @property
    def model_name(self) -> str:
        return self._model

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        all_embeddings: list[list[float]] = []

        # Process in batches; sleep between each to respect TPM limits
        for i in range(0, len(texts), _MAX_BATCH):
            batch = texts[i : i + _MAX_BATCH]
            embeddings = await self._embed_batch(batch)
            all_embeddings.extend(embeddings)
            log.debug("embedded_batch",
                      batch_num=i // _MAX_BATCH + 1,
                      batch_size=len(batch),
                      total=len(texts))
            if i + _MAX_BATCH < len(texts):
                await asyncio.sleep(_INTER_BATCH_SLEEP)

        return all_embeddings

    @retry(
        retry=retry_if_exception_type((RateLimitError, APIConnectionError)),
        wait=wait_exponential(multiplier=2, min=5, max=120),
        stop=stop_after_attempt(6),
    )
    async def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        response = await self._client.embeddings.create(
            model=self._model,
            input=texts,
            encoding_format="float",
        )
        return [item.embedding for item in sorted(response.data, key=lambda x: x.index)]
