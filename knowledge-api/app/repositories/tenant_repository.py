from __future__ import annotations

from typing import Any

import asyncpg
import structlog

log = structlog.get_logger()


class TenantRepository:
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def create(self, name: str, slug: str) -> dict[str, Any]:
        try:
            row = await self._pool.fetchrow(
                """
                INSERT INTO tenants (name, slug)
                VALUES ($1, $2)
                RETURNING id, name, slug, created_at
                """,
                name, slug,
            )
        except asyncpg.UniqueViolationError:
            raise ValueError(f"Tenant with slug '{slug}' already exists")
        log.info("tenant_created", slug=slug)
        return dict(row)

    async def list_all(self) -> list[dict[str, Any]]:
        rows = await self._pool.fetch(
            "SELECT id, name, slug, created_at FROM tenants ORDER BY created_at DESC"
        )
        return [dict(r) for r in rows]
