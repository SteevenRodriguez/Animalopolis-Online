"""Confirm passwords are never stored or returned in plaintext, and that
the hash algorithm is argon2id."""
from sqlalchemy import select, text

from app.core.security import hash_password, verify_password
from app.models.usuario import Usuario
from tests.conftest import auth


class TestPasswordHashing:
    def test_argon2id_format(self):
        h = hash_password("super-secret-password")
        assert h.startswith("$argon2")
        # Default in argon2-cffi is id; we accept i too if config changes.
        assert h.startswith("$argon2id$") or h.startswith("$argon2i$")

    def test_verify_round_trip(self):
        h = hash_password("hello-world-XYZ")
        assert verify_password("hello-world-XYZ", h) is True
        assert verify_password("hello-world-xyz", h) is False
        assert verify_password("", h) is False

    def test_hash_is_unique_per_call_for_same_password(self):
        # Different salts → different hashes.
        a = hash_password("same")
        b = hash_password("same")
        assert a != b
        assert verify_password("same", a)
        assert verify_password("same", b)

    def test_admin_bootstrap_password_is_hashed_in_db(self, db_session, admin_user):
        u = db_session.execute(
            select(Usuario).where(Usuario.email == "admin@example.com")
        ).scalar_one()
        assert u.password_hash != "AdminPass!2026"
        assert "AdminPass" not in u.password_hash

    def test_raw_sql_dump_has_no_plaintext(self, db_session, admin_user):
        # Sanity-check: nothing resembling the password leaked into any column.
        rows = db_session.execute(text("SELECT * FROM usuarios")).all()
        for row in rows:
            for val in row:
                s = str(val) if val is not None else ""
                assert "AdminPass" not in s
                assert "ChangeMeNow" not in s


class TestPasswordIsNeverInApiResponses:
    def test_login_response_omits_password(self, client, admin_user):
        r = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.com", "password": "AdminPass!2026"},
        )
        assert r.status_code == 200
        body = r.text.lower()
        assert "password" not in body
        assert "hash" not in body
        assert "argon2" not in body

    def test_me_response_omits_password(self, client, token_admin):
        r = client.get("/api/v1/auth/me", headers=auth(token_admin))
        assert r.status_code == 200
        body = r.text.lower()
        assert "password" not in body and "argon2" not in body

    def test_create_user_response_omits_password(self, client, token_admin):
        r = client.post(
            "/api/v1/usuarios",
            headers=auth(token_admin),
            json={
                "email": "new-tester@example.com",
                "password": "ThisIsMySecret2026!",
                "nombre": "Tester",
                "rol": "staff",
                "sede": "urdesa",
            },
        )
        assert r.status_code == 201
        body = r.text
        assert "ThisIsMySecret2026" not in body
        assert "password" not in body.lower()
        assert "argon2" not in body.lower()
