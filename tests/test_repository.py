from datetime import datetime, timezone

from app.domain.models import Opportunity
from app.repositories.json_repository import JsonRepository


def test_repository_roundtrip(tmp_path):
    repo = JsonRepository(tmp_path)
    now = datetime.now(timezone.utc)
    item = Opportunity(id="abc", title="Teste", institution="IFPB", source_url="https://x", official_url="https://x", first_seen_at=now, last_seen_at=now)
    repo.save_opportunities({item.id:item})
    loaded = repo.load_opportunities()
    assert loaded["abc"].title == "Teste"
