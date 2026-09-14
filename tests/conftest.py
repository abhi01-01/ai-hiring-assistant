"""Shared pytest fixtures.

Must set required env vars BEFORE any `api.*` module is imported anywhere -
api.core.config.Settings() is instantiated at import time and DATABASE_URL
has no default, so importing api.core.config (directly, or transitively via
almost any other api.* module) fails immediately without it.
"""
import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/hunar_test",
)
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("HUNAR_API_KEY", "test-hunar-key")
os.environ.setdefault("DEFAULT_AGENT_ID", "test-agent")
os.environ.setdefault("HUNAR_WEBHOOK_SECRET", "test-webhook-secret")
os.environ.setdefault("CANDIDATE_SEARCH_PROVIDER", "mock")
os.environ.setdefault("MOCK_CANDIDATE_PHONE", "")
os.environ.setdefault("DB_AUTO_CREATE", "false")
os.environ.setdefault("DB_AUTO_MIGRATE", "false")

import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.core.config import settings
from api.core.database import Base
from api.repositories import models  # noqa: F401 - register tables on Base.metadata


@pytest.fixture(scope="session")
def db_engine():
    """A Postgres engine for tests that touch the database.

    Uses its own Engine/pool (separate from api.core.database.engine) but
    the same DATABASE_URL, so it reads/writes the same database. Tests that
    need this fixture are skipped - not failed - when no Postgres is
    reachable, since that's an environment gap, not a code bug.
    """
    engine = create_engine(settings.DATABASE_URL, future=True)
    try:
        with engine.connect():
            pass
    except Exception as exc:  # noqa: BLE001 - any connection failure means "skip"
        pytest.skip(f"No reachable Postgres at DATABASE_URL - skipping DB tests ({exc})")

    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def db_session(db_engine):
    """A DB session, truncated clean after every test."""
    session_factory = sessionmaker(bind=db_engine, expire_on_commit=False)
    session = session_factory()
    try:
        yield session
    finally:
        session.rollback()
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
        session.close()


@pytest.fixture()
def make_candidate(db_session):
    """Factory for a minimal persisted Candidate row."""
    from api.repositories.models import Candidate

    def _make(**overrides) -> "Candidate":
        defaults = {
            "id": str(uuid.uuid4()),
            "name": "Test Candidate",
            "phone_number": f"+91{uuid.uuid4().int % 10**10:010d}",
            "skills": [],
        }
        defaults.update(overrides)
        candidate = Candidate(**defaults)
        db_session.add(candidate)
        db_session.commit()
        db_session.refresh(candidate)
        return candidate

    return _make


@pytest.fixture()
def make_call_log(db_session):
    """Factory for a minimal persisted CallLog row."""
    from api.repositories.models import CallLog

    def _make(candidate, **overrides) -> "CallLog":
        defaults = {
            "id": str(uuid.uuid4()),
            "candidate_id": candidate.id,
            "status": "INITIATING",
        }
        defaults.update(overrides)
        call_log = CallLog(**defaults)
        db_session.add(call_log)
        db_session.commit()
        db_session.refresh(call_log)
        return call_log

    return _make
