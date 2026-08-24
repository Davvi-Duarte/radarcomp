from __future__ import annotations

from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field


class CurriculumItemType(StrEnum):
    TEACHING = "TEACHING"
    COURSE_TAUGHT = "COURSE_TAUGHT"
    ARTICLE = "ARTICLE"
    PROJECT = "PROJECT"
    EVENT = "EVENT"
    DEGREE = "DEGREE"


class CurriculumItem(BaseModel):
    id: str
    item_type: CurriculumItemType
    institution: str | None = None
    subject_or_title: str
    area: str | None = None
    education_level: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    hours: float | None = None
    has_documentation: bool = False
    documentation_notes: str | None = None
    tags: list[str] = Field(default_factory=list)

# V1 only defines the stable domain model. Persistence/edition will be added in V2.
