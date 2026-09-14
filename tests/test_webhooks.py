import hashlib
import hmac

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from api.core.database import get_db
from api.routers import webhooks


class TestFindValue:
    def test_finds_top_level_key(self):
        assert webhooks._find_value({"status": "completed"}, ("status",)) == "completed"

    def test_recurses_into_nested_dicts(self):
        payload = {"data": {"call": {"status": "completed"}}}
        assert webhooks._find_value(payload, ("status",)) == "completed"

    def test_recurses_into_lists_of_dicts(self):
        # Some payload shapes nest the useful fields inside an array -
        # this used to be silently missed entirely.
        payload = {"calls": [{"id": "1"}, {"status": "completed"}]}
        assert webhooks._find_value(payload, ("status",)) == "completed"

    def test_returns_none_when_absent(self):
        assert webhooks._find_value({"foo": "bar"}, ("status",)) is None


class TestNormalizePhone:
    def test_strips_non_digits_and_adds_plus(self):
        assert webhooks._normalize_phone("+91 98100-00001") == "+919810000001"

    def test_none_input_returns_none(self):
        assert webhooks._normalize_phone(None) is None


class TestVerifyWebhook:
    def test_unsigned_is_accepted_in_development(self, monkeypatch):
        monkeypatch.setattr(webhooks.settings, "HUNAR_WEBHOOK_SECRET", "")
        monkeypatch.setattr(webhooks.settings, "ENVIRONMENT", "development")
        webhooks._verify_webhook(b"{}", None)  # should not raise

    def test_unsigned_is_rejected_outside_development(self, monkeypatch):
        monkeypatch.setattr(webhooks.settings, "HUNAR_WEBHOOK_SECRET", "")
        monkeypatch.setattr(webhooks.settings, "ENVIRONMENT", "production")
        with pytest.raises(HTTPException) as exc_info:
            webhooks._verify_webhook(b"{}", None)
        assert exc_info.value.status_code == 503

    def test_missing_signature_is_rejected_when_secret_configured(self, monkeypatch):
        monkeypatch.setattr(webhooks.settings, "HUNAR_WEBHOOK_SECRET", "shh")
        with pytest.raises(HTTPException) as exc_info:
            webhooks._verify_webhook(b"{}", None)
        assert exc_info.value.status_code == 401

    def test_correct_signature_is_accepted(self, monkeypatch):
        monkeypatch.setattr(webhooks.settings, "HUNAR_WEBHOOK_SECRET", "shh")
        body = b'{"status": "completed"}'
        signature = hmac.new(b"shh", body, hashlib.sha256).hexdigest()
        webhooks._verify_webhook(body, f"sha256={signature}")  # should not raise

    def test_wrong_signature_is_rejected(self, monkeypatch):
        monkeypatch.setattr(webhooks.settings, "HUNAR_WEBHOOK_SECRET", "shh")
        with pytest.raises(HTTPException) as exc_info:
            webhooks._verify_webhook(b'{"status": "completed"}', "sha256=wrong")
        assert exc_info.value.status_code == 401


class TestGetLatestOpenForCandidate:
    def test_returns_open_call_not_completed_one(self, db_session, make_candidate, make_call_log):
        from api.repositories.call_log import call_log_repo

        candidate = make_candidate()
        make_call_log(candidate, status="COMPLETED")
        open_call = make_call_log(candidate, status="INITIATING")

        result = call_log_repo.get_latest_open_for_candidate(db_session, candidate_id=candidate.id)

        assert result is not None
        assert result.id == open_call.id

    def test_returns_none_when_no_open_call_exists(self, db_session, make_candidate, make_call_log):
        from api.repositories.call_log import call_log_repo

        candidate = make_candidate()
        make_call_log(candidate, status="COMPLETED")

        result = call_log_repo.get_latest_open_for_candidate(db_session, candidate_id=candidate.id)

        assert result is None


class TestWebhookFallbackMatching:
    """End-to-end: a webhook whose call id doesn't match anything should still
    land on the right call log via the candidate's phone number, rather than
    being dropped."""

    def _client(self, db_session) -> TestClient:
        app = FastAPI()
        app.include_router(webhooks.router, prefix="/api")
        app.dependency_overrides[get_db] = lambda: db_session
        return TestClient(app)

    def test_unmatched_call_id_falls_back_to_candidate_phone(
        self, monkeypatch, db_session, make_candidate, make_call_log,
    ):
        monkeypatch.setattr(webhooks.settings, "HUNAR_WEBHOOK_SECRET", "")
        monkeypatch.setattr(webhooks.settings, "ENVIRONMENT", "development")

        candidate = make_candidate(phone_number="+919810099999")
        open_call = make_call_log(candidate, status="INITIATING")

        client = self._client(db_session)
        response = client.post(
            "/api/webhooks/hunar",
            json={
                "call_id": "an-id-we-never-stored",
                "to_number": "+919810099999",
                "status": "completed",
                "summary": "Great candidate.",
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["call_log_id"] == open_call.id

        db_session.refresh(open_call)
        assert open_call.status == "COMPLETED"
        assert open_call.summary == "Great candidate."
        assert open_call.external_call_id == "an-id-we-never-stored"

    def test_no_candidate_and_no_call_id_is_ignored(self, monkeypatch, db_session):
        monkeypatch.setattr(webhooks.settings, "HUNAR_WEBHOOK_SECRET", "")
        monkeypatch.setattr(webhooks.settings, "ENVIRONMENT", "development")

        client = self._client(db_session)
        response = client.post("/api/webhooks/hunar", json={"status": "completed"})

        assert response.status_code == 200
        assert response.json()["status"] == "ignored"
