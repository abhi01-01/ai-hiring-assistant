import httpx
from fastapi import APIRouter, Depends, Request

from api.schemas import SearchCandidateResponse, SearchRequest
from api.services.search import get_search_provider

router = APIRouter(prefix="/search", tags=["Search"])


@router.post("", response_model=list[SearchCandidateResponse])
async def search_candidates(request: Request, payload: SearchRequest):
    client: httpx.AsyncClient = request.app.state.http_client

    provider = get_search_provider()

    return await provider.search_candidates(
        client,
        job_description=payload.job_description,
        job_role=payload.job_role,
        company=payload.company,
        per_page=payload.per_page,
    )
