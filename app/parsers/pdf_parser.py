from __future__ import annotations

from io import BytesIO

from pypdf import PdfReader


def extract_pdf_text(content: bytes, max_pages: int = 30, max_chars: int = 120_000) -> str:
    reader = PdfReader(BytesIO(content))
    chunks: list[str] = []
    chars = 0
    for page in reader.pages[:max_pages]:
        text = page.extract_text() or ""
        if text:
            remaining = max_chars - chars
            if remaining <= 0:
                break
            text = text[:remaining]
            chunks.append(text)
            chars += len(text)
    return "\n".join(chunks).strip()
