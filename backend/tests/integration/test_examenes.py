from io import BytesIO

from tests.conftest import auth


def _pdf_bytes(size_padding: int = 0) -> bytes:
    return b"%PDF-1.4\n%test pdf content\n" + b"\x00" * size_padding


def _png_bytes() -> bytes:
    return b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


FORM_BASE = {
    "sede": "urdesa",
    "nombre_mascota": "Firulais",
    "nombre_propietario": "Juan Perez",
    "whatsapp": "+593991234567",
    "tipo_examen": "sangre",
    "consentimiento": "true",
}


def _upload(client, token, *, file_bytes, filename="examen.pdf",
            mime="application/pdf", form=None):
    form = {**FORM_BASE, **(form or {})}
    files = {"file": (filename, BytesIO(file_bytes), mime)}
    return client.post(
        "/api/v1/examenes",
        headers=auth(token),
        data=form,
        files=files,
    )


class TestExamenUpload:
    def test_staff_uploads_pdf(self, client, token_urdesa, s3_mock):
        r = _upload(client, token_urdesa, file_bytes=_pdf_bytes())
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["sede"] == "urdesa"
        assert body["tipo_examen"] == "sangre"
        assert body["archivo_mime"] == "application/pdf"
        assert body["estado_envio"] == "pendiente"
        # The DB stored only metadata + key, not the file.
        assert "storage_key" not in body  # not exposed in response schema

        # The object exists in the mocked bucket.
        objs = s3_mock.list_objects_v2(Bucket="animalopolis-examenes")
        assert objs.get("KeyCount", 0) == 1
        assert objs["Contents"][0]["Key"].startswith("examenes/urdesa/")

    def test_staff_uploads_png(self, client, token_urdesa, s3_mock):
        r = _upload(
            client, token_urdesa,
            file_bytes=_png_bytes(),
            filename="rx.png", mime="image/png",
        )
        assert r.status_code == 201, r.text

    def test_admin_can_upload_any_sede(self, client, token_admin, s3_mock):
        r = _upload(
            client, token_admin, file_bytes=_pdf_bytes(),
            form={"sede": "ciudad_celeste"},
        )
        assert r.status_code == 201, r.text

    def test_staff_cannot_upload_to_other_sede(self, client, token_urdesa, s3_mock):
        r = _upload(
            client, token_urdesa, file_bytes=_pdf_bytes(),
            form={"sede": "ciudad_celeste"},
        )
        assert r.status_code == 403

    def test_consentimiento_required(self, client, token_urdesa, s3_mock):
        r = _upload(
            client, token_urdesa, file_bytes=_pdf_bytes(),
            form={"consentimiento": "false"},
        )
        assert r.status_code == 422

    def test_invalid_mime_rejected(self, client, token_urdesa, s3_mock):
        r = _upload(
            client, token_urdesa,
            file_bytes=b"MZ\x90\x00fakebinary",
            filename="evil.exe",
            mime="application/x-msdownload",
        )
        assert r.status_code == 422

    def test_mime_spoofing_rejected(self, client, token_urdesa, s3_mock):
        # Caller claims image/png but ships PDF bytes -> magic check catches it.
        r = _upload(
            client, token_urdesa,
            file_bytes=_pdf_bytes(),
            filename="evil.png",
            mime="image/png",
        )
        assert r.status_code == 422
        assert "no coincide" in r.json()["error"]["message"]

    def test_oversize_rejected(self, client, token_urdesa, s3_mock):
        # MAX_UPLOAD_SIZE_BYTES is 2 MiB in tests.
        big = _pdf_bytes(size_padding=3 * 1024 * 1024)
        r = _upload(client, token_urdesa, file_bytes=big)
        assert r.status_code in (413, 422)

    def test_empty_file_rejected(self, client, token_urdesa, s3_mock):
        r = _upload(client, token_urdesa, file_bytes=b"")
        assert r.status_code == 422

    def test_invalid_whatsapp(self, client, token_urdesa, s3_mock):
        r = _upload(
            client, token_urdesa, file_bytes=_pdf_bytes(),
            form={"whatsapp": "abc"},
        )
        assert r.status_code == 422

    def test_unauthenticated_rejected(self, client, s3_mock):
        files = {"file": ("a.pdf", BytesIO(_pdf_bytes()), "application/pdf")}
        r = client.post("/api/v1/examenes", data=FORM_BASE, files=files)
        assert r.status_code == 401


