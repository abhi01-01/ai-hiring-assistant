from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
import re


E164_PATTERN = re.compile(r"^\+[1-9]\d{7,14}$")


class CallLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    external_call_id: str | None = None
    status: str
    transcript: str | None = None
    summary: str | None = None
    duration_seconds: int | None = None
    result: str | None = None
    recording_url: str | None = None
    created_at: datetime


class CandidateBase(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    phone_number: str
    email: EmailStr | None = None
    linkedin_url: str | None = Field(default=None, max_length=500)
    skills: list[str] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if len(normalized) < 2:
            raise ValueError("name must contain at least 2 characters")
        return normalized

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        value = value.strip().replace(" ", "")
        if not E164_PATTERN.fullmatch(value):
            raise ValueError("phone_number must be a valid E.164 number, e.g. +919876543210")
        return value


class CandidateCreate(CandidateBase):
    job_description: str | None = Field(default=None, max_length=10000)
    company: str | None = Field(default=None, max_length=200)
    job_role: str | None = Field(default=None, max_length=200)


class CandidateResponse(CandidateBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    calls: list[CallLogResponse] = Field(default_factory=list)


class OutreachResponse(BaseModel):
    candidate: CandidateResponse
    call: CallLogResponse


class SearchRequest(BaseModel):
    job_description: str = Field(min_length=10, max_length=10000)
    company: str | None = Field(default=None, max_length=200)
    job_role: str | None = Field(default=None, max_length=200)
    per_page: int = Field(default=10, ge=1, le=20)


class SearchCandidateResponse(BaseModel):
    apollo_id: str | None = None
    name: str
    email: str | None = None
    phone_number: str | None = None
    linkedin_url: str | None = None
    title: str | None = None
    company: str | None = None
    skills: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
