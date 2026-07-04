from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID
from pydantic import BaseModel, Field


class TenantCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class TenantResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    access_token: str
    created_at: datetime


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


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)
    min_score: float = Field(default=0.5, ge=0.0, le=1.0)


class SearchResult(BaseModel):
    chunk_text: str
    score: float
    document_id: UUID
    filename: str
    chunk_index: int
    metadata: dict[str, Any]


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]


class HistoryMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)
    min_score: float = Field(default=0.5, ge=0.0, le=1.0)
    history: list[HistoryMessage] = Field(default_factory=list)


class AskResponse(BaseModel):
    question: str
    answer: str
    sources: list[SearchResult]
    llm_provider: str
