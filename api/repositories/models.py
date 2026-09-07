import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from api.core.database import Base


class Candidate(Base):
    __tablename__ = "candidates"
    __table_args__ = (
        UniqueConstraint("phone_number", name="uq_candidates_phone_number"),
        Index("ix_candidates_created_at", "created_at"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    phone_number = Column(String(20), nullable=False)
    email = Column(String(320), nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    skills = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    calls = relationship(
        "CallLog",
        back_populates="candidate",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="CallLog.created_at.desc()",
    )


class CallLog(Base):
    __tablename__ = "call_logs"
    __table_args__ = (
        UniqueConstraint("external_call_id", name="uq_call_logs_external_call_id"),
        Index("ix_call_logs_candidate_created", "candidate_id", "created_at"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    external_call_id = Column(String(200), nullable=True)
    candidate_id = Column(
        String(36),
        ForeignKey("candidates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status = Column(String(40), nullable=False, default="INITIATING")
    transcript = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    result = Column(String(100), nullable=True)
    recording_url = Column(String(1000), nullable=True)
    custom_data = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    candidate = relationship("Candidate", back_populates="calls")
