"""Confirm error responses never leak stack traces, file paths, SQL fragments,
secrets, or internal class names."""
from tests.conftest import auth

LEAK_INDICATORS = [
    "Traceback",
    "/home/",
    "/usr/",
    "site-packages",
    "psycopg",
    "sqlalchemy",
    "argon2",
    "APP_SECRET_KEY",
    "WHATSAPP_SERVICE_API_KEY",
    "DATABASE_URL",
    "SELECT ",
    "INSERT INTO",
    "UPDATE ",
]


def _assert_no_leaks(body: str):
    low = body.lower()
    for indicator in LEAK_INDICATORS:
        assert indicator.lower() not in low, (
            f"Sensitive substring leaked in response: {indicator!r}\n"
            f"Body: {body[:500]}"
        )


class TestErrorLeakage:
    def test_404_does_not_leak(self, client):
        r = client.get("/api/v1/this-does-not-exist")
        assert r.status_code == 404
        _assert_no_leaks(r.text)

    def test_405_does_not_leak(self, client):
        r = client.delete("/api/v1/auth/login")
        assert r.status_code in (405, 401, 422)
        _assert_no_leaks(r.text)

    def test_validation_error_returns_clean_details(self, client, token_admin):
        r = client.post(
            "/api/v1/altas",
            headers=auth(token_admin),
            json={"sede": "marte", "consentimiento": True},
        )
        assert r.status_code == 422
        # Pydantic field paths are OK (e.g. "loc": ["body","sede"]) but not Python tracebacks.
        _assert_no_leaks(r.text)

    def test_401_does_not_leak_internal_paths(self, client):
        r = client.get("/api/v1/altas")
        assert r.status_code == 401
        _assert_no_leaks(r.text)

    def test_403_does_not_leak(self, client, token_urdesa):
        r = client.get("/api/v1/usuarios", headers=auth(token_urdesa))
        assert r.status_code == 403
        _assert_no_leaks(r.text)

    def test_uuid_validation_failure_does_not_leak(self, client, token_admin):
        r = client.get(
            "/api/v1/altas/totally-not-a-uuid", headers=auth(token_admin)
        )
        assert r.status_code == 422
        _assert_no_leaks(r.text)

    def test_login_does_not_distinguish_unknown_user_vs_wrong_password(
        self, client, admin_user
    ):
        r_unknown = client.post(
            "/api/v1/auth/login",
            json={"email": "ghost@example.com", "password": "anything"},
        )
        r_wrong = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.com", "password": "wrongpass"},
        )
        # Same status, same body shape — no enumeration via timing/response.
        assert r_unknown.status_code == r_wrong.status_code == 401
        assert (
            r_unknown.json()["error"]["message"]
            == r_wrong.json()["error"]["message"]
        )
