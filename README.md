# Fahéj — Interactive hedgehog gift app for Edina

A local-first web app with **Fahéj** (a custom animated SVG hedgehog), Hungarian speech bubbles, weather for Szeged, birthday and anniversary messages, and a photo gallery.

## Quick start (Windows)

### 1. Backend

```powershell
cd "c:\Python Projects\Animated Love App"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

Copy environment file and set your password:

```powershell
copy .env.example .env
# Edit .env: APP_PASSWORD and SESSION_SECRET
```

Copy profile if needed (a `config/profile.yaml` is already included for Edina):

```powershell
copy config\profile.example.yaml config\profile.yaml
```

Run API:

```powershell
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 2. Frontend

Install [Node.js LTS](https://nodejs.org/) if `npm` is not available, then:

```powershell
cd "c:\Python Projects\Animated Love App\frontend"
npm install
npm run dev
```

Or use the helper script from the project root (after Node is installed):

```powershell
.\scripts\start-backend.ps1   # terminal 1
# terminal 2: cd frontend && npm run dev
```

Open [http://localhost:5173](http://localhost:5173) and log in with `APP_PASSWORD`.

## Features (Core MVP)

- Custom illustrated **Fahéj** hedgehog with mood animations and subtle movement sounds
- **Hungarian** bubble text (static fallbacks; optional AI via Groq/Gemini/OpenRouter in `.env`)
- **Weather** via Open-Meteo (Szeged by default)
- **Birthday** (14 Nov) and anniversaries (12 Nov wedding, 19 Aug engagement)
- **Photos**: upload and carousel (you and Edina, shared password)
- **Session auth** for future public deploy

## Configuration

| File | Purpose |
|------|---------|
| `.env` | `APP_PASSWORD`, `SESSION_SECRET`, optional LLM keys |
| `config/profile.yaml` | Edina's name, dates, cities, interests |

### Enable AI bubbles (Groq + Gemini + OpenRouter)

1. Create keys (see [docs/LLM_SETUP.md](docs/LLM_SETUP.md)).
2. Run `.\scripts\configure-llm.ps1` or paste keys into `.env`.
3. Restart backend, then `.\scripts\clear-bubble-cache.ps1`, then `.\scripts\verify-llm.ps1`.

Without keys, bubbles use static Hungarian text in `data/fallbacks/messages_hu.json`.

## Production build

```powershell
cd frontend
npm run build
cd ..\backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The API serves `frontend/dist` when present.

## Deploying to Render (later)

1. Use **Postgres** (`DATABASE_URL`) — do not rely on SQLite on ephemeral disk.
2. Use **object storage** for photos (`MEDIA_STORE=cloud` when implemented).
3. Set env vars: `APP_PASSWORD`, `SESSION_SECRET`, `SESSION` HTTPS cookies.
4. Add a **cron job** calling `POST /internal/prefetch` with header `X-Prefetch-Secret` (set `PREFETCH_SECRET` in `.env`).

## Phase 1b

- Multi-provider LLM for bubbles (Groq → Gemini → OpenRouter) — see [docs/LLM_SETUP.md](docs/LLM_SETUP.md)
- Daily poem / book / movie cards from `data/content/` (enable in `profile.yaml`)
- News RSS summaries (planned)

## Sounds

Movement sounds use the Web Audio API (no files required). To use real clips, add MP3s under `frontend/public/sounds/` and extend `hedgehogSounds.ts`.
