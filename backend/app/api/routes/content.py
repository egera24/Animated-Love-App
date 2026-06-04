from fastapi import APIRouter, HTTPException, Request

from app.api.deps import require_auth
from app.api.schemas import ContentModuleResponse
from app.config import load_profile
from app.db.session import SessionLocal
from app.services.content_cache import get_cached
from app.services.content_modules import generate_module_content
from app.services.mood import _today_in_tz

router = APIRouter(prefix="/api/content", tags=["content"])

VALID_MODULES = frozenset({"poem", "book", "movie"})


@router.get("/{module}", response_model=ContentModuleResponse)
async def get_content(module: str, request: Request):
    require_auth(request)
    if module not in VALID_MODULES:
        raise HTTPException(status_code=404, detail="Ismeretlen modul.")

    profile = load_profile()
    from app.services.content_modules import _module_enabled

    if not _module_enabled(profile.get("modules_enabled", {}), module):
        raise HTTPException(status_code=404, detail="A modul nincs engedélyezve.")

    content_date = _today_in_tz(profile).isoformat()
    db = SessionLocal()
    try:
        cached = get_cached(db, content_date, module)
        if not cached:
            cached = await generate_module_content(db, module, profile)
        if not cached:
            raise HTTPException(status_code=404, detail="Nincs tartalom ehhez a modulhoz.")
        return ContentModuleResponse(
            module=module,
            text=cached.get("text", ""),
            title=cached.get("title"),
            source=cached.get("source", "corpus"),
        )
    finally:
        db.close()