class TestExamenListing:
    def _seed_two_sedes(self, client, token_urdesa, token_admin, s3_mock):
        _upload(client, token_urdesa, file_bytes=_pdf_bytes())
        _upload(
            client, token_admin, file_bytes=_pdf_bytes(),
            form={"sede": "ciudad_celeste", "whatsapp": "+593987654321",
                  "nombre_propietario": "Maria"},
        )

    def test_admin_sees_all(
        self, client, token_admin, token_urdesa, s3_mock
    ):
        self._seed_two_sedes(client, token_urdesa, token_admin, s3_mock)
        r = client.get("/api/v1/examenes", headers=auth(token_admin))
        assert r.status_code == 200
        assert r.json()["total"] == 2

    def test_staff_sees_only_own_sede(
        self, client, token_admin, token_urdesa, s3_mock
    ):
        self._seed_two_sedes(client, token_urdesa, token_admin, s3_mock)
        r = client.get("/api/v1/examenes", headers=auth(token_urdesa))
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 1
        assert data["items"][0]["sede"] == "urdesa"

    def test_staff_cannot_read_other_sede_examen(
        self, client, token_admin, token_urdesa, s3_mock
    ):
        r_create = _upload(
            client, token_admin, file_bytes=_pdf_bytes(),
            form={"sede": "ciudad_celeste"},
        )
        examen_id = r_create.json()["id"]
        r = client.get(
            f"/api/v1/examenes/{examen_id}", headers=auth(token_urdesa)
        )
        assert r.status_code == 404


class TestPresignedUrl:
    def test_dashboard_presigned_url(self, client, token_urdesa, s3_mock):
        r_create = _upload(client, token_urdesa, file_bytes=_pdf_bytes())
        examen_id = r_create.json()["id"]
        r = client.get(
            f"/api/v1/examenes/{examen_id}/file-url",
            headers=auth(token_urdesa),
        )
        assert r.status_code == 200
        body = r.json()
        assert "url" in body and "animalopolis-examenes" in body["url"]
        # presigned URL must include expiration markers.
        assert "X-Amz-Expires" in body["url"] or "Expires=" in body["url"]
        assert body["expires_at"]

    def test_staff_cannot_get_url_for_other_sede(
        self, client, token_admin, token_urdesa, s3_mock
    ):
        r_create = _upload(
            client, token_admin, file_bytes=_pdf_bytes(),
            form={"sede": "ciudad_celeste"},
        )
        examen_id = r_create.json()["id"]
        r = client.get(
            f"/api/v1/examenes/{examen_id}/file-url",
            headers=auth(token_urdesa),
        )
        assert r.status_code == 404


class TestExamenEnvios:
    def test_pending_list_requires_api_key(self, client, s3_mock):
        r = client.get("/api/v1/envios/examenes/pendientes")
        assert r.status_code == 401

    def test_pending_then_mark_sent_flow(
        self, client, token_urdesa, s3_mock
    ):
        r_create = _upload(client, token_urdesa, file_bytes=_pdf_bytes())
        examen_id = r_create.json()["id"]

        r = client.get(
            "/api/v1/envios/examenes/pendientes",
            headers={"X-API-Key": "test-api-key"},
        )
        assert r.status_code == 200
        assert r.json()["total"] == 1

        # External service gets presigned URL via API key.
        r_url = client.get(
            f"/api/v1/envios/examenes/{examen_id}/file-url",
            headers={"X-API-Key": "test-api-key"},
        )
        assert r_url.status_code == 200
        assert r_url.json()["url"]

        r_mark = client.post(
            f"/api/v1/envios/examenes/{examen_id}/marcar-enviado",
            headers={"X-API-Key": "test-api-key"},
        )
        assert r_mark.status_code == 200
        assert r_mark.json()["estado_envio"] == "enviado"

        r2 = client.get(
            "/api/v1/envios/examenes/pendientes",
            headers={"X-API-Key": "test-api-key"},
        )
        assert r2.json()["total"] == 0

    def test_envios_file_url_rejects_wrong_api_key(self, client, s3_mock):
        r = client.get(
            "/api/v1/envios/examenes/00000000-0000-0000-0000-000000000000/file-url",
            headers={"X-API-Key": "wrong"},
        )
        assert r.status_code == 401
