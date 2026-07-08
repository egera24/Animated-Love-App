from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import delete, select

from app.api.deps import require_auth
from app.api.schemas import (
    ChatHistoryItem,
    ChatHistoryResponse,
    ChatReplyResponse,
    ChatRequest,
)
from app.config import load_profile
from app.db.models import ChatMessage
from app.db.session import SessionLocal
from app.services.chat_service import generate_reply
from app.services.memory_store import extract_and_store, get_memory_context

router = APIRouter(prefix="/api/chat", tags=["chat"])

_VALID_CHARACTERS = {"hedgehog", "self"}


@router.post("", response_model=ChatReplyResponse)
async def post_chat(request: Request, body: ChatRequest):
    require_auth(request)
    message = (body.message or "").strip()
    if not message:
        raise HTTPException(status_code=422, detail="Üres üzenet.")
    character_id = body.character_id if body.character_id in _VALID_CHARACTERS else "hedgehog"

    profile = load_profile()
    db = SessionLocal()
    try:
        memory_context = get_memory_context(db, profile, query=message)
        result = await generate_reply(
            db,
            profile=profile,
            character_id=character_id,
            user_text=message,
            memory_context=memory_context,
        )
        # Learn durable facts from this turn (best-effort, non-blocking on failure).
        await extract_and_store(db, profile, user_text=message)
    finally:
        db.close()

    return ChatReplyResponse(
        reply=result.reply,
        mood=result.mood,
        expression=result.expression,
        source=result.source,
    )


@router.get("/history", response_model=ChatHistoryResponse)
def get_history(request: Request, character_id: str = "hedgehog", limit: int = 50):
    require_auth(request)
    cid = character_id if character_id in _VALID_CHARACTERS else "hedgehog"
    limit = max(1, min(limit, 200))

    db = SessionLocal()
    try:
        rows = db.scalars(
            select(ChatMessage)
            .where(ChatMessage.character_id == cid)
            .order_by(ChatMessage.id.desc())
            .limit(limit)
        ).all()
    finally:
        db.close()

    items = [
        ChatHistoryItem(
            role=r.role,
            content=r.content,
            expression=r.expression,
            created_at=r.created_at.isoformat() if r.created_at else "",
        )
        for r in reversed(rows)
    ]
    return ChatHistoryResponse(items=items)


@router.delete("/history")
def clear_history(request: Request, character_id: str = "hedgehog"):
    require_auth(request)
    cid = character_id if character_id in _VALID_CHARACTERS else "hedgehog"
    db = SessionLocal()
    try:
        db.execute(delete(ChatMessage).where(ChatMessage.character_id == cid))
        db.commit()
    finally:
        db.close()
    return {"ok": True}
