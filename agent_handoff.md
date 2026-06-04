# Agent handoff — Fahéj (Animated Love App)

**Read this file first** in a new session to save tokens. Full user-facing docs: [README.md](README.md). Original plan (with review notes): `c:\Users\egera\.cursor\plans\hedgehog_love_app_65a90fb7.plan.md`.

---

## What this is

A **gift web app** for **Edina** featuring **Fahéj** (custom SVG hedgehog), Hungarian speech bubbles, weather, special dates, and a photo gallery. Built as a personal present; eventual deploy to Render (public URL + password).

**Owner constraints:** Python-first backend, React/TS frontend, local dev now, scalable later. User sets `APP_PASSWORD` in `.env` (never commit).

---

## Current status: Core MVP ✅ · Phase 1b (LLM + prefetch + content) ✅

| Done | Not done yet |
|------|----------------|
| FastAPI + SQLite + session auth | News RSS + summaries |
| `GET /api/today` (weather, mood, bubble + optional poem/book/movie) | `CloudMediaStore` implementation |
| LLM router (Groq → Gemini → OpenRouter) + static fallback | Render deploy + Postgres migration |
| `daily_content` + `llm_usage` cache tables | PWA, admin/guest split UI |
| `POST /internal/prefetch` + APScheduler 06:00 Budapest | Real MP3 hedgehog sounds (optional) |
| Content corpora + `GET /api/content/{module}` | |
| Mood engine + special dates | |
| `MediaStore` (local) + photo API | |
| React UI: Fahéj, bubbles, Ma/Képek tabs + content cards | |
| Open-Meteo weather (Szeged primary) | |
| `tzdata` for `Europe/Budapest` on Windows | |

**Local dev:** User has Node/npm installed (`frontend/node_modules` present). **Both** backend (uvicorn :8000) and frontend (`npm run dev` :5173) must run — frontend alone shows login UI but auth fails without the API.

---

## Personalization (do not change without asking)

| Item | Value |
|------|--------|
| Recipient | Edina, birthday `11-14` |
| Hedgehog | Fahéj — playful, humorous, **Hungarian** bubbles |
| Weather city | **Szeged** (`weather_primary` in profile) |
| Also | Budapest listed in `places` |
| TZ | `Europe/Budapest` |
| Wedding anniversary | `11-12` |
| Engagement anniversary | `08-19` |
| Visual | Slightly illustrated SVG, warm pastels |
| Interests (for Phase 1b) | LOTR, Harry Potter, Elden Ring, comedy films, TLC-style series |
| Photos | Both user and Edina upload (shared password); scale to hundreds |

**Mood priority:** `birthday` > special anniversaries > `weather_mood` > `idle`.

Config: [`config/profile.yaml`](config/profile.yaml) (gitignored; template: [`config/profile.example.yaml`](config/profile.example.yaml)).

---

## Repo layout

```
Animated Love App/
  agent_handoff.md          ← this file
  README.md
  .env                      ← gitignored (APP_PASSWORD, SESSION_SECRET)
  .env.example
  config/profile.yaml       ← gitignored
  config/profile.example.yaml
  data/
    app.db                  ← SQLite (created on first run)
    fallbacks/messages_hu.json
    media/                  ← uploaded images (gitignored contents)
  backend/
    app/main.py             ← loads .env before imports; FastAPI, CORS, sessions
    app/config.py           ← Settings from .env (no lru_cache); load_profile()
    app/api/routes/         ← auth, today, media, health
    app/services/           ← mood, weather, fallbacks, media_store
    app/db/                 ← SQLAlchemy models (MediaItem)
    requirements.txt        ← includes tzdata (required on Windows)
  frontend/
    src/hedgehog/           ← HedgehogCharacter, moods, Web Audio sounds
    src/components/         ← LoginPage, TodayView, PhotoGallery, SpeechBubble
    src/api/client.ts
    vite.config.ts          ← proxies /api → :8000
  scripts/start-backend.ps1
```

---

## Run locally

**Two terminals required.**

| Terminal | Command | URL |
|----------|---------|-----|
| 1 — API | `.\scripts\start-backend.ps1` from project root (or manual uvicorn below) | http://127.0.0.1:8000 |
| 2 — UI | `cd frontend` → `npm run dev` | http://localhost:5173 |

