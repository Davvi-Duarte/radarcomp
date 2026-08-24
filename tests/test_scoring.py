from datetime import datetime, timezone

from app.domain.models import Opportunity, OpportunityType, Plan, Priority
from app.scoring.engine import ScoringEngine


def make_o():
    now = datetime.now(timezone.utc)
    return Opportunity(
        id="x", title="Professor Substituto - Informática", institution="IFPB",
        plan=Plan.A, priority=Priority.P0, opportunity_type=OpportunityType.PROFESSOR_SUBSTITUTE,
        job_area="informatica", city="Campina Grande", source_url="https://x", official_url="https://x",
        first_seen_at=now, last_seen_at=now,
    )


def test_scoring_plan_a_beats_base():
    cfg = {"weights": {"ifpb_professor":100,"professor_substitute":25,"computing_area":40,"target_region":20}, "urgency_bonus_cap":10}
    engine = ScoringEngine(cfg, {"target_regions":["Campina Grande"], "degrees":[], "skills":[], "qa_skills":[]})
    o = engine.score(make_o())
    assert o.strategic_score == 185
    assert o.total_score == 185
    assert any("IFPB" in reason for reason in o.score_explanation)
