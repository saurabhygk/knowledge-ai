from __future__ import annotations
import httpx
from app.config import settings
from app.llm.base import LLMProvider


class OllamaLLMProvider(LLMProvider):
    def __init__(self):
        self._base_url = settings.ollama_base_url.rstrip("/")
        self._model = settings.ollama_chat_model

    @property
    def provider_name(self) -> str:
        return f"ollama/{self._model}"

    async def complete(self, system_prompt: str, user_message: str) -> str:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{self._base_url}/api/chat",
                json={
                    "model": self._model,
                    "stream": False,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                },
            )
            resp.raise_for_status()
            return resp.json()["message"]["content"].strip()
