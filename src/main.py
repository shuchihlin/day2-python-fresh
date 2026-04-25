from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.responses import JSONResponse
from typing import Optional
from datetime import datetime, timedelta, timezone
import os
import jwt

from src.database import Database
from src.models import (
    RegisterRequest,
    LoginRequest,
    LoginResponse,
    PasswordResetRequest,
    ConfirmResetRequest,
    UserProfile,
    UserWithPosts,
)
from src.auth import (
    _hash_password,
    verify,
    _cleanup_old_attempts,
    _reset_attempts,
)
from src.validators import is_strong_password
from src.legacy_user_data import fetch_user_by_id, fetch_user_posts, fetch_user_with_posts

app = FastAPI(title="Authentication API", version="1.0.0")
db = Database("auth.db")

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-key")


@app.on_event("startup")
async def startup():
    await db.connect()


@app.on_event("shutdown")
async def shutdown():
    await db.disconnect()


async def get_current_user(authorization: Optional[str] = Header(None)):
    """Dependency to extract and verify JWT token."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0] != "Bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = parts[1]
    result = verify(token)
    if not result["valid"]:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return result["email"]


@app.post("/register", response_model=UserProfile)
async def register(req: RegisterRequest):
    """Register a new user."""
    if not is_strong_password(req.password):
        raise HTTPException(status_code=400, detail="Password does not meet strength requirements")

    user = await db.get_user_by_email(req.email)
    if user:
        raise HTTPException(status_code=409, detail="Email already registered")

    password_hash = _hash_password(req.password)
    user_id = await db.create_user(req.email, req.name, password_hash)

    return UserProfile(id=user_id, email=req.email, name=req.name)


@app.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    """Login and receive JWT token."""
    user = await db.get_user_by_email(req.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    import hmac

    if not hmac.compare_digest(user["password"], _hash_password(req.password)):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    payload = {
        "email": req.email,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return LoginResponse(token=token, email=req.email)


@app.post("/reset-password")
async def request_password_reset(req: PasswordResetRequest):
    """Request a password reset token."""
    user = await db.get_user_by_email(req.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    _cleanup_old_attempts(req.email)

    if req.email in _reset_attempts and len(_reset_attempts[req.email]) >= 5:
        raise HTTPException(status_code=429, detail="Too many reset requests")

    now = datetime.now(timezone.utc)
    if req.email not in _reset_attempts:
        _reset_attempts[req.email] = []
    _reset_attempts[req.email].append(now)

    payload = {
        "email": req.email,
        "type": "password_reset",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return {"token": token, "email": req.email, "expires_in": 1800}


@app.post("/confirm-reset")
async def confirm_password_reset(req: ConfirmResetRequest):
    """Verify reset token and update password."""
    if not is_strong_password(req.new_password):
        raise HTTPException(status_code=400, detail="Password does not meet strength requirements")

    try:
        payload = jwt.decode(req.token, JWT_SECRET, algorithms=["HS256"])
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    if payload.get("type") != "password_reset":
        raise HTTPException(status_code=400, detail="Invalid token type")

    email = payload.get("email")
    user = await db.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    password_hash = _hash_password(req.new_password)
    await db.update_user_password(email, password_hash)

    return {"success": True, "message": "Password reset complete"}


@app.get("/profile", response_model=UserProfile)
async def get_profile(email: str = Depends(get_current_user)):
    """Get current user profile."""
    user = await db.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserProfile(id=user["id"], email=user["email"], name=user["name"])


@app.get("/profile/posts", response_model=UserWithPosts)
async def get_profile_with_posts(email: str = Depends(get_current_user)):
    """Get current user with all posts."""
    user = await db.get_user_by_email(email)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    posts = await db.get_user_posts(user["id"])

    return UserWithPosts(
        user=UserProfile(id=user["id"], email=user["email"], name=user["name"]),
        posts=posts,
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
