"""
JWT-based auth + SQLite user store (via aiosqlite).
"""

from __future__ import annotations
import hashlib
import hmac
import json
import os
import time
import base64
import aiosqlite
from typing import Optional

from app.config import settings

DB_PATH = os.environ.get("DB_PATH", "fx_signal.db")
_SECRET = os.environ.get("JWT_SECRET", "change-me-in-production-please")


# ── DB init ───────────────────────────────────────────────────────────────────

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                display_name TEXT DEFAULT '',
                alert_pairs TEXT DEFAULT '[]',
                alert_min_score REAL DEFAULT 80.0,
                created_at INTEGER DEFAULT (strftime('%s','now'))
            )
        """)
        await db.commit()


# ── Password ──────────────────────────────────────────────────────────────────

def _hash_password(pw: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, 100_000)
    return base64.b64encode(salt + dk).decode()


def _verify_password(pw: str, stored: str) -> bool:
    raw = base64.b64decode(stored.encode())
    salt, dk = raw[:16], raw[16:]
    check = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, 100_000)
    return hmac.compare_digest(dk, check)


# ── JWT (HS256, stdlib only) ──────────────────────────────────────────────────

def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _create_token(payload: dict, expires_in: int = 86400 * 30) -> str:
    header = _b64url(b'{"alg":"HS256","typ":"JWT"}')
    payload["exp"] = int(time.time()) + expires_in
    body = _b64url(json.dumps(payload).encode())
    sig_input = f"{header}.{body}".encode()
    sig = _b64url(hmac.new(_SECRET.encode(), sig_input, hashlib.sha256).digest())
    return f"{header}.{body}.{sig}"


def _verify_token(token: str) -> Optional[dict]:
    try:
        header, body, sig = token.split(".")
        sig_input = f"{header}.{body}".encode()
        expected = _b64url(hmac.new(_SECRET.encode(), sig_input, hashlib.sha256).digest())
        if not hmac.compare_digest(sig, expected):
            return None
        payload = json.loads(base64.urlsafe_b64decode(body + "=="))
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None


# ── CRUD ──────────────────────────────────────────────────────────────────────

async def create_user(email: str, password: str, display_name: str = "") -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute(
                "INSERT INTO users (email, password_hash, display_name) VALUES (?,?,?)",
                (email.lower(), _hash_password(password), display_name),
            )
            await db.commit()
            return await get_user_by_email(email)
        except aiosqlite.IntegrityError:
            return None


async def get_user_by_email(email: str) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE email=?", (email.lower(),))
        row = await cur.fetchone()
        return dict(row) if row else None


async def get_user_by_id(user_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE id=?", (user_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def update_alert_settings(user_id: int, pairs: list[str], min_score: float):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET alert_pairs=?, alert_min_score=? WHERE id=?",
            (json.dumps(pairs), min_score, user_id),
        )
        await db.commit()


async def authenticate(email: str, password: str) -> Optional[str]:
    """Returns JWT token or None."""
    user = await get_user_by_email(email)
    if not user:
        return None
    if not _verify_password(password, user["password_hash"]):
        return None
    return _create_token({"sub": user["id"], "email": user["email"]})


def decode_token(token: str) -> Optional[dict]:
    return _verify_token(token)
