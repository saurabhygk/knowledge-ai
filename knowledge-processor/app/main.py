"""
knowledge-processor worker entry point.

Run with:  python -m app.main
"""
from __future__ import annotations

import asyncio
import signal

import asyncpg
import redis.asyncio as aioredis
import structlog
from langchain_core.embeddings import Embeddings

from app.config import settings
from app.db.repository import DocumentRepository
from app.logging_config import configure_logging
from app.parsers.unstructured_parser import UnstructuredParser
from app.processor import DocumentProcessor
from app.storage.minio_client import MinioStorageClient

log = structlog.get_logger()


async def _sync_vector_dimensions(pool: asyncpg.Pool, embedder: Embeddings) -> None:
    """
    Detect the embedding dimension by running a probe embed, then check whether
    the vector_store column matches. If not, resize it automatically.

    WHY a probe embed instead of a hardcoded dimension map?
    Any future provider works without updating a lookup table — the dimension
    is measured directly from the provider's actual output.
    """
    test_vec = await embedder.aembed_query("ping")
    required_dims = len(test_vec)

    current_dims = await pool.fetchval(
        """
        SELECT atttypmod
        FROM pg_attribute
        WHERE attrelid = 'vector_store'::regclass
          AND attname = 'embedding'
          AND attnum > 0
        """
    )

    if current_dims == required_dims:
        log.info("vector_dimensions_ok", dims=required_dims)
        return

    log.warning(
        "vector_dimension_mismatch",
        current=current_dims,
        required=required_dims,
        action="resizing column and clearing stale vectors",
    )

    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("DROP INDEX IF EXISTS idx_vector_store_hnsw")
            await conn.execute("DELETE FROM vector_store")
            await conn.execute("ALTER TABLE vector_store DROP COLUMN IF EXISTS embedding")
            await conn.execute(f"ALTER TABLE vector_store ADD COLUMN embedding VECTOR({required_dims})")
            await conn.execute("""
                CREATE INDEX idx_vector_store_hnsw
                    ON vector_store USING hnsw (embedding vector_cosine_ops)
                    WITH (m = 16, ef_construction = 64)
            """)

    log.info("vector_dimensions_updated", dims=required_dims)


def _build_processor(pool: asyncpg.Pool) -> tuple[DocumentProcessor, Embeddings]:
    from app.dependencies import create_embedder, create_chunker

    embedder, embedder_name = create_embedder()
    chunker = create_chunker()
    log.info("embedder_loaded", provider=embedder_name)

    processor = DocumentProcessor(
        parser=UnstructuredParser(),
        chunker=chunker,
        embedder=embedder,
        storage=MinioStorageClient(),
        repo=DocumentRepository(pool),
    )
    return processor, embedder


async def _ensure_consumer_group(client: aioredis.Redis) -> None:
    try:
        await client.xgroup_create(
            settings.redis_stream,
            settings.redis_consumer_group,
            id="0",
            mkstream=True,
        )
        log.info("consumer_group_created", group=settings.redis_consumer_group)
    except aioredis.ResponseError as e:
        if "BUSYGROUP" not in str(e):
            raise


async def _process_message(processor: DocumentProcessor, fields: dict) -> None:
    document_id = fields.get("document_id", "")
    tenant_id = fields.get("tenant_id", "")
    storage_key = fields.get("storage_key", "")
    content_type = fields.get("content_type") or None
    filename = storage_key.split("/")[-1] if storage_key else ""

    await processor.process(
        document_id=document_id,
        tenant_id=tenant_id,
        storage_key=storage_key,
        content_type=content_type,
        filename=filename,
    )


async def run_worker() -> None:
    configure_logging()
    log.info("worker_starting",
             stream=settings.redis_stream,
             group=settings.redis_consumer_group,
             consumer=settings.redis_consumer_name)

    pool = await asyncpg.create_pool(settings.database_url, min_size=2, max_size=5)
    redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    processor, embedder = _build_processor(pool)

    # Auto-detect dimensions from a probe embed and resize DB column if needed.
    await _sync_vector_dimensions(pool, embedder)
    await _ensure_consumer_group(redis_client)
    log.info("worker_ready")

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)

    try:
        while not stop.is_set():
            results = await redis_client.xreadgroup(
                groupname=settings.redis_consumer_group,
                consumername=settings.redis_consumer_name,
                streams={settings.redis_stream: ">"},
                count=settings.redis_batch_size,
                block=settings.redis_block_ms,
            )

            if not results:
                continue

            for _stream, messages in results:
                for msg_id, fields in messages:
                    log.info("message_received", msg_id=msg_id, document_id=fields.get("document_id"))
                    try:
                        await _process_message(processor, fields)
                        await redis_client.xack(
                            settings.redis_stream,
                            settings.redis_consumer_group,
                            msg_id,
                        )
                        log.info("message_acked", msg_id=msg_id)
                    except Exception as exc:
                        log.error("message_failed", msg_id=msg_id, error=str(exc), exc_info=True)
    finally:
        log.info("worker_stopping")
        await redis_client.aclose()
        await pool.close()


if __name__ == "__main__":
    asyncio.run(run_worker())
