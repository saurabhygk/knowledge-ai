import io
import structlog
from app.parsers.base import DocumentParser, ParsedDocument, PageElement

log = structlog.get_logger()


class UnstructuredParser(DocumentParser):
    """
    Parser backed by unstructured.io — handles PDF, DOCX, HTML, PPTX,
    images (with OCR), and more via a single unified API.
    """

    # Element types we keep as-is vs. skip (e.g. page breaks, footers)
    SKIP_TYPES = {"PageBreak", "Header", "Footer"}

    def can_parse(self, content_type: str) -> bool:
        return True  # unstructured handles virtually every document format

    def parse(self, file_bytes: bytes, filename: str) -> ParsedDocument:
        # Import here to keep startup fast when unstructured is not installed
        from unstructured.partition.auto import partition

        log.info("parsing_document", filename=filename, size_bytes=len(file_bytes))

        elements = partition(
            file=io.BytesIO(file_bytes),
            metadata_filename=filename,
            # Strategy: "hi_res" gives better table/image extraction (needs poppler+tesseract)
            # "fast" skips OCR — good for text-native PDFs
            strategy="fast",
            include_page_breaks=False,
        )

        page_elements: list[PageElement] = []
        for el in elements:
            el_type = type(el).__name__
            if el_type in self.SKIP_TYPES:
                continue
            text = el.text.strip() if el.text else ""
            if not text:
                continue

            page_num = 0
            if hasattr(el, "metadata") and el.metadata:
                page_num = getattr(el.metadata, "page_number", 0) or 0

            page_elements.append(PageElement(
                page_number=page_num,
                text=text,
                element_type=el_type,
                metadata={
                    "filename": filename,
                    "page_number": page_num,
                    "element_type": el_type,
                },
            ))

        full_text = "\n\n".join(e.text for e in page_elements)

        log.info("parsing_complete",
                 filename=filename,
                 element_count=len(page_elements),
                 char_count=len(full_text))

        return ParsedDocument(
            text=full_text,
            elements=page_elements,
            metadata={"filename": filename, "page_count": max((e.page_number for e in page_elements), default=0)},
        )
