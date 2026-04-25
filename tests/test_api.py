import pytest
import os
import asyncio
from fastapi.testclient import TestClient
from src.main import app, db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db(event_loop):
    """Setup and teardown test database for each test."""
    async def _setup():
        await db.connect()

    async def _teardown():
        await db.disconnect()

    event_loop.run_until_complete(_setup())
    yield
    event_loop.run_until_complete(_teardown())
    if os.path.exists("auth.db"):
        os.remove("auth.db")


class TestHealth:
    def test_health_check(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestRegister:
    def test_register_success(self):
        response = client.post(
            "/register",
            json={
                "email": "alice@example.com",
                "name": "Alice",
                "password": "SecurePass123!",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "alice@example.com"
        assert data["name"] == "Alice"
        assert "id" in data

    def test_register_duplicate_email(self):
        client.post(
            "/register",
            json={
                "email": "alice@example.com",
                "name": "Alice",
                "password": "SecurePass123!",
            },
        )
        response = client.post(
            "/register",
            json={
                "email": "alice@example.com",
                "name": "Alice2",
                "password": "SecurePass123!",
            },
        )
        assert response.status_code == 409
        assert "already registered" in response.json()["detail"]

    def test_register_weak_password(self):
        response = client.post(
            "/register",
            json={"email": "alice@example.com", "name": "Alice", "password": "weak"},
        )
        assert response.status_code == 400
        assert "strength requirements" in response.json()["detail"]

    def test_register_invalid_email(self):
        response = client.post(
            "/register",
            json={
                "email": "not-an-email",
                "name": "Alice",
                "password": "SecurePass123!",
            },
        )
        assert response.status_code == 422


class TestLogin:
    def test_login_success(self):
        client.post(
            "/register",
            json={
                "email": "alice@example.com",
                "name": "Alice",
                "password": "SecurePass123!",
            },
        )
        response = client.post(
            "/login",
            json={"email": "alice@example.com", "password": "SecurePass123!"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["email"] == "alice@example.com"

    def test_login_wrong_password(self):
        client.post(
            "/register",
            json={
                "email": "alice@example.com",
                "name": "Alice",
                "password": "SecurePass123!",
            },
        )
        response = client.post(
            "/login",
            json={"email": "alice@example.com", "password": "WrongPassword123!"},
        )
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]

    def test_login_nonexistent_user(self):
        response = client.post(
            "/login",
            json={"email": "nonexistent@example.com", "password": "SomePass123!"},
        )
        assert response.status_code == 401


class TestProfile:
    def test_get_profile_with_valid_token(self):
        client.post(
            "/register",
            json={
                "email": "alice@example.com",
                "name": "Alice",
                "password": "SecurePass123!",
            },
        )
        login_response = client.post(
            "/login",
            json={"email": "alice@example.com", "password": "SecurePass123!"},
        )
        token = login_response.json()["token"]

        response = client.get(
            "/profile", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "alice@example.com"
        assert data["name"] == "Alice"

    def test_get_profile_missing_auth_header(self):
        response = client.get("/profile")
        assert response.status_code == 401

    def test_get_profile_invalid_token(self):
        response = client.get(
            "/profile", headers={"Authorization": "Bearer invalid.token.here"}
        )
        assert response.status_code == 401


class TestPasswordReset:
    def test_request_reset_success(self):
        client.post(
            "/register",
            json={
                "email": "alice@example.com",
                "name": "Alice",
                "password": "SecurePass123!",
            },
        )
        response = client.post(
            "/reset-password", json={"email": "alice@example.com"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["email"] == "alice@example.com"
        assert data["expires_in"] == 1800

    def test_request_reset_nonexistent_user(self):
        response = client.post(
            "/reset-password", json={"email": "nonexistent@example.com"}
        )
        assert response.status_code == 404

    def test_confirm_reset_success(self):
        client.post(
            "/register",
            json={
                "email": "alice@example.com",
                "name": "Alice",
                "password": "SecurePass123!",
            },
        )
        reset_response = client.post(
            "/reset-password", json={"email": "alice@example.com"}
        )
        token = reset_response.json()["token"]

        response = client.post(
            "/confirm-reset",
            json={"token": token, "new_password": "NewPass456!"},
        )
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_login_with_new_password(self):
        client.post(
            "/register",
            json={
                "email": "alice@example.com",
                "name": "Alice",
                "password": "SecurePass123!",
            },
        )
        reset_response = client.post(
            "/reset-password", json={"email": "alice@example.com"}
        )
        token = reset_response.json()["token"]

        client.post(
            "/confirm-reset",
            json={"token": token, "new_password": "NewPass456!"},
        )

        login_response = client.post(
            "/login",
            json={"email": "alice@example.com", "password": "NewPass456!"},
        )
        assert login_response.status_code == 200
        assert "token" in login_response.json()

    def test_confirm_reset_invalid_token(self):
        response = client.post(
            "/confirm-reset",
            json={"token": "invalid.token.here", "new_password": "NewPass456!"},
        )
        assert response.status_code == 400

    def test_confirm_reset_weak_password(self):
        client.post(
            "/register",
            json={
                "email": "alice@example.com",
                "name": "Alice",
                "password": "SecurePass123!",
            },
        )
        reset_response = client.post(
            "/reset-password", json={"email": "alice@example.com"}
        )
        token = reset_response.json()["token"]

        response = client.post(
            "/confirm-reset", json={"token": token, "new_password": "weak"}
        )
        assert response.status_code == 400
