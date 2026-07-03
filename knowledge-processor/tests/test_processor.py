import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.processor import DocumentProcessor
from app.parsers.base import ParsedDocument, PageElement
from app.chunking.base import Chunk


def make_processor(
    parsed_doc=None,
    chunks=None,
    embeddings=None,
):
    parser = MagicMock()
    parser.parse.return_value = parsed_doc or ParsedDocument(
        text="Hello world. This is a test document.",
        elements=[PageElement(page_number=1, text="Hello world.", element_type="NarrativeText")],
    )

    chunker = MagicMock()
    chunker.chunk.return_value = chunks or [
        Chunk(text="Hello world.", chunk_index=0, char_start=0, char_end=12, metadata={})
    ]

    embedder = AsyncMock()
    embedder.embed_texts = AsyncMock(return_value=embeddings or [[0.1] * 1536])
    embedder.model_name = "text-embedding-3-small"

    storage = MagicMock()
    storage.download.return_value = b"fake pdf bytes"

    repo = AsyncMock()

    return DocumentProcessor(
        parser=parser,
        chunker=chunker,
        embedder=embedder,
        storage=storage,
        repo=repo,
    ), repo


@pytest.mark.asyncio
async def test_process_happy_path():
    processor, repo = make_processor()

    await processor.process(
        document_id="00000000-0000-0000-0000-000000000001",
        tenant_id="00000000-0000-0000-0000-000000000002",
        storage_key="tenant/doc/file.pdf",
        content_type="application/pdf",
    )

    repo.mark_processing.assert_awaited_once()
    repo.delete_vectors.assert_awaited_once()
    repo.delete_chunks.assert_awaited_once()
    repo.save_chunks.assert_awaited_once()
    repo.save_vectors.assert_awaited_once()
    repo.mark_indexed.assert_awaited_once()
    repo.mark_failed.assert_not_awaited()


@pytest.mark.asyncio
async def test_process_marks_failed_on_error():
    processor, repo = make_processor()
    processor._storage.download.side_effect = RuntimeError("MinIO down")

    with pytest.raises(RuntimeError):
        await processor.process(
            document_id="00000000-0000-0000-0000-000000000001",
            tenant_id="00000000-0000-0000-0000-000000000002",
            storage_key="tenant/doc/file.pdf",
            content_type="application/pdf",
        )

    repo.mark_failed.assert_awaited_once()
    repo.mark_indexed.assert_not_awaited()


@pytest.mark.asyncio
async def test_process_fails_on_empty_text():
    processor, repo = make_processor(
        parsed_doc=ParsedDocument(text="   ", elements=[])
    )

    with pytest.raises(ValueError, match="no extractable text"):
        await processor.process(
            document_id="00000000-0000-0000-0000-000000000001",
            tenant_id="00000000-0000-0000-0000-000000000002",
            storage_key="tenant/doc/file.pdf",
            content_type="application/pdf",
        )

    repo.mark_failed.assert_awaited_once()
