from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class DailyContent(Base):
    __tablename__ = "daily_content"
    __table_args__ = (UniqueConstraint("content_date", "module", name="uq_daily_content_date_module"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content_date: Mapped[str] = mapped_column(String(10), index=True)
    module: Mapped[str] = mapped_column(String(32), index=True)
    payload_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class LlmUsage(Base):
    __tablename__ = "llm_usage"
    __table_args__ = (UniqueConstraint("usage_date", "provider", name="uq_llm_usage_date_provider"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    usage_date: Mapped[str] = mapped_column(String(10), index=True)
    provider: Mapped[str] = mapped_column(String(32))
    calls: Mapped[int] = mapped_column(Integer, default=0)
    tokens: Mapped[int] = mapped_column(Integer, default=0)


class MediaItem(Base):
    __tablename__ = "media_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(512), unique=True, index=True)
    original_name: Mapped[str] = mapped_column(String(512))
    content_type: Mapped[str] = mapped_column(String(128), default="image/jpeg")
    uploaded_by: Mapped[str] = mapped_column(String(64), default="guest")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
