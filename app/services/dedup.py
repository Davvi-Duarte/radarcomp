from __future__ import annotations

from difflib import SequenceMatcher

from app.domain.models import Opportunity
from app.utils.text import normalize_text


def find_duplicate(candidate: Opportunity, existing: list[Opportunity], threshold: float = 0.88) -> Opportunity | None:
    for item in existing:
        if normalize_text(item.institution) != normalize_text(candidate.institution):
            continue
        if candidate.edital_number and item.edital_number and candidate.edital_number == item.edital_number:
            return item
        title_ratio = SequenceMatcher(None, normalize_text(item.title), normalize_text(candidate.title)).ratio()
        if title_ratio >= threshold:
            return item
    return None
