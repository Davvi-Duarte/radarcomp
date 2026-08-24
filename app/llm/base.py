from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.models import LLMExtraction


class LLMProvider(ABC):
    @abstractmethod
    def extract_opportunity(self, text: str, context: dict) -> LLMExtraction:
        raise NotImplementedError
