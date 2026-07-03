import uuid
from typing import Any
import asyncpg
import structlog

log = structlog.get_logger()


class DocumentRepository:
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def get_tenant_by_slug(self, slug: str) -> dict[str, Any] | None:
        row = await self._pool.fetchrow(
            "SELECT id, name, slug, created_at FROM tenants WHERE slug = $1", slug
        )
        return dict(row) if row else None

    async def create_document(
        self,
        tenant_id: uuid.UUID,
        filename: str,
        content_type: str | None,
        storage_key: str,
    ) -> dict[str, Any]:
        row = await self._pool.fetchrow(
            """
            INSERT INTO documents (tenant_id, filename, content_type, storage_key, status, metadata)
            VALUES ($1, $2, $3, $4, 'UPLOADED', '{}')
            RETURNING id, tenant_id, filename, content_type, storage_key, status,
                      metadata, error_message, created_at, indexed_at
            """,
            tenant_id, filename, content_type, storage_key,
        )
        return dict(row)

    async def list_documents(
        self, tenant_id: uuid.UUID, page: int, size: int
    ) -> tuple[list[dict[str, Any]], int]:
        offset = (page - 1) * size
        rows = await self._pool.fetch(
            """
            SELECT id, tenant_id, filename, content_type, storage_key, status,
                   metadata, error_message, created_at, indexed_at
            FROM documents
            WHERE tenant_id = $1
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
            """,
            tenant_id, size, offset,
        )
        total = await self._pool.fetchval(
            "SELECT COUNT(*) FROM documents WHERE tenant_id = $1", tenant_id
        )
        return [dict(r) for r in rows], total

    async def get_document(
        self, document_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> dict[str, Any] | None:
        row = await self._pool.fetchrow(
            """
            SELECT id, tenant_id, filename, content_type, storage_key, status,
                   metadata, error_message, created_at, indexed_at
            FROM documents
            WHERE id = $1 AND tenant_id = $2
            """,
            document_id, tenant_id,
        )
        return dict(row) if row else None
