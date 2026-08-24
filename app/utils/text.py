from __future__ import annotations

import hashlib
import re
import unicodedata


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.lower()
    value = re.sub(r"\s+", " ", value).strip()
    return value


def normalize_html_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="ignore")).hexdigest()


def stable_id(*parts: str | None) -> str:
    raw = "|".join(normalize_text(p or "") for p in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


def extract_edital_number(text: str) -> str | None:
    m = re.search(r"edital\s*(?:n[º°o.]*)?\s*(\d+)\s*/\s*(\d{4})", normalize_text(text))
    if not m:
        return None
    return f"{int(m.group(1))}/{m.group(2)}"
