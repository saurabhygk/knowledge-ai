from __future__ import annotations
from abc import ABC, abstractmethod


class LLMProvider(ABC):
    @abstractmethod
    async def complete(self, system_prompt: str, user_message: str, history: list[dict] | None = None) -> str:
        """Send a prompt with optional conversation history and return the model's text response."""
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        ...
