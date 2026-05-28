import time

from app.core.security import create_access_token
from tests.conftest import auth


class TestAuth:
    def test_login_success(self, client, admin_user):
        r = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.com", "password": "AdminPass!2026"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["token_type"] == "bearer"
        assert data["rol"] == "admin"
        assert data["sede"] is None
        assert data["access_token"]

    def test_login_wrong_password(self, client, admin_user):
        r = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.com", "password": "wrong"},
        )
        assert r.status_code == 401
        # No leaking of which field is wrong.
        assert "Credenciales inválidas" in r.json()["error"]["message"]

    def test_login_unknown_user(self, client):
        r = client.post(
            "/api/v1/auth/login",
            json={"email": "ghost@example.com", "password": "whatever"},
        )
        assert r.status_code == 401

    def test_me_with_token(self, client, admin_user, token_admin):
        r = client.get("/api/v1/auth/me", headers=auth(token_admin))
        assert r.status_code == 200
        data = r.json()
        assert data["email"] == "admin@example.com"
        assert data["rol"] == "admin"

    def test_me_without_token(self, client):
        r = client.get("/api/v1/auth/me")
        assert r.status_code == 401

    def test_me_with_invalid_token(self, client):
        r = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not-a-jwt"})
        assert r.status_code == 401

    def test_me_with_expired_token(self, client, admin_user):
        expired = create_access_token(
            subject=str(admin_user.id), expires_minutes=-1
        )
        r = client.get("/api/v1/auth/me", headers=auth(expired))
        assert r.status_code == 401
        assert "expirado" in r.json()["error"]["message"].lower()

    def test_password_is_hashed_not_plaintext(self, db_session, admin_user):
        # Reload from DB.
        db_session.refresh(admin_user)
        assert admin_user.password_hash != "AdminPass!2026"
        assert admin_user.password_hash.startswith("$argon2")
