"""
Friday — Auth Hub
Session JWT avec expiration pour protéger le hub
"""

from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Response, Cookie
from pydantic import BaseModel
from jose import jwt, JWTError
from config.settings import settings

router = APIRouter(prefix="/auth", tags=["auth"])

SECRET_KEY = settings.FRIDAY_SECRET
ALGORITHM = "HS256"


class LoginRequest(BaseModel):
    username: str
    password: str


def create_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.HUB_SESSION_EXPIRE_HOURS)
    return jwt.encode(
        {"sub": username, "exp": expire},
        SECRET_KEY, algorithm=ALGORITHM
    )


def verify_hub_token(token: str) -> bool:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub") == settings.HUB_USERNAME
    except JWTError:
        return False


@router.post("/login")
async def login(req: LoginRequest, response: Response):
    if req.username != settings.HUB_USERNAME or req.password != settings.HUB_PASSWORD:
        raise HTTPException(status_code=401, detail="Identifiants incorrects")
    token = create_token(req.username)
    response.set_cookie(
        key="friday_session",
        value=token,
        httponly=True,
        max_age=settings.HUB_SESSION_EXPIRE_HOURS * 3600,
        samesite="lax"
    )
    return {"status": "ok", "token": token}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("friday_session")
    return {"status": "ok"}


@router.get("/verify")
async def verify(friday_session: str = Cookie(None)):
    if not friday_session or not verify_hub_token(friday_session):
        raise HTTPException(status_code=401, detail="Session expirée")
    return {"status": "ok"}
