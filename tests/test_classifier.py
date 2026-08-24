from app.domain.models import OpportunityType, Plan, Priority
from app.services.classifier import classify


def test_ifpb_substitute_computing_is_p0():
    result = classify("Professor Substituto de Informática", "IFPB", "ifpb_professor_substituto")
    assert result.relevant is True
    assert result.plan == Plan.A
    assert result.priority == Priority.P0
    assert result.opportunity_type == OpportunityType.PROFESSOR_SUBSTITUTE


def test_ifpb_non_computing_is_not_relevant():
    result = classify("Professor Substituto de Língua Inglesa", "IFPB", "ifpb_professor_substituto")
    assert result.relevant is False


def test_qa_is_plan_c():
    result = classify("QA Engineer com Playwright", "Empresa", "job_site")
    assert result.plan == Plan.C
    assert result.priority == Priority.P2
