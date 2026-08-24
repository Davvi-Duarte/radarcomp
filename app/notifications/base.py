from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.models import Opportunity


class NotificationProvider(ABC):
    @abstractmethod
    def send_opportunity(self, opportunity: Opportunity, is_update: bool = False) -> None:
        raise NotImplementedError
