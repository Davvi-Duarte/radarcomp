from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class Plan(StrEnum):
    A = "A"
    B = "B"
    C = "C"
    OTHER = "OTHER"


class Priority(StrEnum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class OpportunityStatus(StrEnum):
    NEW = "NEW"
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    APPLIED = "APPLIED"
    IGNORED = "IGNORED"
    WATCHING = "WATCHING"


class OpportunityType(StrEnum):
    PROFESSOR_EFFECTIVE = "PROFESSOR_EFFECTIVE"
    PROFESSOR_SUBSTITUTE = "PROFESSOR_SUBSTITUTE"
    PROFESSOR_OTHER = "PROFESSOR_OTHER"
    TAE = "TAE"
    QA = "QA"
    OTHER_IT = "OTHER_IT"
    UNKNOWN = "UNKNOWN"


class DocumentLink(BaseModel):
    title: str
    description: str = ""
    published_at: datetime | None = None
    url: str
    is_pdf: bool = False


class ListingEntry(BaseModel):
    title: str
    description: str = ""
    url: str
    source_name: str
    source_kind: str


class LLMExtraction(BaseModel):
    job_area: str | None = None
    campus: str | None = None
    city: str | None = None
    state: str | None = "PB"
    number_of_positions: int | None = None
    salary: float | None = None
    workload: str | None = None
    registration_start: date | None = None
    registration_end: date | None = None
    accepted_degrees: list[str] = Field(default_factory=list)
    minimum_degree: str | None = None
    requirements: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    summary: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class Opportunity(BaseModel):
    id: str
    title: str
    institution: str
    institution_type: str = "public"
    plan: Plan = Plan.OTHER
    priority: Priority = Priority.P3
    opportunity_type: OpportunityType = OpportunityType.UNKNOWN
    job_area: str | None = None
    city: str | None = None
    state: str | None = "PB"
    campus: str | None = None
    work_mode: str | None = None
    contract_type: str | None = None
    number_of_positions: int | None = None
    salary: float | None = None
    workload: str | None = None
    publication_date: date | None = None
    registration_start: date | None = None
    registration_end: date | None = None
    source_url: str
    official_url: str
    edital_url: str | None = None
    edital_number: str | None = None
    requirements: list[str] = Field(default_factory=list)
    accepted_degrees: list[str] = Field(default_factory=list)
    minimum_degree: str | None = None
    technologies: list[str] = Field(default_factory=list)
    description: str = ""
    strategic_score: float = 0.0
    compatibility_score: float = 0.0
    urgency_score: float = 0.0
    total_score: float = 0.0
    score_explanation: list[str] = Field(default_factory=list)
    first_seen_at: datetime
    last_seen_at: datetime
    status: OpportunityStatus = OpportunityStatus.NEW
    source_hash: str | None = None
    last_notified_hash: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ScanEvent(BaseModel):
    timestamp: datetime
    event: str
    opportunity_id: str | None = None
    source: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
