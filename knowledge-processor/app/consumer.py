import asyncio
import json
import structlog
import redis.asyncio as aioredis

from app.config import settings
from app.processor import DocumentProcessor

log = structlog.get_logger()


class RedisStreamConsumer:
    """
    Consumes ProcessingEvent messages from the Redis Stream published
    by knowledge-api and runs DocumentProcessor for each one.

    Uses consumer groups so multiple processor instances can share load
    and unprocessed messages survive restarts.
    """

    def __init__(self, processor: DocumentProcessor):
        self._processor = processor
        self._redis: aioredis.Redis | None = None
        self._running = False

    async def start(self) -> None:
        self._redis = await aioredis.from_url(settings.redis_url, decode_responses=True)
        await self._ensure_group_exists()
        self._running = True
        log.info("consumer_started",
                 stream=settings.redis_stream,
                 group=settings.redis_consumer_group,
                 consumer=settings.redis_consumer_name)
        await self._consume_loop()

    async def stop(self) -> None:
        self._running = False
        if self._redis:
            await self._redis.aclose()

    async def _ensure_group_exists(self) -> None:
        try:
            await self._redis.xgroup_create(
                name=settings.redis_stream,
                groupname=settings.redis_consumer_group,
                id="0",           # start from the beginning
                mkstream=True,    # create stream if it doesn't exist yet
            )
            log.info("consumer_group_created", group=settings.redis_consumer_group)
        except aioredis.ResponseError as e:
            if "BUSYGROUP" in str(e):
                log.debug("consumer_group_exists", group=settings.redis_consumer_group)
            else:
                raise

    async def _consume_loop(self) -> None:
        while self._running:
            try:
                messages = await self._redis.xreadgroup(
                    groupname=settings.redis_consumer_group,
                    consumername=settings.redis_consumer_name,
                    streams={settings.redis_stream: ">"},   # ">" = only undelivered messages
                    count=settings.redis_batch_size,
                    block=settings.redis_block_ms,
                )

                if not messages:
                    continue

                for stream_name, entries in messages:
                    for msg_id, fields in entries:
                        await self._handle_message(msg_id, fields)

            except aioredis.RedisError as e:
                log.error("redis_error", error=str(e))
                await asyncio.sleep(5)
            except asyncio.CancelledError:
                break

    async def _handle_message(self, msg_id: str, fields: dict) -> None:
        log.info("message_received", msg_id=msg_id, fields=fields)

        try:
            # Fields arrive as flat strings from the stream
            document_id  = fields.get("documentId") or fields.get("document_id", "")
            tenant_id    = fields.get("tenantId")   or fields.get("tenant_id", "")
            storage_key  = fields.get("storageKey") or fields.get("storage_key", "")
            content_type = fields.get("contentType") or fields.get("content_type", "application/octet-stream")

            if not all([document_id, tenant_id, storage_key]):
                raise ValueError(f"Missing required fields in event: {fields}")

            await self._processor.process(
                document_id=document_id,
                tenant_id=tenant_id,
                storage_key=storage_key,
                content_type=content_type,
            )

            # ACK on success so the message is removed from the pending list
            await self._redis.xack(
                settings.redis_stream,
                settings.redis_consumer_group,
                msg_id,
            )
            log.info("message_acked", msg_id=msg_id)

        except Exception as exc:
            # Do NOT ack — message stays in pending list for retry / dead-letter handling
            log.error("message_processing_failed",
                      msg_id=msg_id,
                      error=str(exc),
                      exc_info=True)
