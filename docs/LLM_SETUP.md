# LLM setup (Groq + Gemini + OpenRouter)

Fahéj bubble and chat text use your backend only — **API keys** live in `.env`, **model lists** in `config/llm_models.yaml`. Neither is committed to git.

## 1. Create API keys

| Provider | Sign up / keys | `.env` variable |
|----------|----------------|-----------------|
| Groq | https://console.groq.com → API Keys | `GROQ_API_KEY` |
| Gemini | https://aistudio.google.com/apikey | `GEMINI_API_KEY` |
| OpenRouter | https://openrouter.ai/keys | `OPENROUTER_API_KEY` |

You need **at least one** key. All three give fallbacks when one hits quota or errors.

## 2. Configure model fallback order

Models are listed in YAML (not `.env`):

```powershell
copy config\llm_models.example.yaml config\llm_models.yaml
# Edit llm_models.yaml — reorder providers and models as needed
```

Fallback order: **providers top-to-bottom**, then **models top-to-bottom within each provider**. Providers without an API key in `.env` are skipped.

Example: Groq model 1 fails (429) → Groq model 2 → Groq model 3 → Gemini model 1 → …

If `llm_models.yaml` is missing, the app uses `config/llm_models.example.yaml`. Legacy single-model `.env` vars (`GROQ_MODEL`, etc.) apply only when no YAML catalog is available.

## 3. Add keys to `.env`

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

## 4. Restart backend

```powershell
.\scripts\start-backend.ps1
```

Stop the old uvicorn first (Ctrl+C) so new env vars load.

## 5. Clear bubble cache (if you used the app before adding keys)

```powershell
.\scripts\clear-bubble-cache.ps1
```

## 6. Verify

```powershell
.\scripts\verify-llm.ps1
```

Expect a catalog summary, `cache source: llm`, and a row in `llm_usage` like `bubble:groq/llama-3.3-70b-versatile`.

## Optional: manual prefetch

```powershell
$secret = "your-PREFETCH_SECRET-from-env"
Invoke-RestMethod -Method POST http://127.0.0.1:8000/internal/prefetch -Headers @{ "X-Prefetch-Secret" = $secret }
```

## Troubleshooting

- Still **static** bubbles: cache not cleared, backend not restarted, or empty key in `.env`.
- **503** on prefetch: set `PREFETCH_SECRET` in `.env` and restart.
- **429 / 5xx**: next model, then next provider in chain runs automatically; check uvicorn logs for `LLM fallback:` / `LLM ok:` lines.

Poem / book / movie cards are **not** LLM-generated — enable them in `config/profile.yaml` for corpus-based tips only.
