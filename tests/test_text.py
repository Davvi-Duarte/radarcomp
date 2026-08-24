from app.utils.text import extract_edital_number, normalize_text, sha256_text


def test_normalize_accents():
    assert normalize_text("Tecnologia da Informação") == "tecnologia da informacao"


def test_extract_edital():
    assert extract_edital_number("Edital nº 34/2026 - Professor") == "34/2026"


def test_hash_stable():
    assert sha256_text("abc") == sha256_text("abc")
