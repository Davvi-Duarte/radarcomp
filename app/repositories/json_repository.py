from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from app.domain.models import Opportunity, ScanEvent


class JsonRepository:
    def __init__(self, data_dir: str | Path = "data") -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.opportunities_path = self.data_dir / "opportunities.json"
        self.state_path = self.data_dir / "sources_state.json"
        self.history_path = self.data_dir / "history.json"

    @staticmethod
    def _read(path: Path, default):
        if not path.exists():
            return default
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    @staticmethod
    def _write(path: Path, data) -> None:
        tmp = path.with_suffix(path.suffix + ".tmp")
        with tmp.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2, sort_keys=True, default=str)
            fh.write("\n")
        tmp.replace(path)

    def load_opportunities(self) -> dict[str, Opportunity]:
        raw = self._read(self.opportunities_path, {})
        return {key: Opportunity.model_validate(value) for key, value in raw.items()}

    def save_opportunities(self, items: dict[str, Opportunity]) -> None:
        payload = {key: value.model_dump(mode="json") for key, value in sorted(items.items())}
        self._write(self.opportunities_path, payload)

    def load_state(self) -> dict:
        return self._read(self.state_path, {})

    def save_state(self, state: dict) -> None:
        self._write(self.state_path, state)

    def append_event(self, event: ScanEvent) -> None:
        history = self._read(self.history_path, [])
        history.append(event.model_dump(mode="json"))
        self._write(self.history_path, history)
