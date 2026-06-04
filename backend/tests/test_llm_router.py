"""LLM router tests with mocked HTTP (no real API keys required)."""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base
from app.services.llm.router import generate_bubble


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.mark.asyncio
async def test_generate_bubble_uses_groq_when_configured(db_session):
    profile = {
        "recipient": {"name": "Edina"},
        "hedgehog": {"name": "Fahéj"},
        "content": {"default_language": "hu"},
    }
    fake_response = {
        "bubble_text": "Szia Edina! Teszt üzenet a sünitől.",
        "mood": "idle",
        "language": "hu",
    }

    mock_http_response = MagicMock()
    mock_http_response.status_code = 200
    mock_http_response.json.return_value = {
        "choices": [{"message": {"content": json.dumps(fake_response, ensure_ascii=False)}}]
    }
    mock_http_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_http_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    mock_settings = MagicMock()
    mock_settings.has_any_llm_key.return_value = True
    mock_settings.groq_api_key = "test-groq"
    mock_settings.gemini_api_key = None
    mock_settings.openrouter_api_key = None
    mock_settings.groq_model = "llama-3.3-70b-versatile"
    mock_settings.gemini_model = "gemini-2.0-flash"
    mock_settings.openrouter_model = "google/gemma-2-9b-it:free"
    mock_settings.llm_daily_call_limit = 50

    with (
        patch("app.services.llm.router.get_settings", return_value=mock_settings),
        patch("app.services.llm.router.httpx.AsyncClient", return_value=mock_client),
    ):
        result = await generate_bubble(
            db_session,
            mood="idle",
            profile=profile,
            context={},
        )

    assert result is not None
    assert result.bubble_text == fake_response["bubble_text"]
    assert result.mood == "idle"
