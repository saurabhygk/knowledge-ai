from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class PageElement:
    """A single structural element from a document page."""
    page_number: int
    text: str
    element_type: str       # Title, NarrativeText, Table, ListItem, etc.
    metadata: dict = field(default_factory=dict)


@dataclass
class ParsedDocument:
    """Output of a parser — full text plus structured element breakdown."""
    text: str                           # Full concatenated text
    elements: list[PageElement]         # Structured elements (preserves type + page)
    metadata: dict = field(default_factory=dict)

    @property
    def page_count(self) -> int:
        pages = {e.page_number for e in self.elements if e.page_number}
        return max(pages) if pages else 0


class DocumentParser(ABC):
    @abstractmethod
    def can_parse(self, content_type: str) -> bool:
        """Return True if this parser handles the given MIME type."""
        ...

    @abstractmethod
    def parse(self, file_bytes: bytes, filename: str) -> ParsedDocument:
        """Extract text and structure from raw file bytes."""
        ...
