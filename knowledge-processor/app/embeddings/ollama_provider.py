import structlog
import httpx

from app.embeddings.base import EmbeddingProvider
from app.config import settings

log = structlog.get_logger()

# Ollama processes one text at a time — batch sequentially
_OLLAMA_DIMS = {
    "nomic-embed-text": 768,
    "mxbai-embed-large": 1024,
    "all-minilm": 384,
}


class OllamaEmbeddingProvider(EmbeddingProvider):
    """
    Local embedding via Ollama — zero cost, works offline.
    Default model: nomic-embed-text (768 dims, strong quality).

    Note: dimensions differ from OpenAI — you cannot mix providers
    on the same vector_store table without re-indexing.
    """

    def __init__(self):
        self._base_url = settings.ollama_base_url.rstrip("/")
        self._model = settings.ollama_embedding_model
        self._dims = _OLLAMA_DIMS.get(self._model, 768)

    @property
    def dimensions(self) -> int:
        return self._dims

    @property
    def model_name(self) -> str:
        return self._model

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        results: list[list[float]] = []
        async with httpx.AsyncClient(timeout=60.0) as client:
            for text in texts:
                response = await client.post(
                    f"{self._base_url}/api/embeddings",
                    json={"model": self._model, "prompt": text},
                )
                response.raise_for_status()
                results.append(response.json()["embedding"])
        return results
