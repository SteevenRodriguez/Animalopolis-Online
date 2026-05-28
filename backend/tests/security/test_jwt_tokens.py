"""JWT-specific security tests: signing, algorithm, claims integrity."""
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.config import get_settings
from app.core.security import (
    create_access_token,
    decode_access_token,
)
from tests.conftest import auth


class TestJwtIntegrity:
    def test_decode_round_trip(self):
        token = create_access_token(
            subject="user-1", extra_claims={"rol": "admin"}
        )
        payload = decode_access_token(token)
        assert payload["sub"] == "user-1"
        assert payload["rol"] == "admin"
        assert payload["type"] == "access"
        assert "exp" in payload and "iat" in payload

    def test_wrong_secret_fails_to_decode(self):
        token = create_access_token(subject="user-1")
        with pytest.raises(jwt.InvalidSignatureError):
            jwt.decode(token, "totally-wrong-secret", algorithms=["HS256"])

    def test_expired_token_raises_at_decode(self):
        token = create_access_token(subject="user-1", expires_minutes=-1)
        with pytest.raises(jwt.ExpiredSignatureError):
            decode_access_token(token)

    def test_none_algorithm_not_accepted(self, client, admin_user):
        # Defense against the classic "alg: none" attack.
        settings = get_settings()
        payload = {
            "sub": str(admin_user.id),
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
            "type": "access",
        }
        # Forge an unsigned token. The header says alg=none.
        import base64
        import json

        def b64u(data: bytes) -> bytes:
            return base64.urlsafe_b64encode(data).rstrip(b"=")

        header = b64u(json.dumps({"alg": "none", "typ": "JWT"}).encode())
        body = b64u(json.dumps(payload).encode())
        forged = b".".join([header, body, b""]).decode()
        r = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {forged}"})
        assert r.status_code == 401
        # The configured alg must remain HS256 only.
        assert settings.JWT_ALGORITHM == "HS256"

    def test_missing_subject_rejected(self, client):
        settings = get_settings()
        forged = jwt.encode(
            {
                "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
                "type": "access",
            },
            settings.APP_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )
        r = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {forged}"})
        assert r.status_code == 401

    def test_non_uuid_subject_rejected(self, client):
        settings = get_settings()
        forged = jwt.encode(
            {
                "sub": "not-a-uuid",
                "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
                "type": "access",
            },
            settings.APP_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )
        r = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {forged}"})
        assert r.status_code == 401
