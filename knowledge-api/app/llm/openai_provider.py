from __future__ import annotations
from openai import AsyncOpenAI
from app.config import settings
from app.llm.base import LLMProvider


class OpenAILLMProvider(LLMProvider):
    def __init__(self):
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_chat_model

    @property
    def provider_name(self) -> str:
        return f"openai/{self._model}"

    async def complete(self, system_prompt: str, user_message: str, history: list[dict] | None = None) -> str:
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_message})
        resp = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=0.2,
        )
        return resp.choices[0].message.content.strip()
