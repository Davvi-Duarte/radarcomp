from pathlib import Path

from app.parsers.html_parser import parse_plone_detail, parse_plone_listing

FIX = Path(__file__).parent / "fixtures"


def test_parse_listing():
    html = (FIX / "ifpb_listing.html").read_text(encoding="utf-8")
    items = parse_plone_listing(html, "https://www.ifpb.edu.br/concursopublico/professor-substituto/vigentes", "sub", "ifpb_professor_substituto")
    assert len(items) == 2
    assert items[0].title.startswith("Edital nº 34/2026")
    assert items[0].url.startswith("https://www.ifpb.edu.br/")
    assert "Informática" in items[0].description


def test_parse_detail_table():
    html = (FIX / "ifpb_detail.html").read_text(encoding="utf-8")
    title, description, docs = parse_plone_detail(html, "https://www.ifpb.edu.br/x/")
    assert "34/2026" in title
    assert "Informática" in description
    assert len(docs) == 3
    assert docs[1].is_pdf
    assert docs[1].published_at.year == 2026


def test_find_next_page():
    from app.parsers.html_parser import find_next_page_url
    html = (FIX / "ifpb_listing_paginated.html").read_text(encoding="utf-8")
    url = find_next_page_url(html, "https://www.ifpb.edu.br/list")
    assert url == "https://www.ifpb.edu.br/list?b_start:int=25"
