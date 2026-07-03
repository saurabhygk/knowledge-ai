from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

log = structlog.get_logger()

from app.config import settings
from app.database import close_pool, create_pool, get_pool
from app.events.processing_producer import close_redis_client, create_redis_client
from app.logging_config import configure_logging
from app.embeddings.factory import create_embedding_provider
from app.llm.factory import create_llm_provider
from app.repositories.document_repository import DocumentRepository
from app.repositories.tenant_repository import TenantRepository
from app.routers.ask import router as ask_router
from app.routers.documents import router as documents_router
from app.routers.search import router as search_router
from app.routers.tenants import router as tenants_router
from app.services.ask_service import AskService
from app.services.document_service import DocumentService
from app.services.search_service import SearchService
from app.services.storage_service import StorageService


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    await create_pool()
    await create_redis_client()

    pool = get_pool()
    embedder = create_embedding_provider()
    llm = create_llm_provider()
    log.info("embedding_provider_loaded", provider=embedder.provider_name)
    log.info("llm_provider_loaded", provider=llm.provider_name)

    app.state.tenant_repo = TenantRepository(pool)
    app.state.document_service = DocumentService(
        repo=DocumentRepository(pool),
        storage=StorageService(),
    )
    app.state.search_service = SearchService(pool, embedder)
    app.state.ask_service = AskService(app.state.search_service, llm)

    yield

    await close_pool()
    await close_redis_client()


app = FastAPI(
    title="KnowledgeAI API",
    description="Document management and RAG pipeline",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:4173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tenants_router)
app.include_router(documents_router)
app.include_router(search_router)
app.include_router(ask_router)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    log = structlog.get_logger()
    log.error("unhandled_exception", error=str(exc), path=str(request.url), exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "An unexpected error occurred"})


@app.get("/health", tags=["ops"])
async def health():
    return {"status": "ok"}
