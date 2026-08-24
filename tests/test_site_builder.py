import json
from datetime import datetime, timezone

from app.domain.models import Opportunity
from app.services.site_builder import build_site_data


def test_site_does_not_publish_metadata(tmp_path):
    now = datetime.now(timezone.utc)
    o = Opportunity(id="1", title="Teste", institution="IFPB", source_url="https://source", official_url="https://official", first_seen_at=now, last_seen_at=now, metadata={"secret":"no"})
    out = tmp_path / "opportunities.json"
    build_site_data({"1":o}, out)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "metadata" not in data["opportunities"][0]
    assert data["opportunities"][0]["official_url"] == "https://official"
