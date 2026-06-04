from fastapi import APIRouter, HTTPException, Request, status

from app.api.deps import verify_password
from app.api.schemas import LoginRequest, LoginResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, request: Request):
    if not verify_password(body.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Hibás jelszó.",
        )
    request.session["authenticated"] = True
    return LoginResponse(ok=True, message="Sikeres bejelentkezés!")


@router.post("/logout", response_model=LoginResponse)
async def logout(request: Request):
    request.session.clear()
    return LoginResponse(ok=True, message="Kijelentkezve.")


@router.get("/me")
async def me(request: Request):
    return {"authenticated": bool(request.session.get("authenticated"))}
