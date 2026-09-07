from sqlalchemy.orm import Session

from api.repositories.base import CRUDBase
from api.repositories.models import Candidate
from api.schemas import CandidateCreate


class CRUDCandidate(CRUDBase[Candidate, CandidateCreate, CandidateCreate]):
    def get_by_phone(self, db: Session, *, phone_number: str) -> Candidate | None:
        return (
            db.query(self.model)
            .filter(self.model.phone_number == phone_number)
            .first()
        )


candidate_repo = CRUDCandidate(Candidate)