```powershell
# Terminal 1 (from project root)
cd "c:\Python Projects\Animated Love App"
.\scripts\start-backend.ps1
# equivalent: .\.venv\Scripts\Activate.ps1; cd backend; uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

```powershell
# Terminal 2
cd "c:\Python Projects\Animated Love App\frontend"
npm install   # first time only
npm run dev
```

→ Open http://localhost:5173 — password = `APP_PASSWORD` in `.env` (not the `.env.example` placeholder).

**After editing `.env`:** stop and restart uvicorn (Ctrl+C in terminal 1). A long-running process keeps the password it loaded at startup.

**Quick checks (no browser):**

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

```powershell
cd backend
..\.venv\Scripts\python -c "import httpx; c=httpx.Client(base_url='http://127.0.0.1:8000'); c.post('/api/auth/login',json={'password':'YOUR_PASSWORD'}); print(c.get('/api/today').json())"
```

**Port 8000 busy** (`WinError 10013` or “access forbidden”): another uvicorn/python is already listening. Find/stop it:

```powershell
Get-NetTCPConnection -LocalPort 8000 -State Listen | Select-Object OwningProcess
Stop-Process -Id <OwningProcess> -Force
```

Then start the backend again (only one listener on 8000).

---

## API summary

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/health` | No | Health check |
| POST | `/api/auth/login` | No | Body: `{password}` → session cookie |
| GET | `/api/auth/me` | No | `{authenticated: bool}` |
| POST | `/api/auth/logout` | Session | |
| GET | `/api/today` | Session | Mood, bubble_text, weather, flags |
| GET | `/api/media?page&limit` | Session | Paginated gallery |
| POST | `/api/media` | Session | multipart: `file`, `uploaded_by` |
| GET | `/api/media/file/{filename}` | Session | Serve image |
| GET | `/api/content/{poem\|book\|movie}` | Session | Cached daily module (if enabled in profile) |
| POST | `/internal/prefetch` | `X-Prefetch-Secret` | Warm bubble + enabled modules cache |

Production: `frontend/dist` mounted at `/` when folder exists (`main.py`).

---

## Phase 1b — done locally · next: deploy

1. ~~LLM router~~ — `backend/app/services/llm/router.py`; keys in `.env`; `LLM_DAILY_CALL_LIMIT`.
2. ~~Prefetch~~ — `POST /internal/prefetch` header `X-Prefetch-Secret`; APScheduler when `ENABLE_SCHEDULER=true`.
3. ~~Content modules~~ — `data/content/*.json`; enable `poem` / `book` / `movie` in `modules_enabled` (legacy `poems`/`books`/`movies` also work).
4. **Deploy prep** — Postgres `DATABASE_URL`, `CloudMediaStore`, HTTPS cookies on Render.
5. **News** — RSS + LLM digest (Phase 2).

---

## Known pitfalls (already hit)

1. **`ZoneInfoNotFoundError`** on Windows without `tzdata` → fixed in `requirements.txt`; reinstall if `/api/today` returns 500.
2. **Ephemeral disk on Render** — do not rely on `data/media/` or SQLite in production; use object storage + Postgres.
3. **Session cookies** — frontend uses `credentials: 'include'`; CORS origins in `main.py` are localhost:5173 only (extend for prod).
4. **Do not commit** `.env`, `config/profile.yaml`, or `data/media/*`.
5. **User rule:** only git commit when explicitly asked.
6. **`Hibás jelszó` with correct `.env` password** — usually a **stale uvicorn** still using default `changeme` (started before `APP_PASSWORD` was set, or never restarted). Fix: stop process on :8000, restart backend; verify with login API (see Run locally). Fixed in code: `main.py` calls `load_dotenv` before app imports; `get_settings()` no longer uses `@lru_cache`.
7. **Frontend-only** — `npm run dev` proxies `/api` to :8000; without uvicorn, login always fails.
8. **Duplicate backend on :8000** — second `start-backend.ps1` fails; use existing listener or stop the old PID first.

---

## Design decisions (locked)

- **No stock Lottie** — custom layered SVG + CSS/WAAPI moods.
- **AI cost model** — cache daily content; multi-provider free tier with fallbacks (see plan).
- **Apple/iCloud location** — deferred; Shortcuts webhook or manual city only.
- **First build slice was Core MVP** — AI optional until Phase 1b; user has time (no hard deadline).

---

## Files to touch for common tasks

| Task | Files |
|------|--------|
| Change Hungarian copy | `data/fallbacks/messages_hu.json`, `backend/app/services/fallbacks.py` |
| Dates / name / city | `config/profile.yaml` |
| Hedgehog look/animation | `frontend/src/hedgehog/HedgehogCharacter.tsx`, `hedgehog.css` |
| New activity module | Add `ContentModule` service + route; extend `modules_enabled` in profile |
| Auth / CORS | `backend/app/main.py`, `backend/app/api/routes/auth.py` |
| Photo storage | `backend/app/services/media_store.py` |

---

## Token-saving tips for the next agent

1. Read **this file** + grep target symbol before broad searches.
2. Skip reading `.venv/`, `node_modules/`, `data/media/` binaries.
3. Do not re-read the full plan unless implementing Phase 1b+ or deploy.
4. Test backend with httpx/`Invoke-RestMethod` before spinning up frontend.
5. Ask user before changing Edina’s profile facts or visual identity.
6. If auth fails: `GET /health`, then `POST /api/auth/login` with password from `.env` — don’t assume frontend/proxy bug until API accepts login.

---

*Last updated: local dev / auth troubleshooting session (June 2026).*
