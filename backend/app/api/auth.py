import json
from fastapi import APIRouter, HTTPException, Header
from typing import Optional

from app.models.user import UserCreate, UserLogin, UserOut, TokenResponse, AlertSettings
from app.services.auth import (
    create_user, authenticate, get_user_by_id, decode_token, update_alert_settings
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _current_user_id(authorization: Optional[str]) -> int:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "認証が必要です")
    token = authorization.removeprefix("Bearer ")
    payload = decode_token(token)
    if not payload:
        raise HTTPException(401, "トークンが無効または期限切れです")
    return int(payload["sub"])


def _user_to_out(row: dict) -> UserOut:
    pairs = json.loads(row.get("alert_pairs") or "[]")
    return UserOut(
        id=row["id"],
        email=row["email"],
        display_name=row.get("display_name") or "",
        alert_pairs=pairs,
        alert_min_score=row.get("alert_min_score", 80.0),
    )


@router.post("/register", response_model=TokenResponse)
async def register(body: UserCreate):
    user_row = await create_user(body.email, body.password, body.display_name)
    if not user_row:
        raise HTTPException(409, "このメールアドレスは既に登録されています")
    token = await authenticate(body.email, body.password)
    return TokenResponse(access_token=token, user=_user_to_out(user_row))


@router.post("/login", response_model=TokenResponse)
async def login(body: UserLogin):
    token = await authenticate(body.email, body.password)
    if not token:
        raise HTTPException(401, "メールアドレスまたはパスワードが違います")
    from app.services.auth import get_user_by_email
    user_row = await get_user_by_email(body.email)
    return TokenResponse(access_token=token, user=_user_to_out(user_row))


@router.get("/me", response_model=UserOut)
async def me(authorization: Optional[str] = Header(None)):
    uid = _current_user_id(authorization)
    row = await get_user_by_id(uid)
    if not row:
        raise HTTPException(404, "ユーザーが見つかりません")
    return _user_to_out(row)


@router.put("/alerts", response_model=UserOut)
async def update_alerts(body: AlertSettings, authorization: Optional[str] = Header(None)):
    uid = _current_user_id(authorization)
    await update_alert_settings(uid, body.pairs, body.min_score)
    row = await get_user_by_id(uid)
    return _user_to_out(row)
