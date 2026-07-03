from __future__ import annotations

import math
import uuid
from typing import Any

import structlog

from app.events.processing_producer import publish_processing_event
from app.models.schemas import DocumentResponse, DocumentUploadResponse, PageResponse
from app.repositories.document_repository import DocumentRepository
from app.services.storage_service import StorageService

log = structlog.get_logger()


class DocumentService:
    def __init__(self, repo: DocumentRepository, storage: StorageService):
        self._repo = repo
        self._storage = storage

    async def upload(
        self,
        tenant_slug: str,
        filename: str,
        content_type: str | None,
        data: bytes,
    ) -> DocumentUploadResponse:
        tenant = await self._repo.get_tenant_by_slug(tenant_slug)
        if not tenant:
            raise KeyError(f"Tenant not found: {tenant_slug}")

        tenant_id = tenant["id"]
        storage_key = f"{tenant_id}/{uuid.uuid4()}/{filename}"
        self._storage.upload(storage_key, data, content_type)

        doc = await self._repo.create_document(
            tenant_id=tenant_id,
            filename=filename,
            content_type=content_type,
            storage_key=storage_key,
        )

        await publish_processing_event(
            document_id=str(doc["id"]),
            tenant_id=str(tenant_id),
            storage_key=storage_key,
            content_type=content_type,
        )

        log.info("document_uploaded", document_id=str(doc["id"]), tenant=tenant_slug)
        return DocumentUploadResponse(
            document_id=doc["id"],
            status="UPLOADED",
            message="Document uploaded and queued for processing",
        )

    async def list_documents(self, tenant_slug: str, page: int, size: int) -> PageResponse:
        tenant = await self._repo.get_tenant_by_slug(tenant_slug)
        if not tenant:
            raise KeyError(f"Tenant not found: {tenant_slug}")

        docs, total = await self._repo.list_documents(tenant["id"], page, size)
        return PageResponse(
            items=[_to_response(d) for d in docs],
            total=total,
            page=page,
            size=size,
            pages=max(1, math.ceil(total / size)),
        )

    async def get_document(self, tenant_slug: str, document_id: uuid.UUID) -> DocumentResponse:
        tenant = await self._repo.get_tenant_by_slug(tenant_slug)
        if not tenant:
            raise KeyError(f"Tenant not found: {tenant_slug}")

        doc = await self._repo.get_document(document_id, tenant["id"])
        if not doc:
            raise LookupError(f"Document not found: {document_id}")

        return _to_response(doc)


def _to_response(row: dict[str, Any]) -> DocumentResponse:
    import json
    metadata = row.get("metadata") or {}
    if isinstance(metadata, str):
        metadata = json.loads(metadata)
    return DocumentResponse(
        id=row["id"],
        tenant_id=row["tenant_id"],
        filename=row["filename"],
        content_type=row.get("content_type"),
        status=row["status"],
        metadata=metadata,
        error_message=row.get("error_message"),
        created_at=row["created_at"],
        indexed_at=row.get("indexed_at"),
    )
