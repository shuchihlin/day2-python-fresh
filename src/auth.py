import os
import hashlib
import hmac
import jwt
from datetime import datetime, timedelta, timezone
from functools import wraps

JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET environment variable is required")
TOKEN_EXPIRY = "1h"

_users = {}
_reset_attempts = {}  # Track password reset attempts: email -> [timestamps]


def _hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def _cleanup_old_attempts(email):
    """Remove timestamps older than 1 hour from reset attempts."""
    now = datetime.now(timezone.utc)
    one_hour_ago = now - timedelta(hours=1)

    if email in _reset_attempts:
        _reset_attempts[email] = [
            ts for ts in _reset_attempts[email]
            if ts > one_hour_ago
        ]
        if not _reset_attempts[email]:
            del _reset_attempts[email]


def register(email, password):
    """Register a new user with email and password."""
    if not email or not password:
        return {"error": "Email and password required"}

    if email in _users:
        return {"error": "User already exists"}

    _users[email] = {
        "email": email,
        "password": _hash_password(password),
    }

    return {"success": True, "email": email}


def login(email, password):
    if not email or not password:
        return {"error": "Email and password required"}

    user = _users.get(email)
    if not user:
        return {"error": "Invalid email or password"}

    if not hmac.compare_digest(user["password"], _hash_password(password)):
        return {"error": "Invalid email or password"}

    payload = {
        "email": email,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return {"token": token, "email": email}


def verify(token):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return {"valid": True, "email": payload.get("email")}
    except Exception:
        return {"valid": False}


def auth_middleware(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = kwargs.get("auth_header", "")

        if not auth_header:
            return {"error": "Missing authorization header"}

        parts = auth_header.split(" ")
        if len(parts) != 2:
            return {"error": "Invalid authorization header"}

        scheme, token = parts[0], parts[1]

        if scheme != "Bearer":
            return {"error": "Invalid authorization scheme"}

        result = verify(token)
        if not result["valid"]:
            return {"error": "Invalid token"}

        kwargs["user"] = result
        return f(*args, **kwargs)

    return decorated


@auth_middleware
def protected_route(auth_header="", user=None):
    return {"message": f"Hello, {user['email']}"}


def request_password_reset(email):
    """Generate a password reset token for the given email."""
    if not email or email not in _users:
        return {"error": "User not found"}

    _cleanup_old_attempts(email)

    if email in _reset_attempts and len(_reset_attempts[email]) >= 5:
        return {"error": "Too many reset requests"}

    now = datetime.now(timezone.utc)
    if email not in _reset_attempts:
        _reset_attempts[email] = []
    _reset_attempts[email].append(now)

    payload = {
        "email": email,
        "type": "password_reset",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return {"token": token, "email": email, "expires_in": 1800}


def verify_and_reset_password(token, new_password):
    """Verify reset token and update password."""
    if not token or not new_password:
        return {"error": "Token and password required"}

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except Exception:
        return {"error": "Invalid or expired token"}

    if payload.get("type") != "password_reset":
        return {"error": "Invalid token type"}

    email = payload.get("email")
    if not email or email not in _users:
        return {"error": "Invalid or expired token"}

    from src.validators import is_strong_password
    if not is_strong_password(new_password):
        return {"error": "Password does not meet strength requirements"}

    _users[email]["password"] = _hash_password(new_password)
    return {"success": True, "message": "Password reset complete"}
