from __future__ import annotations

import json
from pathlib import Path

from app.domain.models import Opportunity


PUBLIC_FIELDS = {
    "id", "title", "institution", "institution_type", "plan", "priority", "opportunity_type",
    "job_area", "city", "state", "campus", "work_mode", "contract_type", "number_of_positions",
    "salary", "workload", "publication_date", "registration_start", "registration_end", "official_url",
    "edital_url", "edital_number", "description", "strategic_score", "compatibility_score",
    "urgency_score", "total_score", "score_explanation", "first_seen_at", "last_seen_at", "status",
}


def build_site_data(opportunities: dict[str, Opportunity], output: str | Path = "site/data/opportunities.json") -> None:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    items = []
    for o in opportunities.values():
        raw = o.model_dump(mode="json")
        items.append({key: raw.get(key) for key in PUBLIC_FIELDS})
    items.sort(key=lambda x: (x.get("priority", "P9"), -(x.get("total_score") or 0)))
    latest = max((o.last_seen_at for o in opportunities.values()), default=None)
    payload = {
        "generated_at": latest.isoformat() if latest else None,
        "count": len(items),
        "opportunities": items,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
