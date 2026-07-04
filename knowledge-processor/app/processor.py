import structlog
from langchain_core.embeddings import Embeddings

from app.chunking.base import ChunkingStrategy
from app.db.repository import DocumentRepository
from app.parsers.base import DocumentParser
from app.storage.minio_client import MinioStorageClient

log = structlog.get_logger()


class DocumentProcessor:
    """
    Orchestrates the full data pipeline for a single document:
        download → parse → chunk → embed → store → mark indexed
    """

    def __init__(
        self,
        parser: DocumentParser,
        chunker: ChunkingStrategy,
        embedder: Embeddings,
        storage: MinioStorageClient,
        repo: DocumentRepository,
    ):
        self._parser = parser
        self._chunker = chunker
        self._embedder = embedder
        self._storage = storage
        self._repo = repo

    async def process(
        self,
        document_id: str,
        tenant_id: str,
        storage_key: str,
        content_type: str,
        filename: str = "",
    ) -> None:
        log.info("processing_start", document_id=document_id, storage_key=storage_key)

        await self._repo.mark_processing(document_id)

        try:
            # Step 1: Download raw file from MinIO
            file_bytes = self._storage.download(storage_key)

            # Step 2: Extract text + structure
            parsed = self._parser.parse(file_bytes, filename or storage_key.split("/")[-1])

            if not parsed.text.strip():
                raise ValueError("Document produced no extractable text")

            # Step 3: Chunk
            base_metadata = {
                "document_id": document_id,
                "tenant_id": tenant_id,
                "filename": parsed.metadata.get("filename", ""),
                "page_count": parsed.metadata.get("page_count", 0),
            }
            chunks = self._chunker.chunk(parsed, base_metadata)

            if not chunks:
                raise ValueError("Chunking produced no chunks")

            # Step 4: Embed all chunks.
            # aembed_documents is LangChain's async batch embedding method.
            # For OpenAI it handles batching and rate-limit retry internally.
            # For Ollama it loops sequentially (local, no rate limits).
            texts = [c.text for c in chunks]
            embeddings = await self._embedder.aembed_documents(texts)

            # Step 5: Persist — delete old data first (supports re-indexing)
            await self._repo.delete_vectors(document_id)
            await self._repo.delete_chunks(document_id)
            await self._repo.save_chunks(document_id, tenant_id, chunks)
            await self._repo.save_vectors(chunks, embeddings, document_id, tenant_id)

            # Step 6: Mark done
            await self._repo.mark_indexed(document_id)

            log.info("processing_complete",
                     document_id=document_id,
                     chunk_count=len(chunks),
                     embedding_provider=type(self._embedder).__name__)

        except Exception as exc:
            log.error("processing_failed", document_id=document_id, error=str(exc), exc_info=True)
            await self._repo.mark_failed(document_id, str(exc))
            raise
