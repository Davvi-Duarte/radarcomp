from __future__ import annotations

from datetime import date

from app.domain.models import Opportunity, OpportunityType, Plan
from app.utils.text import normalize_text


class ScoringEngine:
    def __init__(self, config: dict, profile: dict) -> None:
        self.config = config
        self.profile = profile

    def score(self, opportunity: Opportunity) -> Opportunity:
        weights = self.config.get("weights", {})
        strategic = 0.0
        compatibility = 0.0
        reasons: list[str] = []

        if opportunity.institution.upper() == "IFPB" and opportunity.opportunity_type in {
            OpportunityType.PROFESSOR_EFFECTIVE, OpportunityType.PROFESSOR_SUBSTITUTE
        }:
            v = float(weights.get("ifpb_professor", 100))
            strategic += v
            reasons.append(f"IFPB + docência (+{v:g})")
        elif opportunity.institution.upper() == "IFPB" and opportunity.opportunity_type == OpportunityType.TAE:
            v = float(weights.get("ifpb_it", 20))
            strategic += v
            reasons.append(f"Cargo de TI no IFPB (+{v:g})")

        if opportunity.opportunity_type == OpportunityType.PROFESSOR_EFFECTIVE:
            v = float(weights.get("professor_effective", 30)); strategic += v; reasons.append(f"Professor efetivo (+{v:g})")
        if opportunity.opportunity_type == OpportunityType.PROFESSOR_SUBSTITUTE:
            v = float(weights.get("professor_substitute", 25)); strategic += v; reasons.append(f"Professor substituto (+{v:g})")
        if opportunity.plan == Plan.B:
            v = float(weights.get("private_teaching", 60)); strategic += v; reasons.append(f"Docência estratégica (+{v:g})")
        if opportunity.plan == Plan.C:
            v = float(weights.get("qa", 20)); strategic += v; reasons.append(f"Plano C / QA (+{v:g})")

        if opportunity.job_area:
            v = float(weights.get("computing_area", 40)); strategic += v; reasons.append(f"Área de Computação (+{v:g})")

        city = normalize_text(opportunity.city or opportunity.campus or "")
        target_regions = [normalize_text(x) for x in self.profile.get("target_regions", [])]
        if city and any(region and region in city for region in target_regions):
            v = float(weights.get("target_region", 20)); strategic += v; reasons.append(f"Região prioritária (+{v:g})")

        profile_degrees = [normalize_text(x) for x in self.profile.get("degrees", [])]
        accepted = [normalize_text(x) for x in opportunity.accepted_degrees]
        if profile_degrees and accepted:
            if any(p in a or a in p for p in profile_degrees for a in accepted if p and a):
                v = float(weights.get("degree_match", 20)); compatibility += v; reasons.append(f"Formação compatível (+{v:g})")
            else:
                v = float(weights.get("degree_partial", 10)); compatibility += v; reasons.append(f"Formação possivelmente compatível (+{v:g})")

        skills = {normalize_text(x) for x in self.profile.get("skills", []) + self.profile.get("qa_skills", [])}
        technologies = {normalize_text(x) for x in opportunity.technologies}
        overlap = {x for x in skills & technologies if x}
        if overlap:
            per_skill = float(weights.get("skill_match_each", 3))
            cap = float(weights.get("skill_match_cap", 15))
            bonus = min(cap, len(overlap) * per_skill)
            compatibility += bonus
            reasons.append(f"Skills aderentes (+{bonus:g})")

        urgency = self._urgency(opportunity.registration_end)
        urgency_cap = float(self.config.get("urgency_bonus_cap", 10))
        urgency_bonus = min(urgency_cap, urgency)

        opportunity.strategic_score = round(strategic, 2)
        opportunity.compatibility_score = round(compatibility, 2)
        opportunity.urgency_score = round(urgency, 2)
        opportunity.total_score = round(strategic + compatibility + urgency_bonus, 2)
        opportunity.score_explanation = reasons
        return opportunity

    def _urgency(self, end: date | None) -> float:
        if not end:
            return 0.0
        days = (end - date.today()).days
        if days < 0:
            return 0.0
        tiers = self.config.get("urgency", {})
        if days <= 2:
            return float(tiers.get("days_2", 10))
        if days <= 7:
            return float(tiers.get("days_7", 7))
        if days <= 14:
            return float(tiers.get("days_14", 4))
        return 0.0
