import json
import uuid
from datetime import datetime, timezone

import asyncpg
import structlog

from app.chunking.base import Chunk

log = structlog.get_logger()


class DocumentRepository:
    """
    All PostgreSQL operations for the processor.

    We use asyncpg directly (not an ORM) — the processor only needs
    a handful of write operations and performance matters here.
    """

    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    # -------------------------------------------------------------------------
    # Document status lifecycle
    # -------------------------------------------------------------------------

    async def mark_processing(self, document_id: str) -> None:
        await self._pool.execute(
            "UPDATE documents SET status = 'PROCESSING' WHERE id = $1",
            uuid.UUID(document_id),
        )

    async def mark_indexed(self, document_id: str) -> None:
        await self._pool.execute(
            "UPDATE documents SET status = 'INDEXED', indexed_at = $2 WHERE id = $1",
            uuid.UUID(document_id),
            datetime.now(timezone.utc),
        )

    async def mark_failed(self, document_id: str, error: str) -> None:
        await self._pool.execute(
            "UPDATE documents SET status = 'FAILED', error_message = $2 WHERE id = $1",
            uuid.UUID(document_id),
            error[:2048],
        )

    # -------------------------------------------------------------------------
    # Chunks
    # -------------------------------------------------------------------------

    async def delete_chunks(self, document_id: str) -> None:
        """Remove old chunks before re-indexing an updated document."""
        await self._pool.execute(
            "DELETE FROM chunks WHERE document_id = $1",
            uuid.UUID(document_id),
        )

    async def save_chunks(self, document_id: str, tenant_id: str, chunks: list[Chunk]) -> None:
        doc_uuid = uuid.UUID(document_id)
        tenant_uuid = uuid.UUID(tenant_id)

        records = [
            (
                uuid.uuid4(),
                doc_uuid,
                tenant_uuid,
                c.chunk_index,
                c.text,
                c.char_start,
                c.char_end,
                json.dumps(c.metadata),
            )
            for c in chunks
        ]

        await self._pool.executemany(
            """
            INSERT INTO chunks
                (id, document_id, tenant_id, chunk_index, text, char_start, char_end, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb)
            """,
            records,
        )
        log.info("saved_chunks", document_id=document_id, count=len(chunks))

    # -------------------------------------------------------------------------
    # Vector store (Spring AI pgvector format)
    # -------------------------------------------------------------------------

    async def delete_vectors(self, document_id: str) -> None:
        """Remove old vectors — called before re-indexing."""
        await self._pool.execute(
            "DELETE FROM vector_store WHERE metadata->>'document_id' = $1",
            document_id,
        )

    async def save_vectors(
        self,
        chunks: list[Chunk],
        embeddings: list[list[float]],
        document_id: str,
        tenant_id: str,
    ) -> None:
        """
        Write chunks + embeddings into the Spring AI vector_store table.
        Metadata stored here is what the retrieval side will filter on.
        """
        assert len(chunks) == len(embeddings), "chunks/embeddings length mismatch"

        records = []
        for chunk, embedding in zip(chunks, embeddings):
            vector_meta = {
                **chunk.metadata,
                "document_id": document_id,
                "tenant_id": tenant_id,
                "chunk_index": chunk.chunk_index,
            }
            records.append((
                uuid.uuid4(),
                chunk.text,
                json.dumps(vector_meta),
                # pgvector expects a string like '[0.1,0.2,...]'
                "[" + ",".join(str(v) for v in embedding) + "]",
            ))

        await self._pool.executemany(
            """
            INSERT INTO vector_store (id, content, metadata, embedding)
            VALUES ($1, $2, $3::jsonb, $4::vector)
            """,
            records,
        )
        log.info("saved_vectors", document_id=document_id, count=len(records))
