"""PATCH endpoints: Anexo A 2.1.f + Anexo B (b) — consulta y edición de registros."""
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


def _create_alta(client, token, **overrides):
    return client.post(
        "/api/v1/altas", headers=auth(token), json={**ALTA_PAYLOAD, **overrides}
    )


def _create_examen(client, token, **form_overrides):
    files = {"file": ("ok.pdf", BytesIO(b"%PDF-1.4\nhello"), "application/pdf")}
    data = {
        "sede": "urdesa", "nombre_mascota": "Firulais",
        "nombre_propietario": "Juan Perez", "whatsapp": "+593991234567",
        "tipo_examen": "sangre", "consentimiento": "true",
    }
    data.update(form_overrides)
    return client.post("/api/v1/examenes", headers=auth(token), data=data, files=files)


class TestPatchAlta:
    def test_admin_can_patch_alta(self, client, token_admin):
        alta_id = _create_alta(client, token_admin).json()["id"]
        r = client.patch(
            f"/api/v1/altas/{alta_id}",
            headers=auth(token_admin),
            json={"tipo_consulta": "emergencia", "fecha_atencion": "2026-06-13"},
        )
        assert r.status_code == 200, r.text
        assert r.json()["tipo_consulta"] == "emergencia"
        assert r.json()["fecha_atencion"] == "2026-06-13"

    def test_staff_can_patch_own_sede_alta(self, client, token_urdesa):
        alta_id = _create_alta(client, token_urdesa).json()["id"]
        r = client.patch(
            f"/api/v1/altas/{alta_id}",
            headers=auth(token_urdesa),
            json={"tipo_consulta": "vacunacion"},
        )
        assert r.status_code == 200
        assert r.json()["tipo_consulta"] == "vacunacion"

    def test_staff_cannot_patch_other_sede_alta(
        self, client, token_admin, token_urdesa
    ):
        alta_id = _create_alta(
            client, token_admin, sede="ciudad_celeste",
            whatsapp="+593987654321",
        ).json()["id"]
        r = client.patch(
            f"/api/v1/altas/{alta_id}",
            headers=auth(token_urdesa),
            json={"tipo_consulta": "emergencia"},
        )
        # 404 instead of 403 to avoid disclosing the record exists.
        assert r.status_code == 404

    def test_patch_does_not_touch_immutable_fields(self, client, token_admin):
        alta_id = _create_alta(client, token_admin).json()["id"]
        # Try to send sede and consentimiento — those are NOT in AltaUpdate,
        # FastAPI will silently ignore unknown fields (pydantic config).
        r = client.patch(
            f"/api/v1/altas/{alta_id}",
            headers=auth(token_admin),
            json={
                "sede": "ciudad_celeste",
                "consentimiento": False,
                "estado_envio": "enviado",
                "tipo_consulta": "control",
            },
        )
        assert r.status_code == 200
        body = r.json()
        assert body["sede"] == "urdesa"            # untouched
        assert body["consentimiento"] is True       # untouched
        assert body["estado_envio"] == "pendiente"  # untouched

    def test_patch_with_empty_body_is_noop(self, client, token_admin):
        alta_id = _create_alta(client, token_admin).json()["id"]
        r = client.patch(
            f"/api/v1/altas/{alta_id}", headers=auth(token_admin), json={}
        )
        assert r.status_code == 200
        assert r.json()["tipo_consulta"] == "control"


class TestPatchExamen:
    def test_admin_can_patch_tipo_examen(
        self, client, token_admin, s3_mock
    ):
        examen_id = _create_examen(client, token_admin).json()["id"]
        r = client.patch(
            f"/api/v1/examenes/{examen_id}",
            headers=auth(token_admin),
            json={"tipo_examen": "orina"},
        )
        assert r.status_code == 200
        assert r.json()["tipo_examen"] == "orina"

    def test_staff_can_patch_own_sede_examen(
        self, client, token_urdesa, s3_mock
    ):
        examen_id = _create_examen(client, token_urdesa).json()["id"]
        r = client.patch(
            f"/api/v1/examenes/{examen_id}",
            headers=auth(token_urdesa),
            json={"tipo_examen": "heces"},
        )
        assert r.status_code == 200


class TestPatchPropietario:
    def test_admin_can_patch_propietario(self, client, token_admin):
        alta = _create_alta(client, token_admin).json()
        prop_id = alta["propietario_id"]
        r = client.patch(
            f"/api/v1/propietarios/{prop_id}",
            headers=auth(token_admin),
            json={"nombre": "Juan Perez Renombrado", "whatsapp": "+593999999999"},
        )
        assert r.status_code == 200, r.text
        assert r.json()["nombre"] == "Juan Perez Renombrado"
        assert r.json()["whatsapp_e164"] == "+593999999999"

    def test_staff_cannot_patch_propietario(self, client, token_admin, token_urdesa):
        alta = _create_alta(client, token_admin).json()
        prop_id = alta["propietario_id"]
        r = client.patch(
            f"/api/v1/propietarios/{prop_id}",
            headers=auth(token_urdesa),
            json={"nombre": "X"},
        )
        assert r.status_code == 403

    def test_invalid_whatsapp_rejected(self, client, token_admin):
        alta = _create_alta(client, token_admin).json()
        prop_id = alta["propietario_id"]
        r = client.patch(
            f"/api/v1/propietarios/{prop_id}",
            headers=auth(token_admin),
            json={"whatsapp": "not-a-phone"},
        )
        assert r.status_code == 422

    def test_whatsapp_collision_returns_409(self, client, token_admin):
        # Two altas, two propietarios.
        a = _create_alta(client, token_admin).json()
        b = _create_alta(
            client, token_admin,
            whatsapp="+593987654321", nombre_propietario="Otra",
        ).json()
        # Try to set propietario A to the same number as B.
        r = client.patch(
            f"/api/v1/propietarios/{a['propietario_id']}",
            headers=auth(token_admin),
            json={"whatsapp": "+593987654321"},
        )
        assert r.status_code == 409
        assert b["propietario_id"] != a["propietario_id"]


class TestPatchMascota:
    def test_admin_can_patch_mascota(self, client, token_admin):
        alta = _create_alta(client, token_admin).json()
        mascota_id = alta["mascota_id"]
        r = client.patch(
            f"/api/v1/mascotas/{mascota_id}",
            headers=auth(token_admin),
            json={"nombre": "Firulais Junior"},
        )
        assert r.status_code == 200
        assert r.json()["nombre"] == "Firulais Junior"

    def test_staff_cannot_patch_mascota(self, client, token_admin, token_urdesa):
        alta = _create_alta(client, token_admin).json()
        mascota_id = alta["mascota_id"]
        r = client.patch(
            f"/api/v1/mascotas/{mascota_id}",
            headers=auth(token_urdesa),
            json={"nombre": "X"},
        )
        assert r.status_code == 403
