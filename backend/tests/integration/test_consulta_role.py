"""Rol 'Consulta' — read-only, sede-scoped. Required by Anexo A 2.5.c."""
from io import BytesIO

from tests.conftest import auth

ALTA_PAYLOAD = {
    "sede": "urdesa",
    "nombre_mascota": "Firulais",
    "nombre_propietario": "Juan Perez",
    "whatsapp": "+593991234567",
    "fecha_atencion": "2026-06-12",
    "tipo_consulta": "control",
    "consentimiento": True,
}


def _pdf():
    return b"%PDF-1.4\nhello"


class TestConsultaCanRead:
    def test_can_login(self, client, consulta_urdesa):
        r = client.post(
            "/api/v1/auth/login",
            json={"email": "consulta@example.com", "password": "ConsultaPass!2026"},
        )
        assert r.status_code == 200
        assert r.json()["rol"] == "consulta"
        assert r.json()["sede"] == "urdesa"

    def test_can_list_altas_own_sede(
        self, client, token_admin, token_consulta
    ):
        client.post(
            "/api/v1/altas",
            headers=auth(token_admin),
            json={**ALTA_PAYLOAD, "sede": "urdesa"},
        )
        client.post(
            "/api/v1/altas",
            headers=auth(token_admin),
            json={
                **ALTA_PAYLOAD,
                "sede": "ciudad_celeste",
                "whatsapp": "+593987654321",
            },
        )
        r = client.get("/api/v1/altas", headers=auth(token_consulta))
        assert r.status_code == 200
        items = r.json()["items"]
        assert all(a["sede"] == "urdesa" for a in items)

    def test_can_get_alta_detail_own_sede(
        self, client, token_admin, token_consulta
    ):
        r_create = client.post(
            "/api/v1/altas", headers=auth(token_admin), json=ALTA_PAYLOAD
        )
        alta_id = r_create.json()["id"]
        r = client.get(f"/api/v1/altas/{alta_id}", headers=auth(token_consulta))
        assert r.status_code == 200

    def test_can_download_examen(
        self, client, token_admin, token_consulta, s3_mock
    ):
        files = {"file": ("ok.pdf", BytesIO(_pdf()), "application/pdf")}
        r_create = client.post(
            "/api/v1/examenes",
            headers=auth(token_admin),
            data={
                "sede": "urdesa", "nombre_mascota": "X",
                "nombre_propietario": "Y", "whatsapp": "+593991111111",
                "tipo_examen": "sangre", "consentimiento": "true",
            },
            files=files,
        )
        examen_id = r_create.json()["id"]
        r = client.get(
            f"/api/v1/examenes/{examen_id}/file-url",
            headers=auth(token_consulta),
        )
        assert r.status_code == 200
        assert "X-Amz-Signature" in r.json()["url"]


class TestConsultaCannotWrite:
    def test_cannot_create_alta(self, client, token_consulta):
        r = client.post(
            "/api/v1/altas", headers=auth(token_consulta), json=ALTA_PAYLOAD
        )
        assert r.status_code == 403

    def test_cannot_create_examen(self, client, token_consulta, s3_mock):
        files = {"file": ("ok.pdf", BytesIO(_pdf()), "application/pdf")}
        r = client.post(
            "/api/v1/examenes",
            headers=auth(token_consulta),
            data={
                "sede": "urdesa", "nombre_mascota": "X",
                "nombre_propietario": "Y", "whatsapp": "+593991111111",
                "tipo_examen": "sangre", "consentimiento": "true",
            },
            files=files,
        )
        assert r.status_code == 403

    def test_cannot_patch_alta(self, client, token_admin, token_consulta):
        r_create = client.post(
            "/api/v1/altas", headers=auth(token_admin), json=ALTA_PAYLOAD
        )
        alta_id = r_create.json()["id"]
        r = client.patch(
            f"/api/v1/altas/{alta_id}",
            headers=auth(token_consulta),
            json={"tipo_consulta": "emergencia"},
        )
        assert r.status_code == 403

    def test_cannot_manage_users(self, client, token_consulta):
        r = client.get("/api/v1/usuarios", headers=auth(token_consulta))
        assert r.status_code == 403

    def test_cannot_read_audit(self, client, token_consulta):
        r = client.get("/api/v1/auditoria", headers=auth(token_consulta))
        assert r.status_code == 403


class TestConsultaSedeIsolation:
    def test_consulta_cannot_see_other_sede_in_list(
        self, client, token_admin, token_consulta
    ):
        client.post(
            "/api/v1/altas",
            headers=auth(token_admin),
            json={**ALTA_PAYLOAD, "sede": "ciudad_celeste",
                  "whatsapp": "+593987654321"},
        )
        r = client.get("/api/v1/altas", headers=auth(token_consulta))
        assert r.status_code == 200
        assert all(a["sede"] == "urdesa" for a in r.json()["items"])

    def test_consulta_cannot_read_other_sede_by_id(
        self, client, token_admin, token_consulta
    ):
        r_create = client.post(
            "/api/v1/altas",
            headers=auth(token_admin),
            json={**ALTA_PAYLOAD, "sede": "ciudad_celeste",
                  "whatsapp": "+593987654321"},
        )
        alta_id = r_create.json()["id"]
        r = client.get(f"/api/v1/altas/{alta_id}", headers=auth(token_consulta))
        assert r.status_code == 404


class TestConsultaSchemaValidation:
    def test_consulta_requires_sede_at_creation(self, client, token_admin):
        r = client.post(
            "/api/v1/usuarios",
            headers=auth(token_admin),
            json={
                "email": "new-consulta@example.com",
                "password": "ConsultaPass!2026",
                "nombre": "Nueva",
                "rol": "consulta",
                "sede": None,
            },
        )
        assert r.status_code == 422

    def test_consulta_with_sede_is_created(self, client, token_admin):
        r = client.post(
            "/api/v1/usuarios",
            headers=auth(token_admin),
            json={
                "email": "new-consulta@example.com",
                "password": "ConsultaPass!2026",
                "nombre": "Nueva Consulta",
                "rol": "consulta",
                "sede": "urdesa",
            },
        )
        assert r.status_code == 201
        assert r.json()["rol"] == "consulta"
        assert r.json()["sede"] == "urdesa"
