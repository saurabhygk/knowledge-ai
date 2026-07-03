from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from app.parsers.base import ParsedDocument


@dataclass
class Chunk:
    text: str
    chunk_index: int
    char_start: int
    char_end: int
    metadata: dict = field(default_factory=dict)
    # metadata should include: document_id, tenant_id, filename, page_number,
    # element_type (if available), chunk_strategy


class ChunkingStrategy(ABC):
    @abstractmethod
    def chunk(self, doc: ParsedDocument, base_metadata: dict) -> list[Chunk]:
        """Split a parsed document into chunks with enriched metadata."""
        ...
