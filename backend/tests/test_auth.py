"""
tests/test_auth.py
────────────────────
Tests for authentication endpoints:
  - Registration (happy path, duplicate email, weak password)
  - Login (valid, invalid email, wrong password)
  - Protected route access
  - Token validation
"""

from fastapi.testclient import TestClient

from tests.conftest import auth_headers, register_and_login


def test_health_endpoint(test_client: TestClient):
    resp = test_client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("ok", "degraded")


class TestRegistration:
    def test_register_success(self, test_client: TestClient):
        resp = test_client.post("/api/auth/register", json={
            "name": "Alice Smith",
            "email": "alice@example.com",
            "password": "SecurePass1",
        })
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["email"] == "alice@example.com"
        assert "password" not in str(data)
        assert "password_hash" not in str(data)

    def test_register_duplicate_email(self, test_client: TestClient):
        payload = {"name": "Bob", "email": "bob@example.com", "password": "SecurePass1"}
        test_client.post("/api/auth/register", json=payload)
        resp = test_client.post("/api/auth/register", json=payload)
        assert resp.status_code == 409

    def test_register_weak_password_no_uppercase(self, test_client: TestClient):
        resp = test_client.post("/api/auth/register", json={
            "name": "Charlie",
            "email": "charlie@example.com",
            "password": "nouppercase1",
        })
        assert resp.status_code == 422

    def test_register_weak_password_no_digit(self, test_client: TestClient):
        resp = test_client.post("/api/auth/register", json={
            "name": "Diana",
            "email": "diana@example.com",
            "password": "NoDigitHere",
        })
        assert resp.status_code == 422

    def test_register_missing_email(self, test_client: TestClient):
        resp = test_client.post("/api/auth/register", json={
            "name": "Eve",
            "password": "SecurePass1",
        })
        assert resp.status_code == 422

    def test_register_short_name(self, test_client: TestClient):
        resp = test_client.post("/api/auth/register", json={
            "name": "A",
            "email": "short@example.com",
            "password": "SecurePass1",
        })
        assert resp.status_code == 422


class TestLogin:
    def test_login_success(self, test_client: TestClient):
        test_client.post("/api/auth/register", json={
            "name": "Frank",
            "email": "frank@example.com",
            "password": "SecurePass1",
        })
        resp = test_client.post("/api/auth/login", json={
            "email": "frank@example.com",
            "password": "SecurePass1",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, test_client: TestClient):
        test_client.post("/api/auth/register", json={
            "name": "Grace",
            "email": "grace@example.com",
            "password": "SecurePass1",
        })
        resp = test_client.post("/api/auth/login", json={
            "email": "grace@example.com",
            "password": "WrongPassword1",
        })
        assert resp.status_code == 401

    def test_login_unknown_email(self, test_client: TestClient):
        resp = test_client.post("/api/auth/login", json={
            "email": "nobody@example.com",
            "password": "Whatever1",
        })
        assert resp.status_code == 401


class TestProtectedRoutes:
    def test_get_me_requires_auth(self, test_client: TestClient):
        resp = test_client.get("/api/auth/me")
        assert resp.status_code == 401

    def test_get_me_with_valid_token(self, test_client: TestClient):
        token = register_and_login(test_client, "me@example.com")
        resp = test_client.get("/api/auth/me", headers=auth_headers(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "me@example.com"
        assert "password_hash" not in data

    def test_get_me_with_invalid_token(self, test_client: TestClient):
        resp = test_client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalidtoken.abc.xyz"},
        )
        assert resp.status_code == 401

    def test_update_profile(self, test_client: TestClient):
        token = register_and_login(test_client, "profile@example.com")
        resp = test_client.patch(
            "/api/auth/profile",
            json={"name": "Updated Name"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Name"

    def test_change_password(self, test_client: TestClient):
        token = register_and_login(test_client, "changepw@example.com")
        resp = test_client.post(
            "/api/auth/change-password",
            json={"current_password": "Testpass1", "new_password": "NewSecure1"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 204

    def test_change_password_wrong_current(self, test_client: TestClient):
        token = register_and_login(test_client, "badpw@example.com")
        resp = test_client.post(
            "/api/auth/change-password",
            json={"current_password": "WrongCurrent1", "new_password": "NewSecure1"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 401
