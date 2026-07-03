from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    @abstractmethod
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts. Returns one vector per input text."""
        ...

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Number of dimensions in the output vectors."""
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        ...
