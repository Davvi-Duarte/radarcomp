from app.domain.models import LLMExtraction
from app.llm.gemini import _sanitize_schema


def test_schema_removes_unsupported_default():
    schema = _sanitize_schema(LLMExtraction.model_json_schema())
    text = str(schema)
    assert "'default'" not in text
    assert "properties" in schema
