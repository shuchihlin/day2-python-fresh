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


def _hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def register(email, password):
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

        if scheme != "bearer":
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
