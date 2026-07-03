from __future__ import annotations

import json

import asyncpg
import structlog

from app.embeddings.base import EmbeddingProvider
from app.models.schemas import SearchResponse, SearchResult

log = structlog.get_logger()


class SearchService:
    def __init__(self, pool: asyncpg.Pool, embedder: EmbeddingProvider):
        self._pool = pool
        self._embedder = embedder

    async def search(
        self, tenant_slug: str, query: str, top_k: int = 5, min_score: float = 0.5
    ) -> SearchResponse:
        tenant = await self._pool.fetchrow(
            "SELECT id FROM tenants WHERE slug = $1", tenant_slug
        )
        if not tenant:
            raise KeyError(f"Tenant not found: {tenant_slug}")

        log.info("search_start", tenant=tenant_slug, provider=self._embedder.provider_name, query=query[:80])

        embedding = await self._embedder.embed(query)
        vector_literal = "[" + ",".join(str(v) for v in embedding) + "]"
        # (1 - cosine_distance) = cosine_similarity; filter below threshold before returning
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
