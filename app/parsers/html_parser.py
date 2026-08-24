from __future__ import annotations

from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.domain.models import DocumentLink, ListingEntry
from app.utils.text import normalize_html_text


PT_DATETIME_FORMATS = (
    "%d/%m/%Y, %H:%M",
    "%d/%m/%Y %Hh%M",
    "%d/%m/%Y %H:%M",
    "%d/%m/%Y",
)


def parse_pt_datetime(value: str) -> datetime | None:
    value = normalize_html_text(value)
    for fmt in PT_DATETIME_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def _content_root(soup: BeautifulSoup):
    return soup.find("main") or soup.select_one("#content-core") or soup.select_one("#content") or soup


def parse_plone_listing(html: str, base_url: str, source_name: str, source_kind: str) -> list[ListingEntry]:
    soup = BeautifulSoup(html, "html.parser")
    root = _content_root(soup)
    entries: list[ListingEntry] = []
    seen: set[str] = set()

    for heading in root.find_all(["h2", "h3"]):
        anchor = heading.find("a", href=True)
        if anchor is None and heading.parent is not None:
            anchor = heading.parent.find("a", href=True)
        if anchor is None:
            continue
        title = normalize_html_text(heading.get_text(" ", strip=True))
        if not title.lower().startswith("edital"):
            continue
        url = urljoin(base_url, anchor["href"])
        if url in seen:
            continue
        seen.add(url)
        description = ""
        sibling = heading.find_next_sibling()
        if sibling is not None and sibling.name in {"p", "div"}:
            description = normalize_html_text(sibling.get_text(" ", strip=True))
        elif anchor.parent is not None:
            text = normalize_html_text(anchor.parent.get_text(" ", strip=True))
            if text.startswith(title):
                description = text[len(title):].strip(" -–—")
        entries.append(ListingEntry(title=title, description=description, url=url, source_name=source_name, source_kind=source_kind))

    if entries:
        return entries

    # Fallback for Plone result cards where the link wraps the heading.
    for anchor in root.find_all("a", href=True):
        heading = anchor.find(["h2", "h3"])
        if not heading:
            continue
        title = normalize_html_text(heading.get_text(" ", strip=True))
        if not title.lower().startswith("edital"):
            continue
        url = urljoin(base_url, anchor["href"])
        if url in seen:
            continue
        seen.add(url)
        description = ""
        p = anchor.find("p")
        if p:
            description = normalize_html_text(p.get_text(" ", strip=True))
        entries.append(ListingEntry(title=title, description=description, url=url, source_name=source_name, source_kind=source_kind))
    return entries


def parse_plone_detail(html: str, base_url: str) -> tuple[str, str, list[DocumentLink]]:
    soup = BeautifulSoup(html, "html.parser")
    root = _content_root(soup)
    h1 = root.find("h1") or soup.find("h1")
    title = normalize_html_text(h1.get_text(" ", strip=True)) if h1 else ""

    description = ""
    if h1:
        for node in h1.find_all_next(["p", "div"], limit=8):
            text = normalize_html_text(node.get_text(" ", strip=True))
            if text and len(text) > 25 and "Título" not in text:
                description = text
                break

    docs: list[DocumentLink] = []
    table = root.find("table") or soup.find("table")
    if table:
        for row in table.find_all("tr"):
            cells = row.find_all(["td", "th"])
            if len(cells) < 1:
                continue
            anchor = row.find("a", href=True)
            if not anchor:
                continue
            doc_title = normalize_html_text(anchor.get_text(" ", strip=True))
            doc_url = urljoin(base_url, anchor["href"])
            desc = normalize_html_text(cells[1].get_text(" ", strip=True)) if len(cells) >= 2 else ""
            published = parse_pt_datetime(cells[2].get_text(" ", strip=True)) if len(cells) >= 3 else None
            docs.append(DocumentLink(
                title=doc_title,
                description=desc,
                published_at=published,
                url=doc_url,
                is_pdf=doc_url.lower().split("?", 1)[0].endswith(".pdf"),
            ))

    return title, description, docs


def find_next_page_url(html: str, base_url: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    root = _content_root(soup)
    for anchor in root.find_all("a", href=True):
        text = anchor.get_text(" ", strip=True).lower()
        rel = " ".join(anchor.get("rel", [])) if isinstance(anchor.get("rel"), list) else str(anchor.get("rel", ""))
        if "próxima" in text or "proxima" in text or "next" in rel.lower():
            return urljoin(base_url, anchor["href"])
    return None
