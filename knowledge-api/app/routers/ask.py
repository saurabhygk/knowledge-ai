from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.models.schemas import AskRequest, AskResponse
from app.services.ask_service import AskService

router = APIRouter(prefix="/api/v1/tenants/{tenant_slug}/ask", tags=["ask"])


def _svc(request: Request) -> AskService:
    return request.app.state.ask_service


@router.post("", response_model=AskResponse)
async def ask(tenant_slug: str, body: AskRequest, request: Request):
    try:
        return await _svc(request).ask(tenant_slug, body.question, body.top_k, body.min_score, body.history)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
