from __future__ import annotations

from pathlib import Path
from typing import Any

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
    prefetch_secret: str | None = Field(default=None, alias="PREFETCH_SECRET")
    enable_scheduler: bool = Field(default=True, alias="ENABLE_SCHEDULER")

    def has_any_llm_key(self) -> bool:
        return bool(self.groq_api_key or self.gemini_api_key or self.openrouter_api_key)


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
