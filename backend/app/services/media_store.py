from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from pathlib import Path

from app.config import DATA_DIR

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_UPLOAD_BYTES = 15 * 1024 * 1024


class MediaStore(ABC):
    @abstractmethod
    def save(self, filename: str, data: bytes) -> str:
        """Persist file; return storage key/path."""

    @abstractmethod
    def resolve_path(self, storage_key: str) -> Path:
        """Return filesystem path for serving."""

    @abstractmethod
    def delete(self, storage_key: str) -> None:
        pass


class LocalMediaStore(MediaStore):
    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or (DATA_DIR / "media")
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, filename: str, data: bytes) -> str:
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {ext}")
        if len(data) > MAX_UPLOAD_BYTES:
            raise ValueError("File too large (max 15 MB)")
        key = f"{uuid.uuid4().hex}{ext}"
        path = self.base_dir / key
        path.write_bytes(data)
        return key

    def resolve_path(self, storage_key: str) -> Path:
        path = (self.base_dir / storage_key).resolve()
        if not str(path).startswith(str(self.base_dir.resolve())):
            raise ValueError("Invalid storage key")
        return path

    def delete(self, storage_key: str) -> None:
        path = self.resolve_path(storage_key)
        if path.exists():
            path.unlink()


class CloudMediaStore(MediaStore):
    """Stub for future S3/Cloudinary integration."""

    def save(self, filename: str, data: bytes) -> str:
        raise NotImplementedError("Cloud media store not configured. Use MEDIA_STORE=local.")

    def resolve_path(self, storage_key: str) -> Path:
        raise NotImplementedError("Cloud media store not configured.")

    def delete(self, storage_key: str) -> None:
        raise NotImplementedError("Cloud media store not configured.")


def get_media_store(kind: str = "local") -> MediaStore:
    if kind == "cloud":
        return CloudMediaStore()
    return LocalMediaStore()
