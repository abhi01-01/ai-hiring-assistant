
import logging
from typing import Any

import httpx
from fastapi import HTTPException

from api.core.config import settings

logger = logging.getLogger(__name__)


class HunarVoiceService:
    """
    Client for Hunar Voice Agents External API.

    Hunar external API:
        Base URL:
        https://api.voice.hunar.ai/external/v1/

    Authentication:
        X-API-Key: <api-key>

    Single call:
        POST /calls/
    """

    @classmethod
    def _headers(cls) -> dict[str, str]:
        if not settings.HUNAR_API_KEY:
            raise HTTPException(
                status_code=503,
                detail="HUNAR_API_KEY is not configured",
            )

        return {
            "X-API-Key": settings.HUNAR_API_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    @classmethod
    async def initiate_call(
            cls,
            client: httpx.AsyncClient,
            *,
            candidate_name: str,
            phone_number: str,
            custom_data: dict,
            request_id: str,
    ) -> dict:
        headers = cls._headers()

        payload = {
            "agent_id": settings.DEFAULT_AGENT_ID,
            "callee_name": candidate_name,
            "mobile_number": phone_number,
            "custom_data": custom_data,
            "request_id": request_id,
            "timezone": "Asia/Kolkata",
            "callback_config": {
                "call_status_callback_url": settings.HUNAR_WEBHOOK_URL,
                "call_recording_callback_url": settings.HUNAR_WEBHOOK_URL,
                "call_result_callback_url": settings.HUNAR_WEBHOOK_URL,
                "call_summary_callback_url": settings.HUNAR_WEBHOOK_URL,
            },
        }

        logger.info(
            "Starting Hunar call candidate=%s agent_id=%s request_id=%s",
            candidate_name,
            settings.DEFAULT_AGENT_ID,
            request_id,
        )

        try:
            response = await client.post(
                "https://api.voice.hunar.ai/external/v1/calls/",
                headers=headers,
                json=payload,
                timeout=settings.HUNAR_HTTP_TIMEOUT,
            )
        except httpx.TimeoutException as exc:
            logger.exception("Hunar API timeout")
            raise HTTPException(
                status_code=504,
                detail="Hunar API request timed out",
            ) from exc
        except httpx.RequestError as exc:
            logger.exception("Hunar API network error")
            raise HTTPException(
                status_code=502,
                detail="Unable to reach Hunar API",
            ) from exc

        body = response.text[:4000]

        logger.info(
            "Hunar response status=%s body=%s",
            response.status_code,
            body,
        )

        if response.is_error:
            try:
                detail = response.json()
            except ValueError:
                detail = body

            raise HTTPException(
                status_code=502,
                detail={
                    "message": "Hunar API rejected the request",
                    "upstream_status": response.status_code,
                    "upstream_response": detail,
                },
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise HTTPException(
                status_code=502,
                detail="Hunar returned invalid JSON",
            ) from exc

        return data