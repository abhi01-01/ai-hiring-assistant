import hashlib
import hmac
import json
import logging
import re

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from api.core.config import settings
from api.core.database import get_db
from api.repositories.call_log import call_log_repo
from api.repositories.candidate import candidate_repo
from api.repositories.models import CallLog, Candidate
from api.services.hiring import HiringService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


def _find_value(payload: dict, keys: tuple[str, ...]):
    for key in keys:
        if key in payload and payload[key] not in (None, ""):
            return payload[key]
    for value in payload.values():
        if isinstance(value, dict):
            nested = _find_value(value, keys)
            if nested is not None:
                return nested
    return None


def _normalize_phone(value: str | None) -> str | None:
    if not value:
        return None
    digits = re.sub(r"\D", "", str(value))
    return f"+{digits}" if digits else None


def _verify_webhook(raw_body: bytes, signature: str | None) -> None:
    if not settings.HUNAR_WEBHOOK_SECRET:
        return
    if not signature:
        raise HTTPException(status_code=401, detail="Missing webhook signature")

    expected = hmac.new(
        settings.HUNAR_WEBHOOK_SECRET.encode(),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    supplied = signature.removeprefix("sha256=")
    if not hmac.compare_digest(expected, supplied):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")


@router.post("/hunar", status_code=200)
async def process_hunar_webhook(
        request: Request,
        db: Session = Depends(get_db),
        x_hunar_signature: str | None = Header(default=None),
):
    raw_body = await request.body()
    _verify_webhook(raw_body, x_hunar_signature)

    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Webhook body must be valid JSON") from exc

    external_call_id = _find_value(payload, ("call_id", "callId", "conversation_id", "conversationId", "id"))
    external_call_id = str(external_call_id) if external_call_id is not None else None

    call_log: CallLog | None = None
    if external_call_id:
        call_log = call_log_repo.get_by_external_id(db, external_call_id)

    candidate: Candidate | None = None
    phone = _normalize_phone(
        _find_value(
            payload,
            (
                "to_number",
                "customer_number",
                "customerNumber",
                "to",
                "mobile_number",
                "mobileNumber",
                "phone_number",
                "phoneNumber",
            ),
        )
    )
    if phone:
        candidate = candidate_repo.get_by_phone(db, phone_number=phone)

    if call_log is None:
        logger.warning(
            "No CallLog found for Hunar external_call_id=%s phone=%s",
            external_call_id,
            phone,
        )
        return {
            "status": "ignored",
            "reason": "No matching call log",
        }

    status_value = _find_value(payload, ("status", "call_status", "callStatus"))
    if isinstance(status_value, str):
        call_log.status = HiringService._normalize_status(status_value, default="RECEIVED")

    transcript = _find_value(payload, ("transcript", "conversation_transcript", "conversationTranscript"))
    summary = _find_value(payload, ("summary", "call_summary", "callSummary"))
    result = _find_value(payload, ("result", "outcome", "disposition"))
    recording_url = _find_value(payload, ("recording_url", "recordingUrl", "recording"))
    duration = _find_value(payload, ("duration_seconds", "durationSeconds", "duration"))

    if transcript is not None:
        call_log.transcript = str(transcript)
    if summary is not None:
        call_log.summary = str(summary)
    if result is not None:
        call_log.result = json.dumps(result, ensure_ascii=False)
    if recording_url is not None:
        call_log.recording_url = str(recording_url)
    if duration is not None:
        try:
            call_log.duration_seconds = int(float(duration))
        except (TypeError, ValueError):
            logger.warning("Ignoring invalid call duration from Hunar webhook: %r", duration)

    call_log.custom_data = payload
    db.commit()

    return {
        "status": "success",
        "call_log_id": call_log.id,
        "external_call_id": call_log.external_call_id,
    }
