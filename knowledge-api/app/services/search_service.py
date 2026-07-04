from __future__ import annotations

import json

import asyncpg
import structlog
from langchain_core.embeddings import Embeddings

from app.models.schemas import SearchResponse, SearchResult

log = structlog.get_logger()


class SearchService:
    def __init__(self, pool: asyncpg.Pool, embedder: Embeddings, embedder_name: str = ""):
        self._pool = pool
        self._embedder = embedder
        self._embedder_name = embedder_name

    async def search(
        self, tenant_slug: str, query: str, top_k: int = 5, min_score: float = 0.5
    ) -> SearchResponse:
        tenant = await self._pool.fetchrow(
            "SELECT id FROM tenants WHERE slug = $1", tenant_slug
        )
        if not tenant:
            raise KeyError(f"Tenant not found: {tenant_slug}")

        log.info("search_start", tenant=tenant_slug, provider=self._embedder_name, query=query[:80])

        # aembed_query is LangChain's async method for embedding a single string.
        # Identical result to the old embedder.embed() — just through LangChain's interface.
        embedding = await self._embedder.aembed_query(query)
        vector_literal = "[" + ",".join(str(v) for v in embedding) + "]"
        similarity_threshold = 1 - min_score

        rows = await self._pool.fetch(
            """
            SELECT
                vs.content                         AS chunk_text,
                1 - (vs.embedding <=> $1::vector)  AS score,
                vs.metadata
            FROM vector_store vs
            WHERE vs.metadata->>'tenant_id' = $2
              AND (vs.embedding <=> $1::vector) <= $4
            ORDER BY vs.embedding <=> $1::vector
            LIMIT $3
            """,
            vector_literal,
            str(tenant["id"]),
            top_k,
            similarity_threshold,
        )

        results = []
        for row in rows:
            meta = row["metadata"]
            if isinstance(meta, str):
                meta = json.loads(meta)
            results.append(SearchResult(
                chunk_text=row["chunk_text"],
                score=round(float(row["score"]), 4),
                document_id=meta.get("document_id", ""),
                filename=meta.get("filename", ""),
                chunk_index=meta.get("chunk_index", 0),
                metadata=meta,
            ))

        log.info("search_complete", tenant=tenant_slug, result_count=len(results), min_score=min_score)
        return SearchResponse(query=query, results=results)
