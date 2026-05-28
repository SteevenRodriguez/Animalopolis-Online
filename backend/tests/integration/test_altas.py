from tests.conftest import auth

ALTA_BASE = {
    "nombre_mascota": "Firulais",
    "nombre_propietario": "Juan Perez",
    "whatsapp": "+593991234567",
    "fecha_atencion": "2026-05-28",
    "tipo_consulta": "control",
    "consentimiento": True,
}


class TestAltasCreation:
    def test_staff_creates_alta_in_own_sede(self, client, token_urdesa):
        r = client.post(
            "/api/v1/altas",
            headers=auth(token_urdesa),
            json={**ALTA_BASE, "sede": "urdesa"},
        )
        assert r.status_code == 201
        body = r.json()
        assert body["sede"] == "urdesa"
        assert body["estado_envio"] == "pendiente"
        assert body["consentimiento"] is True

    def test_staff_cannot_create_alta_in_other_sede(self, client, token_urdesa):
        r = client.post(
            "/api/v1/altas",
            headers=auth(token_urdesa),
            json={**ALTA_BASE, "sede": "ciudad_celeste"},
        )
        assert r.status_code == 403

    def test_admin_can_create_in_any_sede(self, client, token_admin):
        for sede in ("urdesa", "ciudad_celeste"):
            r = client.post(
                "/api/v1/altas",
                headers=auth(token_admin),
                json={**ALTA_BASE, "sede": sede},
            )
            assert r.status_code == 201, r.json()

    def test_consentimiento_required(self, client, token_urdesa):
        r = client.post(
            "/api/v1/altas",
            headers=auth(token_urdesa),
            json={**ALTA_BASE, "sede": "urdesa", "consentimiento": False},
        )
        assert r.status_code == 422

    def test_invalid_whatsapp_rejected(self, client, token_urdesa):
        r = client.post(
            "/api/v1/altas",
            headers=auth(token_urdesa),
            json={**ALTA_BASE, "sede": "urdesa", "whatsapp": "abc"},
        )
        assert r.status_code == 422

    def test_unauthenticated_cannot_create(self, client):
        r = client.post("/api/v1/altas", json={**ALTA_BASE, "sede": "urdesa"})
        assert r.status_code == 401


class TestAltasListing:
    def _seed(self, client, token_urdesa, token_celeste):
        client.post(
            "/api/v1/altas",
            headers=auth(token_urdesa),
            json={**ALTA_BASE, "sede": "urdesa"},
        )
        client.post(
            "/api/v1/altas",
            headers=auth(token_celeste),
            json={
                **ALTA_BASE,
                "sede": "ciudad_celeste",
                "whatsapp": "+593987654321",
                "nombre_propietario": "Maria Gomez",
            },
        )

    def test_admin_sees_all(
        self, client, token_admin, token_urdesa, token_celeste
    ):
        self._seed(client, token_urdesa, token_celeste)
        r = client.get("/api/v1/altas", headers=auth(token_admin))
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 2
        sedes = {item["sede"] for item in data["items"]}
        assert sedes == {"urdesa", "ciudad_celeste"}

    def test_staff_sees_only_own_sede(
        self, client, token_urdesa, token_celeste
    ):
        self._seed(client, token_urdesa, token_celeste)
        r = client.get("/api/v1/altas", headers=auth(token_urdesa))
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 1
        assert data["items"][0]["sede"] == "urdesa"

    def test_staff_cannot_override_sede_filter(
        self, client, token_urdesa, token_celeste
    ):
        # Even if staff sends ?sede=ciudad_celeste, the WHERE clause is forced
        # to their own sede — they get an empty list, never another sede's data.
        self._seed(client, token_urdesa, token_celeste)
        r = client.get(
            "/api/v1/altas?sede=ciudad_celeste", headers=auth(token_urdesa)
        )
        assert r.status_code == 200
        assert r.json()["total"] == 0

    def test_staff_cannot_read_other_sede_alta_by_id(
        self, client, token_urdesa, token_celeste
    ):
        r_create = client.post(
            "/api/v1/altas",
            headers=auth(token_celeste),
            json={**ALTA_BASE, "sede": "ciudad_celeste"},
        )
        alta_id = r_create.json()["id"]
        r = client.get(f"/api/v1/altas/{alta_id}", headers=auth(token_urdesa))
        # 404 (not 403) to avoid disclosing existence.
        assert r.status_code == 404

    def test_filter_by_estado_envio(self, client, token_admin, token_urdesa):
        client.post(
            "/api/v1/altas",
            headers=auth(token_urdesa),
            json={**ALTA_BASE, "sede": "urdesa"},
        )
        r = client.get(
            "/api/v1/altas?estado_envio=pendiente", headers=auth(token_admin)
        )
        assert r.status_code == 200
        assert r.json()["total"] == 1

    def test_pagination(self, client, token_admin, token_urdesa):
        for i in range(5):
            client.post(
                "/api/v1/altas",
                headers=auth(token_urdesa),
                json={
                    **ALTA_BASE,
                    "sede": "urdesa",
                    "whatsapp": f"+59399123456{i}",
                    "nombre_propietario": f"Owner {i}",
                },
            )
        r = client.get("/api/v1/altas?page=1&size=2", headers=auth(token_admin))
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2


class TestUsuariosAccessControl:
    def test_staff_cannot_list_users(self, client, token_urdesa):
        r = client.get("/api/v1/usuarios", headers=auth(token_urdesa))
        assert r.status_code == 403

    def test_admin_can_list_users(self, client, token_admin):
        r = client.get("/api/v1/usuarios", headers=auth(token_admin))
        assert r.status_code == 200
        assert r.json()["total"] >= 1

    def test_staff_cannot_create_users(self, client, token_urdesa):
        r = client.post(
            "/api/v1/usuarios",
            headers=auth(token_urdesa),
            json={
                "email": "new@example.com",
                "password": "NewPass!2026",
                "nombre": "Nuevo",
                "rol": "staff",
                "sede": "urdesa",
            },
        )
        assert r.status_code == 403


class TestEnviosApi:
    def test_envios_requires_api_key(self, client):
        r = client.get("/api/v1/envios/altas/pendientes")
        assert r.status_code == 401

    def test_envios_rejects_wrong_api_key(self, client):
        r = client.get(
            "/api/v1/envios/altas/pendientes", headers={"X-API-Key": "wrong"}
        )
        assert r.status_code == 401

    def test_envios_accepts_valid_api_key(self, client, token_urdesa):
        client.post(
            "/api/v1/altas",
            headers=auth(token_urdesa),
            json={**ALTA_BASE, "sede": "urdesa"},
        )
        r = client.get(
            "/api/v1/envios/altas/pendientes",
            headers={"X-API-Key": "test-api-key"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 1
        assert data["items"][0]["estado_envio"] == "pendiente"

    def test_marcar_enviado(self, client, token_urdesa):
        r_create = client.post(
            "/api/v1/altas",
            headers=auth(token_urdesa),
            json={**ALTA_BASE, "sede": "urdesa"},
        )
        alta_id = r_create.json()["id"]
        r = client.post(
            f"/api/v1/envios/altas/{alta_id}/marcar-enviado",
            headers={"X-API-Key": "test-api-key"},
        )
        assert r.status_code == 200
        assert r.json()["estado_envio"] == "enviado"
        # Now pending list is empty.
        r2 = client.get(
            "/api/v1/envios/altas/pendientes",
            headers={"X-API-Key": "test-api-key"},
        )
        assert r2.json()["total"] == 0
