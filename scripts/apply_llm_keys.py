"""Merge LLM keys from .env.llm.local into .env (gitignored local secrets file)."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / ".env"
LOCAL = ROOT / ".env.llm.local"
NAMES = (
    "GROQ_API_KEY",
    "GEMINI_API_KEY",
    "OPENROUTER_API_KEY",
    "GROQ_MODEL",
    "GEMINI_MODEL",
    "OPENROUTER_MODEL",
    "LLM_DAILY_CALL_LIMIT",
    "PREFETCH_SECRET",
    "ENABLE_SCHEDULER",
)


def parse_env(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        out[k.strip()] = v.strip()
    return out


def main() -> int:
    if not LOCAL.exists():
        print(f"Create {LOCAL.name} from .env.llm.local.example and add your API keys.")
        return 1

    local = parse_env(LOCAL)
    merged = {k: local[k] for k in NAMES if local.get(k)}
    if not any(merged.get(k) for k in ("GROQ_API_KEY", "GEMINI_API_KEY", "OPENROUTER_API_KEY")):
        print("No API keys found in .env.llm.local")
        return 1

    content = ENV.read_text(encoding="utf-8") if ENV.exists() else ""
    for name, value in merged.items():
        if name.endswith("_API_KEY") and not value.strip():
            continue
        if re.search(rf"^{re.escape(name)}=", content, flags=re.M):
            content = re.sub(rf"^{re.escape(name)}=.*$", f"{name}={value}", content, flags=re.M)
        else:
            content = content.rstrip() + f"\n{name}={value}\n"

    ENV.write_text(content.rstrip() + "\n", encoding="utf-8")
    print(f"Updated .env with {len(merged)} value(s) from .env.llm.local")
    print("Restart backend, then: .\\scripts\\clear-bubble-cache.ps1 && .\\scripts\\verify-llm.ps1")
    return 0


if __name__ == "__main__":
    sys.exit(main())
