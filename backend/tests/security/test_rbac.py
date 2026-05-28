"""RBAC end-to-end: every protected endpoint must reject:
- no token
- invalid token
- expired token
- staff trying to act on another sede
- staff trying to use admin endpoints
"""
import uuid
from datetime import date

from app.core.security import create_access_token
from tests.conftest import auth


PROTECTED_ENDPOINTS_GET = [
    "/api/v1/auth/me",
    "/api/v1/altas",
    "/api/v1/examenes",
    "/api/v1/usuarios",
]


class TestNoTokenIsRejected:
    def test_all_protected_get_endpoints_reject_no_token(self, client):
        for path in PROTECTED_ENDPOINTS_GET:
            r = client.get(path)
            assert r.status_code == 401, f"{path} debió rechazar sin token"

    def test_invalid_token_rejected(self, client):
        for path in PROTECTED_ENDPOINTS_GET:
            r = client.get(path, headers={"Authorization": "Bearer not-a-jwt"})
            assert r.status_code == 401, f"{path} aceptó un token inválido"

    def test_tampered_token_rejected(self, client, admin_user):
        good = create_access_token(subject=str(admin_user.id))
        # Flip a single char in the payload section.
        tampered = good[:-2] + "AB"
        r = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tampered}"})
        assert r.status_code == 401

    def test_token_signed_with_wrong_secret(self, client, admin_user):
        import jwt
        bogus = jwt.encode(
            {"sub": str(admin_user.id), "exp": 9999999999, "type": "access"},
            "WRONG-SECRET",
            algorithm="HS256",
        )
        r = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {bogus}"})
        assert r.status_code == 401

    def test_expired_token_rejected_everywhere(self, client, admin_user):
        expired = create_access_token(
            subject=str(admin_user.id), expires_minutes=-5,
        )
        for path in PROTECTED_ENDPOINTS_GET:
            r = client.get(path, headers=auth(expired))
            assert r.status_code == 401


class TestStaffSedeIsolation:
    """Staff de Urdesa no puede leer NI escribir sobre datos de Ciudad Celeste."""

    def test_staff_cannot_list_other_sede_altas_via_query_param(
        self, client, token_urdesa
    ):
        # Even if the staff sends ?sede=ciudad_celeste, the WHERE is forced
        # to their own sede. Result must be their own scope, never another.
        r = client.get(
            "/api/v1/altas?sede=ciudad_celeste", headers=auth(token_urdesa)
        )
        assert r.status_code == 200
        for item in r.json()["items"]:
            assert item["sede"] == "urdesa"

    def test_staff_cannot_read_other_sede_alta_by_id_returns_404(
        self, client, token_admin, token_urdesa
    ):
        # 404 (not 403) so we don't disclose record existence.
        created = client.post(
            "/api/v1/altas",
            headers=auth(token_admin),
            json={
                "sede": "ciudad_celeste",
                "nombre_mascota": "X",
                "nombre_propietario": "Maria",
                "whatsapp": "+593987654321",
                "fecha_atencion": "2026-05-28",
                "tipo_consulta": "control",
                "consentimiento": True,
            },
        )
        alta_id = created.json()["id"]
        r = client.get(f"/api/v1/altas/{alta_id}", headers=auth(token_urdesa))
        assert r.status_code == 404
        # The body must not say "exists but forbidden" — only "no encontrado".
        assert "no encontrad" in r.json()["error"]["message"].lower()

    def test_staff_cannot_create_alta_in_other_sede(
        self, client, token_urdesa
    ):
        r = client.post(
            "/api/v1/altas",
            headers=auth(token_urdesa),
            json={
                "sede": "ciudad_celeste",
                "nombre_mascota": "Y",
                "nombre_propietario": "Otro",
                "whatsapp": "+593987654322",
                "fecha_atencion": "2026-05-28",
                "tipo_consulta": "control",
                "consentimiento": True,
            },
        )
        assert r.status_code == 403


class TestStaffCannotUseAdminEndpoints:
    def test_staff_cannot_list_users(self, client, token_urdesa):
        r = client.get("/api/v1/usuarios", headers=auth(token_urdesa))
        assert r.status_code == 403

    def test_staff_cannot_create_users(self, client, token_urdesa):
        r = client.post(
            "/api/v1/usuarios",
            headers=auth(token_urdesa),
            json={
                "email": "x@example.com", "password": "Pass!2026XXX",
                "nombre": "X", "rol": "staff", "sede": "urdesa",
            },
        )
        assert r.status_code == 403

    def test_staff_cannot_update_users(self, client, token_urdesa, admin_user):
        r = client.patch(
            f"/api/v1/usuarios/{admin_user.id}",
            headers=auth(token_urdesa),
            json={"nombre": "Hacked"},
        )
        assert r.status_code == 403

    def test_staff_cannot_delete_users(self, client, token_urdesa, admin_user):
        r = client.delete(
            f"/api/v1/usuarios/{admin_user.id}", headers=auth(token_urdesa)
        )
        assert r.status_code == 403

    def test_staff_cannot_mark_envio_via_api_key_path_without_key(
        self, client, token_urdesa
    ):
        # JWT shouldn't grant access to the /envios endpoints — these
        # require X-API-Key. Sending only a Bearer token fails.
        r = client.get(
            "/api/v1/envios/altas/pendientes", headers=auth(token_urdesa)
        )
        assert r.status_code == 401


class TestAdminCannotBeBypassed:
    def test_deactivated_admin_token_rejected(
        self, client, admin_user, db_session
    ):
        # Even with a valid token, if the user is deactivated, all routes fail.
        token = create_access_token(subject=str(admin_user.id))
        admin_user.is_active = False
        db_session.add(admin_user)
        db_session.commit()
        r = client.get("/api/v1/auth/me", headers=auth(token))
        assert r.status_code == 401

    def test_token_with_unknown_user_rejected(self, client):
        # Random UUID as subject.
        bogus = create_access_token(subject=str(uuid.uuid4()))
        r = client.get("/api/v1/auth/me", headers=auth(bogus))
        assert r.status_code == 401
