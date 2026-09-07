from sqlalchemy.orm import Session

from api.repositories.base import CRUDBase
from api.repositories.models import CallLog


class CRUDCallLog(CRUDBase[CallLog, object, object]):
    def get_by_external_id(self, db: Session, external_call_id: str) -> CallLog | None:
        return (
            db.query(self.model)
            .filter(self.model.external_call_id == external_call_id)
            .first()
        )


call_log_repo = CRUDCallLog(CallLog)
