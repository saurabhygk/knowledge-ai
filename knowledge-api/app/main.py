from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.database import create_pool, close_pool, get_pool
from app.events.processing_producer import create_redis_client, close_redis_client
from app.logging_config import configure_logging
from app.repositories.document_repository import DocumentRepository
from app.services.document_service import DocumentService
from app.services.storage_service import StorageService
from app.routers.documents import router as documents_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    await create_pool()
    await create_redis_client()

    pool = get_pool()
    storage = StorageService()
    repo = DocumentRepository(pool)
    app.state.document_service = DocumentService(repo, storage)

    yield

    await close_pool()
    await close_redis_client()


app = FastAPI(
    title="KnowledgeAI API",
    description="Document management and RAG pipeline",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(documents_router)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    import structlog
    log = structlog.get_logger()
    log.error("unhandled_exception", error=str(exc), path=request.url.path, exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "An unexpected error occurred"})


@app.get("/health")
async def health():
    return {"status": "ok"}
