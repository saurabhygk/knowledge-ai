from __future__ import annotations

import structlog

from app.embeddings.base import EmbeddingProvider
from app.llm.base import LLMProvider
from app.models.schemas import AskResponse, SearchResult
from app.services.search_service import SearchService

log = structlog.get_logger()

_SYSTEM_PROMPT = """\
You are a helpful assistant that answers questions strictly based on the provided context.

Rules:
- Answer only from the context below. Do not use outside knowledge.
- If the context does not contain enough information, say "I could not find a clear answer in the provided documents."
- Be concise and direct. Quote the relevant part of the document when it helps.
- Do not make up information.
"""


class AskService:
    def __init__(
        self,
        search_service: SearchService,
        llm: LLMProvider,
    ):
        self._search = search_service
        self._llm = llm

    async def ask(self, tenant_slug: str, question: str, top_k: int = 5, min_score: float = 0.5) -> AskResponse:
        # Step 1: retrieve relevant chunks above the confidence threshold
        search_resp = await self._search.search(tenant_slug, question, top_k, min_score)

        if not search_resp.results:
            return AskResponse(
                question=question,
                answer="I could not find any relevant content in the documents for this tenant.",
                sources=[],
                llm_provider=self._llm.provider_name,
            )

        # Step 2: build context from retrieved chunks
        context_parts = []
        for i, result in enumerate(search_resp.results, 1):
            context_parts.append(
                f"[Source {i} — {result.filename}, chunk {result.chunk_index}]\n{result.chunk_text}"
            )
        context = "\n\n".join(context_parts)

        user_message = f"Context:\n{context}\n\nQuestion: {question}"

        log.info("ask_generating", tenant=tenant_slug, provider=self._llm.provider_name, sources=len(search_resp.results))

        # Step 3: generate answer
        answer = await self._llm.complete(_SYSTEM_PROMPT, user_message)

        log.info("ask_complete", tenant=tenant_slug, answer_length=len(answer))
        return AskResponse(
            question=question,
            answer=answer,
            sources=search_resp.results,
            llm_provider=self._llm.provider_name,
        )
