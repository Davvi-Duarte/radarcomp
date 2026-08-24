from __future__ import annotations

import html
import os

import requests

from app.domain.models import Opportunity
from app.notifications.base import NotificationProvider


class TelegramNotificationProvider(NotificationProvider):
    def __init__(self, token: str | None = None, chat_id: str | None = None, timeout: int = 20) -> None:
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        self.timeout = timeout
        if not self.token or not self.chat_id:
            raise ValueError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are required")

    def format_message(self, o: Opportunity, is_update: bool = False) -> str:
        header = "🔄 <b>RADARCOMP — ATUALIZAÇÃO</b>" if is_update else "🚨 <b>RADARCOMP — NOVA OPORTUNIDADE</b>"
        reasons = "\n".join(f"• {html.escape(r)}" for r in o.score_explanation[:5]) or "• aderência detectada pelo RadarComp"
        deadline = o.registration_end.strftime("%d/%m/%Y") if o.registration_end else "não extraído"
        area = html.escape(o.job_area or "Computação / verificar edital")
        campus = html.escape(o.campus or o.city or "não identificado")
        return (
            f"{header}\n\n"
            f"<b>{html.escape(o.title)}</b>\n"
            f"{html.escape(o.institution)} — {campus}\n\n"
            f"Plano: <b>{o.plan}</b> | Prioridade: <b>{o.priority}</b>\n"
            f"Score: <b>{o.total_score:g}</b>\n"
            f"Área: {area}\n"
            f"Inscrições até: {deadline}\n\n"
            f"<b>Por que é relevante</b>\n{reasons}\n\n"
            f'<a href="{html.escape(o.official_url)}">Ver fonte oficial</a>'
        )

    def send_opportunity(self, opportunity: Opportunity, is_update: bool = False) -> None:
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        response = requests.post(url, json={
            "chat_id": self.chat_id,
            "text": self.format_message(opportunity, is_update=is_update),
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        }, timeout=self.timeout)
        response.raise_for_status()
