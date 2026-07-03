import structlog
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.chunking.base import Chunk, ChunkingStrategy
from app.parsers.base import ParsedDocument

log = structlog.get_logger()


class RecursiveChunker(ChunkingStrategy):
    """
    Split text recursively on paragraph/sentence/word boundaries.
    Fast and reliable — the right default for most document types.
    """

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 64):
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            # Try to break at natural boundaries, falling back to smaller units
            separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""],
            length_function=len,
        )
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    def chunk(self, doc: ParsedDocument, base_metadata: dict) -> list[Chunk]:
        raw_chunks = self._splitter.split_text(doc.text)

        chunks: list[Chunk] = []
        cursor = 0

        for idx, text in enumerate(raw_chunks):
            start = doc.text.find(text, cursor)
            if start == -1:
                start = cursor
            end = start + len(text)
            cursor = max(cursor, end - self._chunk_overlap)

            chunks.append(Chunk(
                text=text,
                chunk_index=idx,
                char_start=start,
                char_end=end,
                metadata={
                    **base_metadata,
                    "chunk_strategy": "recursive",
                    "chunk_size": self._chunk_size,
                    "chunk_overlap": self._chunk_overlap,
                },
            ))

        log.info("chunking_complete",
                 strategy="recursive",
                 chunk_count=len(chunks),
                 chunk_size=self._chunk_size)
        return chunks
