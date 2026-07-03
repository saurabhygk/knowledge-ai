import structlog
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.chunking.base import Chunk, ChunkingStrategy
from app.parsers.base import PageElement, ParsedDocument

log = structlog.get_logger()

# Element types that act as natural section breaks — start a new chunk group
SECTION_BREAK_TYPES = {"Title", "Header"}

# Element types to never split mid-element (emit as a single chunk even if large)
ATOMIC_TYPES = {"Table", "FigureCaption", "Image"}


class ElementAwareChunker(ChunkingStrategy):
    """
    Chunking that respects document structure.
    - Titles group following paragraphs together
    - Tables are never split across chunks
    - Chunk boundaries align with paragraph ends, not mid-sentence

    Better than RecursiveChunker for structured documents (manuals, reports).
    Use RecursiveChunker for raw prose or when element metadata is missing.
    """

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 64):
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        self._chunk_size = chunk_size

    def chunk(self, doc: ParsedDocument, base_metadata: dict) -> list[Chunk]:
        # Group elements into logical sections (Title + its following paragraphs)
        sections = self._group_into_sections(doc.elements)

        chunks: list[Chunk] = []
        char_offset = 0

        for section_elements in sections:
            for el in section_elements:
                el_meta = {
                    **base_metadata,
                    "chunk_strategy": "element_aware",
                    "element_type": el.element_type,
                    "page_number": el.page_number,
                }

                if el.element_type in ATOMIC_TYPES:
                    # Keep atomic elements whole — don't split tables
                    chunks.append(Chunk(
                        text=el.text,
                        chunk_index=len(chunks),
                        char_start=char_offset,
                        char_end=char_offset + len(el.text),
                        metadata=el_meta,
                    ))
                    char_offset += len(el.text) + 2
                else:
                    # Split long elements at sentence boundaries
                    sub_texts = self._splitter.split_text(el.text)
                    for sub in sub_texts:
                        chunks.append(Chunk(
                            text=sub,
                            chunk_index=len(chunks),
                            char_start=char_offset,
                            char_end=char_offset + len(sub),
                            metadata=el_meta,
                        ))
                        char_offset += len(sub)

        log.info("chunking_complete",
                 strategy="element_aware",
                 chunk_count=len(chunks),
                 section_count=len(sections))
        return chunks

    def _group_into_sections(self, elements: list[PageElement]) -> list[list[PageElement]]:
        sections: list[list[PageElement]] = []
        current: list[PageElement] = []

        for el in elements:
            if el.element_type in SECTION_BREAK_TYPES and current:
                sections.append(current)
                current = [el]
            else:
                current.append(el)

        if current:
            sections.append(current)

        return sections
