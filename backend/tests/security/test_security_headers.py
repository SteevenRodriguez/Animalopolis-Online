"""Security headers and CORS sanity."""
from tests.conftest import auth


class TestSecurityHeaders:
    def test_default_headers_present(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        h = {k.lower(): v for k, v in r.headers.items()}
        assert h.get("x-content-type-options") == "nosniff"
        assert h.get("x-frame-options") == "DENY"
        assert h.get("referrer-policy") == "no-referrer"
        assert "geolocation" in h.get("permissions-policy", "")

    def test_headers_present_on_api_response_too(self, client, token_admin):
        r = client.get("/api/v1/auth/me", headers=auth(token_admin))
        h = {k.lower(): v for k, v in r.headers.items()}
        assert h.get("x-content-type-options") == "nosniff"
        assert h.get("x-frame-options") == "DENY"

    def test_headers_present_on_error_responses(self, client):
        r = client.get("/api/v1/auth/me")  # 401
        h = {k.lower(): v for k, v in r.headers.items()}
        assert h.get("x-content-type-options") == "nosniff"


class TestCORS:
    def test_allowed_origin_is_echoed_not_wildcard(self, client):
        r = client.options(
            "/api/v1/auth/login",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        # CORS preflight should succeed and echo the specific origin (not *).
        origin = r.headers.get("access-control-allow-origin")
        assert origin == "http://localhost:5173"
        assert origin != "*"

    def test_disallowed_origin_does_not_get_cors_headers(self, client):
        r = client.options(
            "/api/v1/auth/login",
            headers={
                "Origin": "http://evil.example.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        origin = r.headers.get("access-control-allow-origin")
        # Either header is missing entirely, or it's not "*".
        assert origin != "*"
        assert origin != "http://evil.example.com"

    def test_allow_credentials_does_not_combine_with_wildcard(self, client):
        # If allow-credentials is true, ACAO MUST NOT be "*" (browser will reject).
        r = client.options(
            "/api/v1/auth/login",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        ac = r.headers.get("access-control-allow-credentials")
        ao = r.headers.get("access-control-allow-origin")
        if ac and ac.lower() == "true":
            assert ao != "*"
