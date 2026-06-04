from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.config import DATA_DIR, load_profile
from app.services.content_cache import get_cached, set_cached
from app.services.mood import _today_in_tz

CONTENT_DIR = DATA_DIR / "content"
PICK_SALT = "fahej-v1"

CORPUS_FILES = {
    "poem": "poems_hu.json",
    "book": "books.json",
    "movie": "movies.json",
}


def _daily_index(content_date: str, module: str, corpus_len: int) -> int:
    key = f"{content_date}:{module}:{PICK_SALT}"
    digest = hashlib.sha256(key.encode()).hexdigest()
    return int(digest, 16) % corpus_len


def _load_corpus(module: str) -> list[dict[str, Any]]:
    filename = CORPUS_FILES.get(module)
    if not filename:
        return []
    path = CONTENT_DIR / filename
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def pick_static_entry(module: str, content_date: str) -> dict[str, Any] | None:
    corpus = _load_corpus(module)
    if not corpus:
        return None
    idx = _daily_index(content_date, module, len(corpus))
    return corpus[idx]


def _format_module_text(module: str, entry: dict[str, Any]) -> str:
    if module == "poem":
        title = entry.get("title", "")
        body = entry.get("body", "")
        author = entry.get("author", "")
        parts = [p for p in [title, body, f"— {author}" if author else ""] if p]
        return "\n\n".join(parts)
    if module == "book":
        return f"{entry.get('title', '')} — {entry.get('author', '')}\n{entry.get('blurb', '')}"
    if module == "movie":
        return f"{entry.get('title', '')} ({entry.get('year', '')})\n{entry.get('blurb', '')}"
    return entry.get("text", str(entry))


async def generate_module_content(
    db: Session,
    module: str,
    profile: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    profile = profile or load_profile()
    content_date = _today_in_tz(profile).isoformat()
    cached = get_cached(db, content_date, module)
    if cached:
        return cached

    entry = pick_static_entry(module, content_date)
    if not entry:
        return None

    text = _format_module_text(module, entry)
    payload: dict[str, Any] = {
        "module": module,
        "text": text,
        "title": entry.get("title"),
        "source": "corpus",
        "content_date": content_date,
    }

    set_cached(db, content_date, module, payload)
    return payload


_MODULE_ALIASES = {"poems": "poem", "books": "book", "movies": "movie"}


def _module_enabled(modules: dict[str, Any], module: str) -> bool:
    if modules.get(module, False):
        return True
    for alias, canonical in _MODULE_ALIASES.items():
        if canonical == module and modules.get(alias, False):
            return True
    return False


def get_enabled_modules(profile: dict[str, Any]) -> list[str]:
    modules = profile.get("modules_enabled", {})
    return [m for m in ("poem", "book", "movie") if _module_enabled(modules, m)]
