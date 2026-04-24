import os
import pytest
import jwt
from datetime import datetime, timedelta

# Import after conftest has set JWT_SECRET
from src.auth import (
    register,
    login,
    verify,
    auth_middleware,
    protected_route,
    _users,
    JWT_SECRET,
)


class TestRegister:
    def test_register_success(self):
        _users.clear()
        result = register("alice@example.com", "SecurePass123!")
        assert result["success"] is True
        assert result["email"] == "alice@example.com"

    def test_register_duplicate_user(self):
        _users.clear()
        register("bob@example.com", "Pass123!")
        result = register("bob@example.com", "DifferentPass!")
        assert "error" in result

    def test_register_missing_email(self):
        _users.clear()
        result = register("", "Pass123!")
        assert "error" in result

    def test_register_missing_password(self):
        _users.clear()
        result = register("charlie@example.com", "")
        assert "error" in result


class TestLogin:
    def setup_method(self):
        _users.clear()
        register("user@example.com", "CorrectPass123!")

    def test_login_success(self):
        result = login("user@example.com", "CorrectPass123!")
        assert "token" in result
        assert result["email"] == "user@example.com"

    def test_login_wrong_password(self):
        result = login("user@example.com", "WrongPass456!")
        assert "error" in result

    def test_login_nonexistent_user(self):
        result = login("nonexistent@example.com", "SomePass123!")
        assert "error" in result

    def test_login_missing_email(self):
        result = login("", "CorrectPass123!")
        assert "error" in result

    def test_login_missing_password(self):
        result = login("user@example.com", "")
        assert "error" in result


class TestVerify:
    def setup_method(self):
        _users.clear()
        register("verifier@example.com", "TestPass123!")

    def test_verify_valid_token(self):
        login_result = login("verifier@example.com", "TestPass123!")
        token = login_result["token"]
        result = verify(token)
        assert result["valid"] is True
        assert result["email"] == "verifier@example.com"

    def test_verify_invalid_token(self):
        result = verify("invalid.token.here")
        assert result["valid"] is False

    def test_verify_malformed_token(self):
        result = verify("not-a-jwt")
        assert result["valid"] is False

    def test_verify_empty_token(self):
        result = verify("")
        assert result["valid"] is False

    def test_verify_token_structure(self):
        login_result = login("verifier@example.com", "TestPass123!")
        token = login_result["token"]
        assert isinstance(token, str)
        assert len(token) > 0


class TestAuthMiddleware:
    def setup_method(self):
        _users.clear()
        register("middleware@example.com", "MiddlePass123!")

    def test_middleware_valid_token(self):
        login_result = login("middleware@example.com", "MiddlePass123!")
        token = login_result["token"]
        result = protected_route(auth_header=f"Bearer {token}")
        assert "message" in result
        assert "middleware@example.com" in result["message"]

    def test_middleware_missing_header(self):
        result = protected_route(auth_header="")
        assert "error" in result

    def test_middleware_malformed_header(self):
        result = protected_route(auth_header="JustAToken")
        assert "error" in result

    def test_middleware_invalid_scheme(self):
        result = protected_route(auth_header="Basic sometoken")
        assert "error" in result

    def test_middleware_invalid_token(self):
        result = protected_route(auth_header="Bearer invalid.token.here")
        assert "error" in result

    def test_middleware_empty_token(self):
        result = protected_route(auth_header="Bearer ")
        assert "error" in result


class TestTokenExpiry:
    def setup_method(self):
        _users.clear()
        register("expiry@example.com", "ExpiryPass123!")

    def test_token_has_expiry_claim(self):
        login_result = login("expiry@example.com", "ExpiryPass123!")
        token = login_result["token"]
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        assert "exp" in payload
        assert "iat" in payload
