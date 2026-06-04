from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import DailyContent


def get_cached(db: Session, content_date: str, module: str) -> dict[str, Any] | None:
    row = db.scalar(
        select(DailyContent).where(
            DailyContent.content_date == content_date,
            DailyContent.module == module,
        )
    )
    if not row:
        return None
    return json.loads(row.payload_json)


def set_cached(db: Session, content_date: str, module: str, payload: dict[str, Any]) -> None:
    row = db.scalar(
        select(DailyContent).where(
            DailyContent.content_date == content_date,
            DailyContent.module == module,
        )
    )
    payload_json = json.dumps(payload, ensure_ascii=False)
    if row:
        row.payload_json = payload_json
    else:
        db.add(
            DailyContent(
                content_date=content_date,
                module=module,
                payload_json=payload_json,
            )
        )
    db.commit()
