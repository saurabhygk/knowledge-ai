from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID
from pydantic import BaseModel


class DocumentStatus(str, Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    INDEXED = "INDEXED"
    FAILED = "FAILED"


class DocumentResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    filename: str
    content_type: str | None
    status: DocumentStatus
    metadata: dict[str, Any]
    error_message: str | None
    created_at: datetime
    indexed_at: datetime | None

    model_config = {"from_attributes": True}


class DocumentUploadResponse(BaseModel):
    document_id: UUID
    status: str
    message: str


class PageResponse(BaseModel):
    items: list[DocumentResponse]
    total: int
    page: int
    size: int
    pages: int
