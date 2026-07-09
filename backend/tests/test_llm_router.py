"""LLM router and catalog tests with mocked HTTP (no real API keys required)."""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.config import LlmProviderEntry, load_llm_catalog
from app.db.models import Base, LlmUsage
from app.services.llm.router import generate_bubble

PROFILE = {
    "recipient": {"name": "Edina"},
    "hedgehog": {"name": "Fahéj"},
    "content": {"default_language": "hu"},
}

FAKE_BUBBLE = {
    "bubble_text": "Szia Edina! Teszt üzenet a sünitől.",
    "mood": "idle",
    "language": "hu",
}


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def _mock_settings(**overrides):
    mock_settings = MagicMock()
    mock_settings.has_any_llm_key.return_value = True
    mock_settings.groq_api_key = "test-groq"
    mock_settings.gemini_api_key = None
    mock_settings.openrouter_api_key = None
    mock_settings.groq_model = "llama-3.3-70b-versatile"
    mock_settings.gemini_model = "gemini-2.0-flash"
    mock_settings.openrouter_model = "google/gemma-2-9b-it:free"
    mock_settings.llm_daily_call_limit = 50
    for k, v in overrides.items():
        setattr(mock_settings, k, v)
    return mock_settings


def _success_response(content: dict | None = None) -> MagicMock:
    payload = content or FAKE_BUBBLE
    mock_http_response = MagicMock()
    mock_http_response.status_code = 200
    mock_http_response.json.return_value = {
        "choices": [{"message": {"content": json.dumps(payload, ensure_ascii=False)}}]
    }
    mock_http_response.raise_for_status = MagicMock()
    return mock_http_response


def _error_response(status_code: int) -> MagicMock:
    mock_http_response = MagicMock()
    mock_http_response.status_code = status_code
    return mock_http_response


def _make_http_client(post_impl):
    mock_client = AsyncMock()
    mock_client.post = post_impl
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    return mock_client


@pytest.mark.asyncio
async def test_generate_bubble_uses_groq_when_configured(db_session):
    catalog = [LlmProviderEntry(name="groq", models=["llama-3.3-70b-versatile"])]
    mock_client = _make_http_client(AsyncMock(return_value=_success_response()))

    with (
        patch("app.services.llm.router.get_settings", return_value=_mock_settings()),
        patch("app.services.llm.router.load_llm_catalog", return_value=catalog),
        patch("app.services.llm.router.httpx.AsyncClient", return_value=mock_client),
    ):
        result = await generate_bubble(
            db_session,
            mood="idle",
            profile=PROFILE,
            context={},
        )

    assert result is not None
    assert result.bubble_text == FAKE_BUBBLE["bubble_text"]
    assert result.mood == "idle"


@pytest.mark.asyncio
async def test_generate_bubble_falls_back_to_second_model(db_session):
    catalog = [
        LlmProviderEntry(name="groq", models=["model-a", "model-b"]),
    ]
    calls: list[str] = []

    async def mock_post(url, **kwargs):
        model = kwargs["json"]["model"]
        calls.append(model)
        if model == "model-a":
            return _error_response(429)
        return _success_response()

    mock_client = _make_http_client(mock_post)

    with (
        patch("app.services.llm.router.get_settings", return_value=_mock_settings()),
        patch("app.services.llm.router.load_llm_catalog", return_value=catalog),
        patch("app.services.llm.router.httpx.AsyncClient", return_value=mock_client),
    ):
        result = await generate_bubble(
            db_session,
            mood="idle",
            profile=PROFILE,
            context={},
        )

    assert result is not None
    assert calls == ["model-a", "model-b"]
    usage = db_session.scalar(select(LlmUsage))
    assert usage is not None
    assert usage.provider == "bubble:groq/model-b"
    assert usage.calls == 1


@pytest.mark.asyncio
async def test_generate_bubble_falls_back_to_next_provider(db_session):
    catalog = [
        LlmProviderEntry(name="groq", models=["groq-only"]),
        LlmProviderEntry(name="gemini", models=["gemini-flash"]),
    ]

    async def mock_post(url, **kwargs):
        if "groq.com" in url:
            return _error_response(429)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": json.dumps(FAKE_BUBBLE, ensure_ascii=False)}
                        ]
                    }
                }
            ]
        }
        mock_resp.raise_for_status = MagicMock()
        return mock_resp

    mock_client = _make_http_client(mock_post)

    with (
        patch(
            "app.services.llm.router.get_settings",
            return_value=_mock_settings(gemini_api_key="test-gemini"),
        ),
        patch("app.services.llm.router.load_llm_catalog", return_value=catalog),
        patch("app.services.llm.router.httpx.AsyncClient", return_value=mock_client),
    ):
        result = await generate_bubble(
            db_session,
            mood="idle",
            profile=PROFILE,
            context={},
        )

    assert result is not None
    usage = db_session.scalar(select(LlmUsage))
    assert usage.provider == "bubble:gemini/gemini-flash"


def test_load_llm_catalog_legacy_env_when_no_yaml(tmp_path, monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "k")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("GROQ_MODEL", "legacy-groq-model")

    fake_config = tmp_path / "config"
    fake_config.mkdir()
    monkeypatch.setattr("app.config.CONFIG_DIR", fake_config)
    monkeypatch.setattr("app.config.LLM_CATALOG_PATH", fake_config / "llm_models.yaml")
    monkeypatch.setattr(
        "app.config.LLM_CATALOG_EXAMPLE_PATH", fake_config / "llm_models.example.yaml"
    )
    monkeypatch.setattr("app.config.ROOT_DIR", tmp_path)

    from app.config import Settings

    settings = Settings(_env_file=tmp_path / "missing.env")
    catalog = load_llm_catalog(settings)
    assert len(catalog) == 1
    assert catalog[0].name == "groq"
    assert catalog[0].models == ["legacy-groq-model"]


def test_load_llm_catalog_from_yaml(tmp_path, monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "k")
    monkeypatch.setenv("GEMINI_API_KEY", "g")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    fake_config = tmp_path / "config"
    fake_config.mkdir()
    yaml_path = fake_config / "llm_models.yaml"
    yaml_path.write_text(
        """
providers:
  groq:
    models:
      - alpha
      - beta
  gemini:
    models:
      - flash
  openrouter:
    models:
      - free-model
""",
        encoding="utf-8",
    )
    monkeypatch.setattr("app.config.CONFIG_DIR", fake_config)
    monkeypatch.setattr("app.config.LLM_CATALOG_PATH", yaml_path)
    monkeypatch.setattr(
        "app.config.LLM_CATALOG_EXAMPLE_PATH", fake_config / "missing.example.yaml"
    )
    monkeypatch.setattr("app.config.ROOT_DIR", tmp_path)

    from app.config import Settings

    settings = Settings(_env_file=tmp_path / "missing.env")
    catalog = load_llm_catalog(settings)
    assert [e.name for e in catalog] == ["groq", "gemini"]
    assert catalog[0].models == ["alpha", "beta"]
    assert catalog[1].models == ["flash"]
