from datetime import datetime, timezone

from app.domain.models import Opportunity
from app.services.dedup import find_duplicate


def o(id_, title, edital):
    now = datetime.now(timezone.utc)
    return Opportunity(id=id_, title=title, institution="IFPB", edital_number=edital, source_url="https://x", official_url="https://x", first_seen_at=now, last_seen_at=now)


def test_same_edital_is_duplicate():
    old = o("1", "Edital Professor", "34/2026")
    new = o("2", "Notícia sobre edital", "34/2026")
    assert find_duplicate(new, [old]).id == "1"
