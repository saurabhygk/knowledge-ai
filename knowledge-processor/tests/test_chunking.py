import pytest
from app.chunking.recursive_chunker import RecursiveChunker
from app.chunking.element_aware_chunker import ElementAwareChunker
from app.parsers.base import ParsedDocument, PageElement

BASE_META = {"document_id": "doc-1", "tenant_id": "tenant-1", "filename": "test.pdf"}


def make_doc(text: str, elements: list[PageElement] | None = None) -> ParsedDocument:
    return ParsedDocument(
        text=text,
        elements=elements or [PageElement(page_number=1, text=text, element_type="NarrativeText")],
    )


class TestRecursiveChunker:
    def test_splits_long_text(self):
        chunker = RecursiveChunker(chunk_size=100, chunk_overlap=10)
        doc = make_doc("word " * 200)
        chunks = chunker.chunk(doc, BASE_META)
        assert len(chunks) > 1

    def test_short_text_is_one_chunk(self):
        chunker = RecursiveChunker(chunk_size=512, chunk_overlap=64)
        doc = make_doc("This is a short document.")
        chunks = chunker.chunk(doc, BASE_META)
        assert len(chunks) == 1
        assert chunks[0].chunk_index == 0

    def test_chunk_metadata_has_strategy(self):
        chunker = RecursiveChunker(chunk_size=512, chunk_overlap=64)
        doc = make_doc("Hello world.")
        chunks = chunker.chunk(doc, BASE_META)
        assert chunks[0].metadata["chunk_strategy"] == "recursive"

    def test_chunk_text_covers_full_document(self):
        chunker = RecursiveChunker(chunk_size=100, chunk_overlap=20)
        original = "The quick brown fox jumps over the lazy dog. " * 20
        doc = make_doc(original)
        chunks = chunker.chunk(doc, BASE_META)
        combined = " ".join(c.text for c in chunks)
        # Every word from the original should appear in at least one chunk
        for word in original.split():
            assert word in combined


class TestElementAwareChunker:
    def test_atomic_table_not_split(self):
        chunker = ElementAwareChunker(chunk_size=50, chunk_overlap=0)
        table_text = "col1 | col2\n" + "data | data\n" * 20  # > 50 chars
        elements = [PageElement(page_number=1, text=table_text, element_type="Table")]
        doc = make_doc(table_text, elements)
        chunks = chunker.chunk(doc, BASE_META)
        # Table should be emitted as a single chunk regardless of chunk_size
        table_chunks = [c for c in chunks if c.metadata.get("element_type") == "Table"]
        assert len(table_chunks) == 1
        assert table_chunks[0].text == table_text

    def test_section_break_on_title(self):
        chunker = ElementAwareChunker(chunk_size=512, chunk_overlap=0)
        elements = [
            PageElement(page_number=1, text="Introduction", element_type="Title"),
            PageElement(page_number=1, text="Some intro text.", element_type="NarrativeText"),
            PageElement(page_number=2, text="Chapter 2", element_type="Title"),
            PageElement(page_number=2, text="Chapter 2 content.", element_type="NarrativeText"),
        ]
        full_text = "\n\n".join(e.text for e in elements)
        doc = make_doc(full_text, elements)
        chunks = chunker.chunk(doc, BASE_META)
        assert len(chunks) >= 4  # at minimum one chunk per element
