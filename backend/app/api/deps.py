from fastapi import HTTPException, Request, status

from app.config import get_settings


def require_auth(request: Request) -> None:
    if not request.session.get("authenticated"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bejelentkezés szükséges.",
        )


def verify_password(password: str) -> bool:
    settings = get_settings()
    return password == settings.app_password
