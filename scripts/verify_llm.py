"""Check LLM keys in .env and optionally test /api/today against running backend."""
import json
import os
import sqlite3
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

load_dotenv(ROOT / ".env")


def key_ok(name: str) -> bool:
    v = os.getenv(name, "")
    return bool(v and v.strip())


def print_catalog() -> None:
    try:
        from app.config import load_llm_catalog

        catalog = load_llm_catalog()
        if not catalog:
            print("LLM catalog: (empty — add API keys or check config/llm_models.yaml)")
            return
        print("LLM catalog (fallback order):")
        for entry in catalog:
            print(f"  {entry.name}: {len(entry.models)} model(s)")
            for model in entry.models:
                print(f"    - {model}")
    except Exception as e:
        print(f"LLM catalog: could not load ({e})")


def main() -> int:
    keys = {
        "GROQ_API_KEY": key_ok("GROQ_API_KEY"),
        "GEMINI_API_KEY": key_ok("GEMINI_API_KEY"),
        "OPENROUTER_API_KEY": key_ok("OPENROUTER_API_KEY"),
    }
    print("Keys configured:")
    for k, ok in keys.items():
        print(f"  {k}: {'yes' if ok else 'no'}")

    if not any(keys.values()):
        print("\nNo LLM keys in .env. Run: .\\scripts\\configure-llm.ps1")
        return 1

    print()
    print_catalog()

    try:
        import httpx
    except ImportError:
        print("httpx not installed")
        return 1

    base = "http://127.0.0.1:8000"
    pw = os.getenv("APP_PASSWORD", "changeme")
    try:
        with httpx.Client(base_url=base, timeout=60.0) as c:
            if c.get("/health").status_code != 200:
                print(f"\nBackend not healthy at {base} — start .\\scripts\\start-backend.ps1")
                return 1
            c.post("/api/auth/login", json={"password": pw})
            r = c.get("/api/today")
            r.raise_for_status()
            data = r.json()
            print("\n/api/today OK")
            print("bubble preview:", data.get("bubble_text", "")[:100], "...")
    except httpx.ConnectError:
        print(f"\nCannot connect to {base} — start backend first.")
        return 1

    db = ROOT / "data" / "app.db"
    if db.exists():
        conn = sqlite3.connect(db)
        row = conn.execute(
            "SELECT payload_json FROM daily_content WHERE module='bubble' ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if row:
            src = json.loads(row[0]).get("source", "?")
            print("cache source:", src)
            if src != "llm":
                print("  -> Expected 'llm'. Run clear-bubble-cache.ps1 and call /api/today again.")
        else:
            print("cache: no bubble row yet")
        usage = conn.execute(
            "SELECT usage_date, provider, calls, tokens FROM llm_usage"
        ).fetchall()
        print("llm_usage:", usage if usage else "(empty)")
        conn.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
