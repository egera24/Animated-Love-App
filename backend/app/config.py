from __future__ import annotations

import json
import logging
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# #region agent log
try:
    _dbg = Path(__file__).resolve().parents[2] / "debug-ad283c.log"
    _dbg.write_text(
        json.dumps(
            {
                "sessionId": "ad283c",
                "runId": "pre-fix",
                "hypothesisId": "H2",
                "location": "config.py:import",
                "message": "python environment before pydantic_settings import",
                "data": {
                    "executable": sys.executable,
                    "prefix": sys.prefix,
                    "base_prefix": getattr(sys, "base_prefix", None),
                    "in_venv": sys.prefix != getattr(sys, "base_prefix", sys.prefix),
                    "version": sys.version,
                },
                "timestamp": int(time.time() * 1000),
            }
        )
        + "\n",
        encoding="utf-8",
    )
except Exception:
    pass
# #endregion

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT_DIR / "config"
DATA_DIR = ROOT_DIR / "data"

CITY_COORDS: dict[str, tuple[float, float]] = {
    "Szeged": (46.253, 20.148),
    "Budapest": (47.4979, 19.0402),
}

logger = logging.getLogger(__name__)

LLM_CATALOG_PATH = CONFIG_DIR / "llm_models.yaml"
LLM_CATALOG_EXAMPLE_PATH = CONFIG_DIR / "llm_models.example.yaml"

_PROVIDER_KEY_ATTR: dict[str, str] = {
    "groq": "groq_api_key",
    "gemini": "gemini_api_key",
    "openrouter": "openrouter_api_key",
}


@dataclass(frozen=True)
class LlmProviderEntry:
    name: str
    models: list[str]


def _provider_has_key(settings: Settings, provider: str) -> bool:
    attr = _PROVIDER_KEY_ATTR.get(provider)
    if not attr:
        return False
    key = getattr(settings, attr, None)
    return bool(key and str(key).strip())


def _parse_catalog_yaml(data: dict[str, Any]) -> list[LlmProviderEntry]:
    providers_raw = data.get("providers")
    if not isinstance(providers_raw, dict):
        return []
    entries: list[LlmProviderEntry] = []
    for name, cfg in providers_raw.items():
        if not isinstance(cfg, dict):
            continue
        models_raw = cfg.get("models")
        if not isinstance(models_raw, list):
            continue
        models = [str(m).strip() for m in models_raw if m and str(m).strip()]
        if models:
            entries.append(LlmProviderEntry(name=str(name), models=models))
    return entries


def _legacy_catalog_from_env(settings: Settings) -> list[LlmProviderEntry]:
    """Single-model catalog from legacy GROQ_MODEL / GEMINI_MODEL / OPENROUTER_MODEL."""
    entries: list[LlmProviderEntry] = []
    if _provider_has_key(settings, "groq"):
        entries.append(LlmProviderEntry(name="groq", models=[settings.groq_model]))
    if _provider_has_key(settings, "gemini"):
        entries.append(LlmProviderEntry(name="gemini", models=[settings.gemini_model]))
    if _provider_has_key(settings, "openrouter"):
        entries.append(
            LlmProviderEntry(name="openrouter", models=[settings.openrouter_model])
        )
    return entries


def load_llm_catalog(settings: Settings | None = None) -> list[LlmProviderEntry]:
    """Load ordered provider/model catalog; filter to providers with API keys."""
    settings = settings or get_settings()
    path = LLM_CATALOG_PATH if LLM_CATALOG_PATH.exists() else LLM_CATALOG_EXAMPLE_PATH
    entries: list[LlmProviderEntry] = []
    if path.exists():
        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        if isinstance(data, dict):
            entries = _parse_catalog_yaml(data)
    if not entries:
        entries = _legacy_catalog_from_env(settings)
    filtered = [e for e in entries if _provider_has_key(settings, e.name)]
    if not filtered and settings.has_any_llm_key():
        logger.warning("LLM catalog empty after filtering; check config/llm_models.yaml")
    return filtered


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_password: str = Field(default="changeme", alias="APP_PASSWORD")
    session_secret: str = Field(default="dev-secret-change-me", alias="SESSION_SECRET")
    media_store: str = Field(default="local", alias="MEDIA_STORE")
    database_url: str = Field(
        default=f"sqlite:///{ROOT_DIR / 'data' / 'app.db'}",
        alias="DATABASE_URL",
    )

    groq_api_key: str | None = Field(default=None, alias="GROQ_API_KEY")
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    openrouter_api_key: str | None = Field(default=None, alias="OPENROUTER_API_KEY")
    groq_model: str = Field(default="llama-3.3-70b-versatile", alias="GROQ_MODEL")
    gemini_model: str = Field(default="gemini-2.0-flash", alias="GEMINI_MODEL")
    openrouter_model: str = Field(
        default="google/gemma-2-9b-it:free",
        alias="OPENROUTER_MODEL",
    )
    llm_daily_call_limit: int = Field(default=50, alias="LLM_DAILY_CALL_LIMIT")
    llm_chat_daily_call_limit: int = Field(default=300, alias="LLM_CHAT_DAILY_CALL_LIMIT")
    chat_history_turns: int = Field(default=12, alias="CHAT_HISTORY_TURNS")
    prefetch_secret: str | None = Field(default=None, alias="PREFETCH_SECRET")
    enable_scheduler: bool = Field(default=True, alias="ENABLE_SCHEDULER")

    def has_any_llm_key(self) -> bool:
        keys = (self.groq_api_key, self.gemini_api_key, self.openrouter_api_key)
        return any(k and str(k).strip() for k in keys)


def get_settings() -> Settings:
    """Load settings from .env on each call (no cache — .env edits need a process restart)."""
    return Settings()


def load_profile() -> dict[str, Any]:
    path = CONFIG_DIR / "profile.yaml"
    if not path.exists():
        path = CONFIG_DIR / "profile.example.yaml"
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def weather_coords(profile: dict[str, Any]) -> tuple[float, float, str]:
    city = profile.get("locations", {}).get("weather_primary", "Szeged")
    lat, lon = CITY_COORDS.get(city, CITY_COORDS["Szeged"])
    return lat, lon, city
