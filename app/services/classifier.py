from __future__ import annotations

from dataclasses import dataclass

from app.domain.models import OpportunityType, Plan, Priority
from app.utils.text import normalize_text


COMPUTING_TERMS = [
    "computacao", "informatica", "tecnologia da informacao", "sistemas de informacao",
    "redes de computadores", "programacao", "desenvolvimento de sistemas", "banco de dados",
    "engenharia de software", "seguranca da informacao", "sistemas operacionais",
    "arquitetura de computadores", "analista de tecnologia da informacao", "tecnico de tecnologia da informacao",
    "analista de sistemas", "desenvolvedor", "software",
]

QA_TERMS = [
    "quality assurance", "qa analyst", "qa engineer", "qa automation", "automation qa",
    "analista de qa", "analista de testes", "software tester", "test analyst", "testador de software",
    "quality engineer", "sdet", "test automation", "software quality",
]


@dataclass(slots=True)
class Classification:
    plan: Plan
    priority: Priority
    opportunity_type: OpportunityType
    job_area: str | None
    confidence: float
    relevant: bool


def _first_term(text: str, terms: list[str]) -> str | None:
    for term in terms:
        if term in text:
            return term
    return None


def classify(text: str, institution: str, source_kind: str) -> Classification:
    normalized = normalize_text(text)
    computing = _first_term(normalized, COMPUTING_TERMS)
    qa = _first_term(normalized, QA_TERMS)
    is_ifpb = "ifpb" in normalize_text(institution) or source_kind.startswith("ifpb")

    if is_ifpb and source_kind == "ifpb_professor_substituto":
        return Classification(Plan.A, Priority.P0 if computing else Priority.P3,
                              OpportunityType.PROFESSOR_SUBSTITUTE, computing,
                              0.98 if computing else 0.65, bool(computing))
    if is_ifpb and source_kind == "ifpb_professor_efetivo":
        return Classification(Plan.A, Priority.P0 if computing else Priority.P3,
                              OpportunityType.PROFESSOR_EFFECTIVE, computing,
                              0.98 if computing else 0.55, bool(computing))
    if is_ifpb and source_kind == "ifpb_tae":
        return Classification(Plan.A, Priority.P2 if computing else Priority.P3,
                              OpportunityType.TAE, computing,
                              0.95 if computing else 0.55, bool(computing))
    if qa:
        return Classification(Plan.C, Priority.P2, OpportunityType.QA, qa, 0.95, True)
    if "professor" in normalized and computing:
        return Classification(Plan.B, Priority.P1, OpportunityType.PROFESSOR_OTHER, computing, 0.9, True)
    if computing:
        return Classification(Plan.OTHER, Priority.P3, OpportunityType.OTHER_IT, computing, 0.7, True)
    return Classification(Plan.OTHER, Priority.P3, OpportunityType.UNKNOWN, None, 0.4, False)
