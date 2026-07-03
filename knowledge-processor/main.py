"""
Entry point for the knowledge-processor service.

Starts two things concurrently:
  1. FastAPI HTTP server (health check + future admin endpoints)
  2. Redis Stream consumer loop (the actual processing worker)
"""
import asyncio
import contextlib
import structlog
import uvicorn
from fastapi import FastAPI

from app.config import settings
from app.consumer import RedisStreamConsumer
from app.dependencies import create_db_pool, create_processor
from app.logging_config import configure_logging

configure_logging()
log = structlog.get_logger()

# ---------------------------------------------------------------------------
# FastAPI app (health check + future admin endpoints)
# ---------------------------------------------------------------------------
app = FastAPI(title="knowledge-processor", version="0.1.0")

_consumer: RedisStreamConsumer | None = None


@app.get("/health")
async def health():
    return {"status": "ok", "consumer_running": _consumer is not None}


@app.get("/ready")
async def ready():
    return {"status": "ready"}


# ---------------------------------------------------------------------------
# Lifespan — wire up DB pool and consumer
# ---------------------------------------------------------------------------
@contextlib.asynccontextmanager
async def lifespan(application: FastAPI):
    global _consumer

    log.info("startup", embedding_provider=settings.embedding_provider,
             chunking_strategy=settings.chunking_strategy)

    pool = await create_db_pool()
    processor = create_processor(pool)
    _consumer = RedisStreamConsumer(processor)

    # Run consumer in the background alongside the HTTP server
    consumer_task = asyncio.create_task(_consumer.start(), name="redis-consumer")

    yield  # app is running

    log.info("shutdown")
    await _consumer.stop()
    consumer_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await consumer_task
    await pool.close()


app.router.lifespan_context = lifespan


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=False,
        log_level=settings.log_level.lower(),
    )
