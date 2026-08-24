from __future__ import annotations

import logging

from app.domain.models import ListingEntry
from app.parsers.html_parser import find_next_page_url, parse_plone_listing
from app.sources.base import BaseSource
from app.utils.http import HttpClient

logger = logging.getLogger(__name__)


class IFPBSource(BaseSource):
    def __init__(self, source_config: dict, http: HttpClient | None = None) -> None:
        self.config = source_config
        self.http = http or HttpClient()

    def list_entries(self) -> list[ListingEntry]:
        entries: list[ListingEntry] = []
        for section in self.config.get("sections", []):
            if not section.get("enabled", True):
                continue
            url = section["url"]
            name = section["name"]
            kind = section["kind"]
            try:
                current_url = url
                visited: set[str] = set()
                section_entries: list[ListingEntry] = []
                while current_url and current_url not in visited and len(visited) < 20:
                    visited.add(current_url)
                    response = self.http.get(current_url)
                    section_entries.extend(parse_plone_listing(response.text, current_url, name, kind))
                    current_url = find_next_page_url(response.text, current_url)
                unique = {item.url: item for item in section_entries}
                parsed = list(unique.values())
                logger.info("IFPB section %s: %d edital(s) across %d page(s)", name, len(parsed), len(visited))
                entries.extend(parsed)
            except Exception as exc:  # source isolation is intentional
                logger.exception("Failed IFPB section %s (%s): %s", name, url, exc)
        return entries
