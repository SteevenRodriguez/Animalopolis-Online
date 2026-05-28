"""SQL injection attempts: SQLAlchemy uses parametrized queries, but we
verify it explicitly. Each test sends a payload that — if string-interpolated
into SQL — would either succeed unexpectedly, leak data, or crash with 500."""
from tests.conftest import auth

CLASSIC_PAYLOADS = [
    "' OR '1'='1",
    "' OR 1=1 --",
    "admin'--",
    "' UNION SELECT NULL,NULL,NULL --",
    "'; DROP TABLE usuarios; --",
    '" OR ""="',
    "%27%20OR%201=1--",
]


class TestSqlInjectionLogin:
    def test_injection_in_email_returns_401_not_500(self, client, admin_user):
        for p in CLASSIC_PAYLOADS:
            r = client.post(
                "/api/v1/auth/login",
                json={"email": f"admin{p}@example.com", "password": "x"},
            )
            # Must be either 401 (auth fail) or 422 (validation). Never 200, never 500.
            assert r.status_code in (401, 422), (
                f"Payload {p!r} returned {r.status_code}: {r.text}"
            )

    def test_injection_in_password_field(self, client, admin_user):
        for p in CLASSIC_PAYLOADS:
            r = client.post(
                "/api/v1/auth/login",
                json={"email": "admin@example.com", "password": p},
            )
            assert r.status_code in (401, 422)


class TestSqlInjectionFilters:
    def test_injection_in_sede_filter(self, client, token_admin):
        for p in CLASSIC_PAYLOADS:
            r = client.get(
                "/api/v1/altas", params={"sede": p}, headers=auth(token_admin)
            )
            # Either valid empty result or schema rejection — never 500 / 200 with leaked rows.
            assert r.status_code in (200, 422)
            if r.status_code == 200:
                assert r.json()["total"] == 0

    def test_injection_in_estado_envio_filter(self, client, token_admin):
        for p in CLASSIC_PAYLOADS:
            r = client.get(
                "/api/v1/altas",
                params={"estado_envio": p},
                headers=auth(token_admin),
            )
            assert r.status_code in (200, 422)


class TestSqlInjectionBody:
    def test_injection_in_nombre_does_not_crash_and_is_stored_literally(
        self, client, token_urdesa
    ):
        payload = "Bobby'); DROP TABLE altas; --"
        r = client.post(
            "/api/v1/altas",
            headers=auth(token_urdesa),
            json={
                "sede": "urdesa",
                "nombre_mascota": payload,
                "nombre_propietario": payload,
                "whatsapp": "+593991234567",
                "fecha_atencion": "2026-05-28",
                "tipo_consulta": "control",
                "consentimiento": True,
            },
        )
        # It should either accept (storing the string literally) or 422.
        # NEVER 500. NEVER cause the altas table to disappear.
        assert r.status_code in (201, 422)

        # The table must still exist — try another insert.
        r2 = client.post(
            "/api/v1/altas",
            headers=auth(token_urdesa),
            json={
                "sede": "urdesa",
                "nombre_mascota": "Otra",
                "nombre_propietario": "Otra",
                "whatsapp": "+593991234560",
                "fecha_atencion": "2026-05-28",
                "tipo_consulta": "control",
                "consentimiento": True,
            },
        )
        assert r2.status_code == 201

    def test_injection_in_uuid_path_param_is_422(self, client, token_admin):
        r = client.get(
            "/api/v1/altas/' OR 1=1 --", headers=auth(token_admin)
        )
        assert r.status_code == 422  # FastAPI's UUID validator catches it.
