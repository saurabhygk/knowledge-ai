from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status

from app.models.schemas import TenantCreate, TenantResponse
from app.repositories.tenant_repository import TenantRepository

router = APIRouter(prefix="/api/v1/tenants", tags=["tenants"])


def _repo(request: Request) -> TenantRepository:
    return request.app.state.tenant_repo


@router.post("", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(body: TenantCreate, request: Request):
    try:
        row = await _repo(request).create(body.name, body.slug)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return TenantResponse(**row)


@router.get("", response_model=list[TenantResponse])
async def list_tenants(request: Request):
    rows = await _repo(request).list_all()
    return [TenantResponse(**r) for r in rows]
