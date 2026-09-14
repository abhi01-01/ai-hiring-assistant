from sqlalchemy.orm import Session

from api.repositories.base import CRUDBase
from api.repositories.models import CallLog

OPEN_CALL_STATUSES = ("INITIATING", "CREATED", "IN_PROGRESS")
class CRUDCallLog(CRUDBase[CallLog, object, object]):
    def get_by_external_id(self, db: Session, external_call_id: str) -> CallLog | None:
        return (
            db.query(self.model)
            .filter(self.model.external_call_id == external_call_id)
            .first()
        )

    def get_latest_open_for_candidate(self, db: Session, *, candidate_id: str) -> CallLog | None:
        return (
            db.query(self.model)
            .filter(
                self.model.candidate_id == candidate_id,
                self.model.status.in_(OPEN_CALL_STATUSES),
                )
            .order_by(self.model.created_at.desc())
            .first()
        )


call_log_repo = CRUDCallLog(CallLog)
