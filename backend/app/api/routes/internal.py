from fastapi import APIRouter, Header, HTTPException
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.session import SessionLocal
from app.services.prefetch import run_prefetch

router = APIRouter(prefix="/internal", tags=["internal"])


def _verify_prefetch_secret(x_prefetch_secret: str | None) -> None:
    settings = get_settings()
    expected = settings.prefetch_secret
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="PREFETCH_SECRET nincs beállítva a .env fájlban.",
        )
    if not x_prefetch_secret or x_prefetch_secret != expected:
        raise HTTPException(status_code=401, detail="Érvénytelen prefetch kulcs.")


@router.post("/prefetch")
async def prefetch_daily(x_prefetch_secret: str | None = Header(default=None)):
    _verify_prefetch_secret(x_prefetch_secret)
    db = SessionLocal()
    try:
        result = await run_prefetch(db)
        return result
    finally:
        db.close()
