import re
import uuid

import httpx
from sqlalchemy.orm import Session

from api.repositories.candidate import candidate_repo
from api.repositories.models import CallLog, Candidate
from api.schemas import CandidateCreate
from api.services.hunar import HunarVoiceService


class HiringService:
    @staticmethod
    def _sanitize_job_description(job_description: str | None, job_role: str | None) -> str:
        raw = job_description or f"We are hiring for a {job_role or 'Software Engineer'} role."
        clean = re.sub(r"[^a-zA-Z0-9\s.,:/+#()_-]", " ", raw)
        return " ".join(clean.split())[:1000]

    @staticmethod
    def _extract_external_call_id(response: dict) -> str | None:
        for key in ("call_id", "callId", "id", "campaign_call_id"):
            value = response.get(key)
            if value is not None:
                return str(value)
        nested_call = response.get("call")
        if isinstance(nested_call, dict):
            for key in ("call_id", "callId", "id"):
                value = nested_call.get(key)
                if value is not None:
                    return str(value)
        return None

    @classmethod
    async def process_new_candidate(
            cls,
            db: Session,
            client: httpx.AsyncClient,
            candidate_in: CandidateCreate,
    ) -> tuple[Candidate, CallLog]:
        candidate = candidate_repo.get_by_phone(db, phone_number=candidate_in.phone_number)

        if candidate is None:
            candidate = Candidate(
                id=str(uuid.uuid4()),
                name=candidate_in.name,
                phone_number=candidate_in.phone_number,
                email=str(candidate_in.email) if candidate_in.email else None,
                linkedin_url=candidate_in.linkedin_url,
                skills=candidate_in.skills,
            )
            db.add(candidate)
        else:
            # A repeat outreach is valid. Update profile data without creating a duplicate candidate.
            candidate.name = candidate_in.name
            candidate.email = str(candidate_in.email) if candidate_in.email else candidate.email
            candidate.linkedin_url = candidate_in.linkedin_url or candidate.linkedin_url
            candidate.skills = candidate_in.skills or candidate.skills

        request_id = f"candidate-{candidate.id}-{uuid.uuid4().hex[:12]}"

        call_log = CallLog(
            id=str(uuid.uuid4()),
            candidate_id=candidate.id,
            status="INITIATING",
            custom_data={"request_id": request_id},
        )
        db.add(call_log)
        db.commit()
        db.refresh(candidate)
        db.refresh(call_log)

        custom_data = {
            "job_description": cls._sanitize_job_description(
                candidate_in.job_description,
                candidate_in.job_role,
            ),
            "company": candidate_in.company or "Unknown",
            "job_role": candidate_in.job_role or "Software Engineer",
            "candidate_id": candidate.id,
            "outreach_id": call_log.id,
        }

        try:
            request_id = call_log.custom_data["request_id"]

            response = await HunarVoiceService.initiate_call(
                client,
                candidate_name=candidate.name,
                phone_number=candidate.phone_number,
                custom_data=custom_data,
                request_id=request_id,
            )

            external_call_id = cls._extract_external_call_id(response)
            if external_call_id:
                call_log.external_call_id = external_call_id

            call_log.status = cls._normalize_status(response.get("status"), default="CREATED")
            call_log.custom_data = {**custom_data, "hunar_response": response}
            db.commit()
            db.refresh(call_log)
            return candidate, call_log
        except Exception:
            call_log.status = "FAILED"
            db.commit()
            raise

    @staticmethod
    def _normalize_status(value: str | None, default: str = "UNKNOWN") -> str:
        normalized = (value or default).strip().upper().replace(" ", "_")
        aliases = {
            "PENDING": "CREATED",
            "QUEUED": "CREATED",
            "IN_PROGRESS": "IN_PROGRESS",
            "IN-PROGRESS": "IN_PROGRESS",
            "COMPLETED": "COMPLETED",
            "COMPLETE": "COMPLETED",
            "FAILED": "FAILED",
            "ERROR": "FAILED",
            "NO_ANSWER": "NO_ANSWER",
        }
        return aliases.get(normalized, normalized[:40])
