"""Login endpoint must rate-limit excessive attempts (10/minute by default).
Uses an isolated limiter state so other tests don't interfere."""
import pytest

from app.core.rate_limit import limiter


def _reset_limiter():
    """Clear slowapi in-memory state so this test runs deterministically."""
    if hasattr(limiter, "reset"):
        try:
            limiter.reset()
            return
        except Exception:
            pass
    storage = getattr(limiter, "_storage", None)
    if storage is not None:
        if hasattr(storage, "storage") and hasattr(storage.storage, "clear"):
            storage.storage.clear()
        elif hasattr(storage, "reset"):
            storage.reset()


@pytest.fixture(autouse=True)
def reset_state():
    _reset_limiter()
    yield
    _reset_limiter()


class TestLoginRateLimit:
    def test_excessive_login_attempts_hit_429(self, client, admin_user):
        # Default cap is 10/min. Send 15 wrong-password attempts; expect a 429
        # before reaching 15.
        statuses = []
        for _ in range(15):
            r = client.post(
                "/api/v1/auth/login",
                json={"email": "admin@example.com", "password": "wrong"},
            )
            statuses.append(r.status_code)
            if r.status_code == 429:
                break
        assert 429 in statuses, f"No rate-limit response observed: {statuses}"

    def test_valid_login_still_works_when_under_cap(self, client, admin_user):
        r = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.com", "password": "AdminPass!2026"},
        )
        assert r.status_code == 200
