from pathlib import Path

from app.config.loader import load_yaml
from app.domain.models import ListingEntry, Priority
from app.repositories.json_repository import JsonRepository
from app.scoring.engine import ScoringEngine
from app.services.scanner import Scanner
from app.sources.base import BaseSource

FIX = Path(__file__).parent / "fixtures"


class FakeSource(BaseSource):
    def list_entries(self):
        return [ListingEntry(
            title="Edital nº 34/2026 - Professor Substituto do IFPB",
            description="Professor substituto de Informática",
            url="https://example.test/edital-34",
            source_name="IFPB Professor Substituto",
            source_kind="ifpb_professor_substituto",
        )]


class FakeResponse:
    def __init__(self, text="", content=b""):
        self.text = text
        self.content = content


class FakeHttp:
    def get(self, url):
        assert url == "https://example.test/edital-34"
        return FakeResponse(text=(FIX / "ifpb_detail.html").read_text(encoding="utf-8"))


def test_scanner_creates_p0_without_network(tmp_path):
    repo = JsonRepository(tmp_path)
    scoring = ScoringEngine(load_yaml("config/scoring.yaml"), {"target_regions":[],"degrees":[],"skills":[],"qa_skills":[]})
    scanner = Scanner(FakeSource(), repo, scoring, http=FakeHttp())
    stats = scanner.scan()
    items = repo.load_opportunities()
    assert stats["new"] == 1
    assert len(items) == 1
    item = next(iter(items.values()))
    assert item.priority == Priority.P0
    assert item.total_score >= 165


def test_second_identical_scan_is_skipped(tmp_path):
    repo = JsonRepository(tmp_path)
    scoring = ScoringEngine(load_yaml("config/scoring.yaml"), {"target_regions":[],"degrees":[],"skills":[],"qa_skills":[]})
    scanner = Scanner(FakeSource(), repo, scoring, http=FakeHttp())
    first = scanner.scan()
    opportunities_before = (tmp_path / "opportunities.json").read_text(encoding="utf-8")
    history_before = (tmp_path / "history.json").read_text(encoding="utf-8")
    second = scanner.scan()
    assert first["new"] == 1
    assert second["skipped"] == 1
    assert (tmp_path / "opportunities.json").read_text(encoding="utf-8") == opportunities_before
    assert (tmp_path / "history.json").read_text(encoding="utf-8") == history_before
