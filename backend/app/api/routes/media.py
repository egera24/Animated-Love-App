from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_auth
from app.api.schemas import MediaItemOut, MediaListResponse
from app.config import get_settings
from app.db.models import MediaItem
from app.db.session import get_db
from app.services.media_store import get_media_store

router = APIRouter(prefix="/api/media", tags=["media"])


@router.get("", response_model=MediaListResponse)
def list_media(
    request: Request,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    require_auth(request)
    offset = (page - 1) * limit
    total = db.scalar(select(func.count()).select_from(MediaItem)) or 0
    rows = (
        db.execute(
            select(MediaItem)
            .order_by(MediaItem.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        .scalars()
        .all()
    )
    items = [
        MediaItemOut(
            id=r.id,
            filename=r.filename,
            original_name=r.original_name,
            url=f"/api/media/file/{r.filename}",
            uploaded_by=r.uploaded_by,
            created_at=r.created_at.isoformat(),
        )
        for r in rows
    ]
    return MediaListResponse(items=items, total=total, page=page, limit=limit)


@router.post("", response_model=MediaItemOut, status_code=status.HTTP_201_CREATED)
async def upload_media(
    request: Request,
    file: UploadFile = File(...),
    uploaded_by: str = Form("család"),
    db: Session = Depends(get_db),
):
    require_auth(request)
    settings = get_settings()
    store = get_media_store(settings.media_store)
    data = await file.read()
    try:
        key = store.save(file.filename or "photo.jpg", data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    uploader = (uploaded_by or "család").strip()[:64]

    item = MediaItem(
        filename=key,
        original_name=file.filename or key,
        content_type=file.content_type or "image/jpeg",
        uploaded_by=uploader,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    return MediaItemOut(
        id=item.id,
        filename=item.filename,
        original_name=item.original_name,
        url=f"/api/media/file/{item.filename}",
        uploaded_by=item.uploaded_by,
        created_at=item.created_at.isoformat(),
    )


@router.get("/file/{filename}")
def serve_media(
    filename: str,
    request: Request,
    db: Session = Depends(get_db),
):
    require_auth(request)
    row = db.execute(
        select(MediaItem).where(MediaItem.filename == filename)
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Nem található.")
    settings = get_settings()
    store = get_media_store(settings.media_store)
    path = store.resolve_path(filename)
    if not path.exists():
        raise HTTPException(status_code=404, detail="A fájl hiányzik.")
    return FileResponse(path, media_type=row.content_type)
