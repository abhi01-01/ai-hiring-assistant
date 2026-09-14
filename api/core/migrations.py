
from sqlalchemy import inspect, text

from api.core.database import Base, engine
from api.repositories import models

# These are the tables that make up the application's current schema.
_REQUIRED_TABLES = {"candidates", "call_logs"}


def _bootstrap_schema(connection) -> None:
    """Create the ORM schema only when this is a new/empty database.

    We do this at application startup rather than module import time. That
    avoids racing PostgreSQL during container startup while still making a
    fresh assignment/demo database self-initializing.
    """
    inspector = inspect(connection)
    existing = set(inspector.get_table_names())

    if not _REQUIRED_TABLES.issubset(existing):
        Base.metadata.create_all(bind=connection)


def run_compatible_migrations() -> None:
    """Bootstrap a fresh DB and apply idempotent compatibility changes."""
    with engine.begin() as connection:
        _bootstrap_schema(connection)

        # Existing installations may have an earlier version of the schema.
        # These ALTER statements are safe to run repeatedly.
        statements = [
            "ALTER TABLE candidates ADD COLUMN IF NOT EXISTS linkedin_url VARCHAR(500)",
            "ALTER TABLE candidates ADD COLUMN IF NOT EXISTS skills JSON NOT NULL DEFAULT '[]'::json",
            "ALTER TABLE call_logs ADD COLUMN IF NOT EXISTS external_call_id VARCHAR(200)",
            "ALTER TABLE call_logs ADD COLUMN IF NOT EXISTS transcript TEXT",
            "ALTER TABLE call_logs ADD COLUMN IF NOT EXISTS summary TEXT",
            "ALTER TABLE call_logs ADD COLUMN IF NOT EXISTS duration_seconds INTEGER",
            "ALTER TABLE call_logs ADD COLUMN IF NOT EXISTS result TEXT",
            "ALTER TABLE call_logs ALTER COLUMN result TYPE TEXT",
            "ALTER TABLE call_logs ADD COLUMN IF NOT EXISTS recording_url VARCHAR(1000)",
            "ALTER TABLE call_logs ADD COLUMN IF NOT EXISTS custom_data JSON",
            "ALTER TABLE call_logs ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL",
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_call_logs_external_call_id ON call_logs(external_call_id) WHERE external_call_id IS NOT NULL",
            "CREATE INDEX IF NOT EXISTS ix_call_logs_candidate_created ON call_logs(candidate_id, created_at DESC)",
            "CREATE INDEX IF NOT EXISTS ix_candidates_created_at ON candidates(created_at DESC)",
        ]

        for statement in statements:
            connection.execute(text(statement))
