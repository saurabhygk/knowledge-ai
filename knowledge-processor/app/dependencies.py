"""
Wires all components together.  Called once at startup.
"""
import asyncpg
import structlog

from app.config import settings
from app.chunking.base import ChunkingStrategy
from app.chunking.recursive_chunker import RecursiveChunker
from app.chunking.element_aware_chunker import ElementAwareChunker
from app.db.repository import DocumentRepository
from app.embeddings.base import EmbeddingProvider
from app.embeddings.openai_provider import OpenAIEmbeddingProvider
from app.embeddings.ollama_provider import OllamaEmbeddingProvider
from app.parsers.base import DocumentParser
from app.parsers.unstructured_parser import UnstructuredParser
from app.processor import DocumentProcessor
from app.storage.minio_client import MinioStorageClient

log = structlog.get_logger()


async def create_db_pool() -> asyncpg.Pool:
    return await asyncpg.create_pool(
        dsn=settings.database_url,
        min_size=2,
        max_size=10,
    )


def create_parser() -> DocumentParser:
    return UnstructuredParser()


def create_chunker() -> ChunkingStrategy:
    if settings.chunking_strategy == "element_aware":
        return ElementAwareChunker(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
    return RecursiveChunker(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )


def create_embedder() -> EmbeddingProvider:
    if settings.embedding_provider == "ollama":
        log.info("using_ollama_embeddings", model=settings.ollama_embedding_model)
        return OllamaEmbeddingProvider()
    log.info("using_openai_embeddings", model=settings.openai_embedding_model)
    return OpenAIEmbeddingProvider()


def create_processor(pool: asyncpg.Pool) -> DocumentProcessor:
    return DocumentProcessor(
        parser=create_parser(),
        chunker=create_chunker(),
        embedder=create_embedder(),
        storage=MinioStorageClient(),
        repo=DocumentRepository(pool),
    )
