from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.models import ListingEntry


class BaseSource(ABC):
    @abstractmethod
    def list_entries(self) -> list[ListingEntry]:
        raise NotImplementedError
