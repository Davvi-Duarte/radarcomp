from datetime import datetime, timezone

from app.domain.models import Opportunity, Plan, Priority
from app.notifications.telegram import TelegramNotificationProvider


def test_telegram_message_contains_official_link():
    now = datetime.now(timezone.utc)
    o = Opportunity(id="1", title="Professor <Informática>", institution="IFPB", plan=Plan.A, priority=Priority.P0,
                    source_url="https://ifpb.edu.br/x", official_url="https://ifpb.edu.br/x", first_seen_at=now, last_seen_at=now,
                    total_score=150, score_explanation=["IFPB + docência"])
    provider = TelegramNotificationProvider(token="dummy", chat_id="123")
    msg = provider.format_message(o)
    assert "https://ifpb.edu.br/x" in msg
    assert "&lt;Informática&gt;" in msg
