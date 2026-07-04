"""
Wires all components together. Called once at startup.
"""
import asyncpg
import structlog
from langchain_core.embeddings import Embeddings

from app.config import settings
from app.chunking.base import ChunkingStrategy
from app.chunking.recursive_chunker import RecursiveChunker
from app.chunking.element_aware_chunker import ElementAwareChunker
from app.db.repository import DocumentRepository
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


def create_embedder() -> tuple[Embeddings, str]:
    """
    Return a (LangChain Embeddings instance, human-readable name) pair.
    Set EMBEDDING_PROVIDER in .env to switch providers — no code changes needed.
    """
    provider = settings.embedding_provider.lower()

    if provider == "ollama":
        from langchain_ollama import OllamaEmbeddings
        log.info("using_ollama_embeddings", model=settings.ollama_embedding_model)
        emb = OllamaEmbeddings(
            model=settings.ollama_embedding_model,
            base_url=settings.ollama_base_url,
        )
        return emb, f"ollama/{settings.ollama_embedding_model}"

    from langchain_openai import OpenAIEmbeddings
    log.info("using_openai_embeddings", model=settings.openai_embedding_model)
    emb = OpenAIEmbeddings(
        model=settings.openai_embedding_model,
        api_key=settings.openai_api_key,
    )
    return emb, f"openai/{settings.openai_embedding_model}"


def create_processor(pool: asyncpg.Pool) -> DocumentProcessor:
    embedder, _ = create_embedder()
    return DocumentProcessor(
        parser=create_parser(),
        chunker=create_chunker(),
        embedder=embedder,
        storage=MinioStorageClient(),
        repo=DocumentRepository(pool),
    )
