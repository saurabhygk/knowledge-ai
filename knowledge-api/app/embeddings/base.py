from __future__ import annotations
from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Embed a single query string and return its vector."""
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        ...
