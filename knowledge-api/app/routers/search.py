from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.models.schemas import SearchRequest, SearchResponse
from app.services.search_service import SearchService

router = APIRouter(prefix="/api/v1/tenants/{tenant_slug}/search", tags=["search"])


def _svc(request: Request) -> SearchService:
    return request.app.state.search_service


@router.post("", response_model=SearchResponse)
async def search(tenant_slug: str, body: SearchRequest, request: Request):
    try:
        return await _svc(request).search(tenant_slug, body.query, body.top_k, body.min_score)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
