import httpx
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session, selectinload

from api.core.database import get_db
from api.repositories.models import Candidate
from api.schemas import CandidateCreate, CandidateResponse, OutreachResponse
from api.services.hiring import HiringService

router = APIRouter(prefix="/candidates", tags=["Candidates"])


@router.get("", response_model=list[CandidateResponse])
def get_candidates(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db),
):
    limit = min(max(limit, 1), 100)
    return (
        db.query(Candidate)
        .options(selectinload(Candidate.calls))
        .order_by(Candidate.created_at.desc())
        .offset(max(skip, 0))
        .limit(limit)
        .all()
    )


@router.post("", response_model=OutreachResponse, status_code=status.HTTP_201_CREATED)
async def create_candidate(
        candidate_in: CandidateCreate,
        request: Request,
        db: Session = Depends(get_db),
):
    client: httpx.AsyncClient = request.app.state.http_client
    candidate, call = await HiringService.process_new_candidate(db, client, candidate_in)
    candidate = (
        db.query(Candidate)
        .options(selectinload(Candidate.calls))
        .filter(Candidate.id == candidate.id)
        .one()
    )
    return OutreachResponse(candidate=candidate, call=call)


@router.get("/dashboard", response_model=list[dict])
def get_dashboard_data(db: Session = Depends(get_db)):
    candidates = (
        db.query(Candidate)
        .options(selectinload(Candidate.calls))
        .order_by(Candidate.created_at.desc())
        .limit(100)
        .all()
    )
    return [
        {
            "name": candidate.name,
            "phone": candidate.phone_number,
            "status": candidate.calls[0].status if candidate.calls else "PENDING",
            "transcript": candidate.calls[0].transcript if candidate.calls else None,
            "summary": candidate.calls[0].summary if candidate.calls else None,
        }
        for candidate in candidates
    ]
