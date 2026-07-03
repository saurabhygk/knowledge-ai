from __future__ import annotations

import uuid

from fastapi import APIRouter, File, HTTPException, Query, Request, UploadFile, status

from app.models.schemas import DocumentResponse, DocumentUploadResponse, PageResponse
from app.services.document_service import DocumentService

router = APIRouter(prefix="/api/v1/tenants/{tenant_slug}/documents", tags=["documents"])


def _svc(request: Request) -> DocumentService:
    return request.app.state.document_service


@router.post("", response_model=DocumentUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    tenant_slug: str,
    request: Request,
    file: UploadFile = File(...),
):
    data = await file.read()
    try:
        return await _svc(request).upload(tenant_slug, file.filename, file.content_type, data)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("", response_model=PageResponse)
async def list_documents(
    tenant_slug: str,
    request: Request,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
):
    try:
        return await _svc(request).list_documents(tenant_slug, page, size)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    tenant_slug: str,
    document_id: uuid.UUID,
    request: Request,
):
    try:
        return await _svc(request).get_document(tenant_slug, document_id)
    except (KeyError, LookupError) as e:
        raise HTTPException(status_code=404, detail=str(e))
