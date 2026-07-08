from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

# Load .env before any app imports that read settings (e.g. db.session).
_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_ROOT / ".env")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.api.routes import auth, chat, content, health, internal, media, today
from app.config import ROOT_DIR, get_settings
from app.db.session import init_db
from app.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    Path(ROOT_DIR / "data" / "media").mkdir(parents=True, exist_ok=True)
    start_scheduler()
    yield
    stop_scheduler()


settings = get_settings()

app = FastAPI(
    title="Fahéj — Edina ajándéka",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
    same_site="lax",
    https_only=False,
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(today.router)
app.include_router(chat.router)
app.include_router(content.router)
app.include_router(media.router)
app.include_router(internal.router)

# Production: mount frontend build
_dist = ROOT_DIR / "frontend" / "dist"
if _dist.exists():
    from fastapi.staticfiles import StaticFiles

    app.mount("/", StaticFiles(directory=_dist, html=True), name="static")
