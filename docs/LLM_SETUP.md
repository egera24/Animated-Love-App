# LLM setup (Groq + Gemini + OpenRouter)

Fahéj bubble text uses your backend only — keys live in `.env`, never in git.

## 1. Create API keys

| Provider | Sign up / keys | `.env` variable |
|----------|----------------|-----------------|
| Groq | https://console.groq.com → API Keys | `GROQ_API_KEY` |
| Gemini | https://aistudio.google.com/apikey | `GEMINI_API_KEY` |
| OpenRouter | https://openrouter.ai/keys | `OPENROUTER_API_KEY` |

You need **at least one** key. All three give fallbacks when one hits quota or errors.

## 2. Add keys to `.env`

**Option A — local secrets file (easy to paste three keys):**

```powershell
copy .env.llm.local.example .env.llm.local
# Edit .env.llm.local — paste keys (file is gitignored)
.\.venv\Scripts\python scripts\apply_llm_keys.py
```

**Option B — interactive:**

```powershell
.\scripts\configure-llm.ps1
```

**Option C — manual:** edit `.env` directly (see `.env.example`).

## 3. Restart backend

```powershell
.\scripts\start-backend.ps1
```

Stop the old uvicorn first (Ctrl+C) so new env vars load.

## 4. Clear bubble cache (if you used the app before adding keys)

```powershell
.\scripts\clear-bubble-cache.ps1
```

## 5. Verify

```powershell
.\scripts\verify-llm.ps1
```

Expect `cache source: llm` and a row in `llm_usage` (usually `groq` first).

## Optional: manual prefetch

```powershell
$secret = "your-PREFETCH_SECRET-from-env"
Invoke-RestMethod -Method POST http://127.0.0.1:8000/internal/prefetch -Headers @{ "X-Prefetch-Secret" = $secret }
```

## Troubleshooting

- Still **static** bubbles: cache not cleared, backend not restarted, or empty key in `.env`.
- **503** on prefetch: set `PREFETCH_SECRET` in `.env` and restart.
- **429 / 5xx**: next provider in chain runs automatically; check uvicorn logs.

Poem / book / movie cards are **not** LLM-generated — enable them in `config/profile.yaml` for corpus-based tips only.
