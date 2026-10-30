"""Yandex ID authorization with one-use state, PKCE and explicit account linking."""
import base64
import hashlib
import os
import secrets
import time
from urllib.parse import urlencode, urlsplit

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.database import get_connection
from app.repositories.reservation_repository import ReservationRepository
from app.repositories.user_repository import UserRepository
from app.utils.jwt import create_access_token, get_optional_user
from app.utils.security import hash_password

router = APIRouter(prefix="/auth/yandex", tags=["auth"])


def settings():
    client_id = os.getenv("YANDEX_CLIENT_ID", "").strip()
    secret = os.getenv("YANDEX_CLIENT_SECRET", "").strip()
    redirect = os.getenv("YANDEX_REDIRECT_URI", "").strip()
    parsed = urlsplit(redirect)
    valid_url = (parsed.scheme == "https" or (parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1"})) and parsed.netloc and not parsed.username and not parsed.password and not parsed.fragment and not parsed.query
    if not client_id or not secret or not valid_url:
        raise HTTPException(503, "Yandex sign-in is not configured")
    return client_id, secret, redirect


def limit(request: Request):
    ip = request.client.host if request.client else "unknown"
    retry = ReservationRepository().check_guest_rate_limit(f"yandex:{ip}")
    if retry:
        raise HTTPException(429, "Too many attempts", headers={"Retry-After": str(retry)})


class StartRequest(BaseModel):
    link: bool = False


class ExchangeRequest(BaseModel):
    state: str = Field(min_length=30, max_length=128)
    code: str = Field(min_length=1, max_length=2048)
    proof: str = Field(min_length=30, max_length=128)


@router.get("/availability")
def availability():
    try:
        settings()
    except HTTPException:
        return {"enabled": False}
    return {"enabled": True}


@router.post("/start")
def start(data: StartRequest, request: Request, user=Depends(get_optional_user)):
    client_id, _, redirect = settings()
    limit(request)
    if data.link and user is None:
        raise HTTPException(401, "Sign in before linking")
    state, proof, verifier = secrets.token_urlsafe(32), secrets.token_urlsafe(32), secrets.token_urlsafe(48)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    now = int(time.time())
    with get_connection() as conn:
        conn.execute("DELETE FROM yandex_auth_states WHERE expires_at <= ?", (now,))
        conn.execute("INSERT INTO yandex_auth_states (state_hash, browser_hash, verifier, user_id, expires_at) VALUES (?, ?, ?, ?, ?)",
                     (hashlib.sha256(state.encode()).hexdigest(), hashlib.sha256(proof.encode()).hexdigest(), verifier, user.id if data.link else None, now + 600))
    params = {"response_type": "code", "client_id": client_id, "redirect_uri": redirect,
              "state": state, "code_challenge": challenge, "code_challenge_method": "S256"}
    return {"state": state, "proof": proof, "url": "https://oauth.yandex.ru/authorize?" + urlencode(params)}


@router.post("/exchange")
def exchange(data: ExchangeRequest, request: Request, user=Depends(get_optional_user)):
    client_id, secret, redirect = settings()
    limit(request)
    state_hash = hashlib.sha256(data.state.encode()).hexdigest()
    with get_connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute("SELECT * FROM yandex_auth_states WHERE state_hash = ? AND expires_at > ?", (state_hash, int(time.time()))).fetchone()
        if row is None or not secrets.compare_digest(row["browser_hash"], hashlib.sha256(data.proof.encode()).hexdigest()):
            raise HTTPException(400, "Authorization expired or already used")
        if row["user_id"] is not None and (user is None or user.id != row["user_id"]):
            raise HTTPException(403, "Sign in to the original account to link")
        conn.execute("DELETE FROM yandex_auth_states WHERE state_hash = ?", (state_hash,))
    try:
        with httpx.Client(timeout=8, follow_redirects=False) as client:
            response = client.post("https://oauth.yandex.ru/token", data={"grant_type": "authorization_code", "code": data.code, "client_id": client_id, "client_secret": secret, "redirect_uri": redirect, "code_verifier": row["verifier"]})
            response.raise_for_status()
            token = response.json()["access_token"]
            info = client.get("https://login.yandex.ru/info", headers={"Authorization": f"OAuth {token}"}, params={"format": "json"})
            info.raise_for_status()
            profile = info.json()
        yandex_id = profile["id"]
        if not isinstance(yandex_id, str) or not yandex_id.isascii() or not yandex_id.isdigit() or len(yandex_id) > 32 or profile.get("client_id") != client_id:
            raise ValueError("Invalid Yandex identity")
    except (httpx.HTTPError, KeyError, TypeError, ValueError):
        raise HTTPException(502, "Could not verify Yandex account") from None

    with get_connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        existing = conn.execute("SELECT user_id FROM yandex_accounts WHERE yandex_id = ?", (yandex_id,)).fetchone()
        if row["user_id"] is not None:
            linked = conn.execute("SELECT yandex_id FROM yandex_accounts WHERE user_id = ?", (row["user_id"],)).fetchone()
            if (existing and existing["user_id"] != row["user_id"]) or (linked and linked["yandex_id"] != yandex_id):
                raise HTTPException(409, "Yandex account is already linked")
            if not existing:
                conn.execute("INSERT INTO yandex_accounts VALUES (?, ?)", (yandex_id, row["user_id"]))
            user_id = row["user_id"]
        elif existing:
            user_id = existing["user_id"]
        else:
            # Never associate an existing account merely because its email matches.
            name = str(profile.get("display_name") or profile.get("real_name") or "Пользователь Яндекса").strip()[:100] or "Пользователь Яндекса"
            login = "yandex_" + secrets.token_hex(12)
            password_hash = hash_password(secrets.token_urlsafe(32))
            user_id = conn.execute("INSERT INTO users (name, login, password_hash) VALUES (?, ?, ?)", (name, login, password_hash)).lastrowid
            conn.execute("INSERT INTO yandex_accounts VALUES (?, ?)", (yandex_id, user_id))
    account = UserRepository().get_user_by_id(user_id)
    token = create_access_token({"sub": account.login, "user_id": account.id, "auth_version": account.auth_version})
    return {"access_token": token, "token_type": "bearer", "linked": row["user_id"] is not None,
            "user": {"id": account.id, "name": account.name, "login": account.login}}
