from __future__ import annotations

import secrets
from typing import Any

import asyncpg
import structlog

log = structlog.get_logger()


class TenantRepository:
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def create(self, name: str, slug: str) -> dict[str, Any]:
        token = secrets.token_hex(16)  # 32-char hex, cryptographically random
        try:
            row = await self._pool.fetchrow(
                """
                INSERT INTO tenants (name, slug, access_token)
                VALUES ($1, $2, $3)
                RETURNING id, name, slug, access_token, created_at
                """,
                name, slug, token,
            )
        except asyncpg.UniqueViolationError:
            raise ValueError(f"Tenant with slug '{slug}' already exists")
        log.info("tenant_created", slug=slug)
        return dict(row)

    async def list_all(self) -> list[dict[str, Any]]:
        rows = await self._pool.fetch(
            "SELECT id, name, slug, access_token, created_at FROM tenants ORDER BY created_at DESC"
        )
        return [dict(r) for r in rows]

    async def get_by_slug(self, slug: str) -> dict[str, Any] | None:
        row = await self._pool.fetchrow(
            "SELECT id, name, slug, access_token, created_at FROM tenants WHERE slug = $1", slug
        )
        return dict(row) if row else None

    async def verify_token(self, slug: str, token: str) -> bool:
        row = await self._pool.fetchrow(
            "SELECT access_token FROM tenants WHERE slug = $1", slug
        )
        if not row:
            return False
        # Use constant-time comparison to prevent timing attacks
        return secrets.compare_digest(row["access_token"], token)
