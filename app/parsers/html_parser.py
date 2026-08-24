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
    return (
        soup.select_one("#content-core")
        or soup.select_one("#content")
        or soup.find("main")
        or soup
    )


def parse_plone_listing(
    html: str,
    base_url: str,
    source_name: str,
    source_kind: str,
) -> list[ListingEntry]:
    soup = BeautifulSoup(html, "html.parser")
    root = _content_root(soup)

    entries: list[ListingEntry] = []
    seen: set[str] = set()

    def find_card(anchor):
        """
        Procura o menor container razoável que represente
        um item da listagem.
        """
        node = anchor

        for _ in range(6):
            parent = getattr(node, "parent", None)

            if parent is None:
                break

            classes = " ".join(parent.get("class", []))

            if (
                parent.name in {"article", "li"}
                or any(
                    word in classes.lower()
                    for word in (
                        "listing",
                        "card",
                        "tile",
                        "item",
                        "result",
                        "summary",
                    )
                )
            ):
                return parent

            if parent == root:
                break

            node = parent

        return anchor.parent

    def find_title(anchor) -> str:
        # Caso 1:
        # <a><h2>Edital...</h2></a>
        heading = anchor.find(["h2", "h3", "h4"])

        if heading:
            title = normalize_html_text(
                heading.get_text(" ", strip=True)
            )

            if title.lower().startswith("edital"):
                return title

        # Caso 2:
        # <h2><a>Edital...</a></h2>
        text = normalize_html_text(
            anchor.get_text(" ", strip=True)
        )

        if text.lower().startswith("edital"):
            return text

        # Caso 3:
        # <h2>Edital...</h2>
        # <a href="..."></a>
        #
        # ou outras variações do Plone.
        node = anchor

        for _ in range(6):
            parent = getattr(node, "parent", None)

            if parent is None:
                break

            heading = parent.find(["h2", "h3", "h4"])

            if heading:
                title = normalize_html_text(
                    heading.get_text(" ", strip=True)
                )

                if title.lower().startswith("edital"):
                    return title

            if parent == root:
                break

            node = parent

        # Alguns layouts podem usar title/aria-label.
        for attribute in ("title", "aria-label"):
            value = anchor.get(attribute)

            if value:
                title = normalize_html_text(value)

                if title.lower().startswith("edital"):
                    return title

        return ""

    def find_description(anchor, title: str) -> str:
        card = find_card(anchor)

        if card:
            paragraph = card.find("p")

            if paragraph:
                description = normalize_html_text(
                    paragraph.get_text(" ", strip=True)
                )

                if description and description != title:
                    return description

        # Fallback para título seguido por descrição.
        node = anchor

        for _ in range(5):
            parent = getattr(node, "parent", None)

            if parent is None:
                break

            heading = parent.find(["h2", "h3", "h4"])

            if heading:
                sibling = heading.find_next_sibling()

                if sibling is not None and sibling.name in {
                    "p",
                    "div",
                }:
                    description = normalize_html_text(
                        sibling.get_text(" ", strip=True)
                    )

                    if description:
                        return description

            if parent == root:
                break

            node = parent

        return ""

    # Em vez de presumir a estrutura exata do Plone,
    # analisamos todos os links do conteúdo.
    for anchor in root.find_all("a", href=True):
        title = find_title(anchor)

        if not title:
            continue

        href = str(anchor.get("href", "")).strip()

        if not href:
            continue

        url = urljoin(base_url, href)

        # Arquivos não são páginas de oportunidade.
        clean_url = url.lower().split("?", 1)[0]

        if clean_url.endswith(
            (
                ".pdf",
                ".doc",
                ".docx",
                ".xls",
                ".xlsx",
                ".zip",
            )
        ):
            continue

        if url in seen:
            continue

        seen.add(url)

        description = find_description(anchor, title)

        entries.append(
            ListingEntry(
                title=title,
                description=description,
                url=url,
                source_name=source_name,
                source_kind=source_kind,
            )
        )

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
