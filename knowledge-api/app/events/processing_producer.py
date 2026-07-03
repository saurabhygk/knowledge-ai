from __future__ import annotations

import redis.asyncio as redis
import structlog

from app.config import settings

log = structlog.get_logger()

_client: redis.Redis | None = None


async def create_redis_client() -> redis.Redis:
    global _client
    _client = redis.from_url(settings.redis_url, decode_responses=True)
    return _client


async def close_redis_client() -> None:
    global _client
    if _client:
        await _client.aclose()
        _client = None


def get_redis_client() -> redis.Redis:
    if _client is None:
        raise RuntimeError("Redis client not initialised")
    return _client


async def publish_processing_event(
    document_id: str,
    tenant_id: str,
    storage_key: str,
    content_type: str | None,
) -> None:
    client = get_redis_client()
    await client.xadd(settings.redis_stream, {
        "document_id": document_id,
        "tenant_id": tenant_id,
        "storage_key": storage_key,
        "content_type": content_type or "",
    })
    log.info("published_processing_event", document_id=document_id)
