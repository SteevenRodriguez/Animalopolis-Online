"""Audit log: Anexo A 2.6 + Cláusula 16."""
from io import BytesIO

from sqlalchemy import select

from app.models.audit import AuditLog
from tests.conftest import auth

ALTA = {
    "sede": "urdesa",
    "nombre_mascota": "Firulais",
    "nombre_propietario": "Juan Perez",
    "whatsapp": "+593991234567",
    "fecha_atencion": "2026-06-12",
    "tipo_consulta": "control",
    "consentimiento": True,
}


def _logs(db, **filters):
    stmt = select(AuditLog).order_by(AuditLog.timestamp)
    for k, v in filters.items():
        stmt = stmt.where(getattr(AuditLog, k) == v)
    return db.execute(stmt).scalars().all()


class TestAuditLogins:
    def test_successful_login_is_logged(self, client, admin_user, db_session):
        r = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.com", "password": "AdminPass!2026"},
        )
        assert r.status_code == 200
        entries = _logs(db_session, action="login")
        assert len(entries) == 1
        e = entries[0]
        assert e.user_id == admin_user.id
        assert e.user_email == "admin@example.com"
        assert e.user_rol == "admin"
        assert e.success is True

    def test_failed_login_is_logged_with_attempted_email(
        self, client, admin_user, db_session
    ):
        r = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.com", "password": "wrong"},
        )
        assert r.status_code == 401
        entries = _logs(db_session, action="login_failed")
        assert len(entries) == 1
        e = entries[0]
        assert e.user_id is None  # not authenticated
        assert e.success is False
        assert e.details["email"] == "admin@example.com"

    def test_failed_login_with_unknown_email_still_logged(
        self, client, db_session
    ):
        client.post(
            "/api/v1/auth/login",
            json={"email": "ghost@example.com", "password": "anything"},
        )
        entries = _logs(db_session, action="login_failed")
        assert len(entries) == 1


class TestAuditAlta:
    def test_create_alta_logged(
        self, client, staff_urdesa, token_urdesa, db_session
    ):
        r = client.post(
            "/api/v1/altas", headers=auth(token_urdesa), json=ALTA
        )
        assert r.status_code == 201
        entries = _logs(db_session, action="create_alta")
        assert len(entries) == 1
        e = entries[0]
        assert e.user_id == staff_urdesa.id
        assert e.resource_type == "alta"
        assert e.resource_id is not None
        assert e.details["sede"] == "urdesa"

    def test_patch_alta_records_diff(
        self, client, token_admin, db_session
    ):
        alta_id = client.post(
            "/api/v1/altas", headers=auth(token_admin), json=ALTA
        ).json()["id"]
        r = client.patch(
            f"/api/v1/altas/{alta_id}",
            headers=auth(token_admin),
            json={"tipo_consulta": "emergencia"},
        )
        assert r.status_code == 200
        entries = _logs(db_session, action="update_alta")
        assert len(entries) == 1
        e = entries[0]
        diff = e.details["diff"]
        assert diff["tipo_consulta"] == {"from": "control", "to": "emergencia"}


class TestAuditExamenAndDownload:
    def test_create_and_download_examen_are_logged(
        self, client, staff_urdesa, token_urdesa, s3_mock, db_session
    ):
        files = {"file": ("x.pdf", BytesIO(b"%PDF-1.4\n"), "application/pdf")}
        r = client.post(
            "/api/v1/examenes",
            headers=auth(token_urdesa),
            data={
                "sede": "urdesa", "nombre_mascota": "X",
                "nombre_propietario": "Y", "whatsapp": "+593991111111",
                "tipo_examen": "sangre", "consentimiento": "true",
            },
            files=files,
        )
        assert r.status_code == 201
        examen_id = r.json()["id"]

        create_logs = _logs(db_session, action="create_examen")
        assert len(create_logs) == 1
        assert create_logs[0].user_id == staff_urdesa.id

        # Trigger a download.
        r2 = client.get(
            f"/api/v1/examenes/{examen_id}/file-url",
            headers=auth(token_urdesa),
        )
        assert r2.status_code == 200

        dl_logs = _logs(db_session, action="download_examen")
        assert len(dl_logs) == 1
        assert dl_logs[0].user_id == staff_urdesa.id
        assert dl_logs[0].details["via"] == "dashboard"


class TestAuditExternalService:
    def test_marcar_enviado_logged_with_external_actor(
        self, client, token_urdesa, db_session
    ):
        alta_id = client.post(
            "/api/v1/altas", headers=auth(token_urdesa), json=ALTA
        ).json()["id"]
        r = client.post(
            f"/api/v1/envios/altas/{alta_id}/marcar-enviado",
            headers={"X-API-Key": "test-api-key"},
        )
        assert r.status_code == 200
        entries = _logs(db_session, action="mark_sent_alta")
        assert len(entries) == 1
        e = entries[0]
        assert e.user_id is None
        assert e.user_email == "service:whatsapp_external"
        assert e.user_rol == "service"
        assert e.resource_id is not None

    def test_envios_file_url_logs_download(
        self, client, token_urdesa, s3_mock, db_session
    ):
        files = {"file": ("x.pdf", BytesIO(b"%PDF-1.4\n"), "application/pdf")}
        r = client.post(
            "/api/v1/examenes",
            headers=auth(token_urdesa),
            data={
                "sede": "urdesa", "nombre_mascota": "X",
                "nombre_propietario": "Y", "whatsapp": "+593991111111",
                "tipo_examen": "sangre", "consentimiento": "true",
            },
            files=files,
        )
        examen_id = r.json()["id"]
        r2 = client.get(
            f"/api/v1/envios/examenes/{examen_id}/file-url",
            headers={"X-API-Key": "test-api-key"},
        )
        assert r2.status_code == 200
        dl = [
            e for e in _logs(db_session, action="download_examen")
            if e.details.get("via") == "envios_api"
        ]
        assert len(dl) == 1


class TestAuditUsers:
    def test_create_user_logged(self, client, token_admin, db_session):
        client.post(
            "/api/v1/usuarios",
            headers=auth(token_admin),
            json={
                "email": "new@example.com",
                "password": "SomeStrong!2026",
                "nombre": "Nuevo",
                "rol": "staff",
                "sede": "urdesa",
            },
        )
        entries = _logs(db_session, action="create_user")
        assert len(entries) == 1
        assert entries[0].details["email"] == "new@example.com"

    def test_deactivate_user_logged(
        self, client, token_admin, staff_urdesa, db_session
    ):
        r = client.delete(
            f"/api/v1/usuarios/{staff_urdesa.id}", headers=auth(token_admin)
        )
        assert r.status_code == 204
        entries = _logs(db_session, action="deactivate_user")
        assert len(entries) == 1


class TestAuditEndpoint:
    def test_admin_can_list_audit(self, client, token_admin):
        # Trigger an event first.
        client.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.com", "password": "AdminPass!2026"},
        )
        r = client.get("/api/v1/auditoria", headers=auth(token_admin))
        assert r.status_code == 200
        assert r.json()["total"] >= 1

    def test_staff_cannot_list_audit(self, client, token_urdesa):
        r = client.get("/api/v1/auditoria", headers=auth(token_urdesa))
        assert r.status_code == 403

    def test_consulta_cannot_list_audit(self, client, token_consulta):
        r = client.get("/api/v1/auditoria", headers=auth(token_consulta))
        assert r.status_code == 403

    def test_audit_filters_by_action(self, client, token_admin):
        client.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.com", "password": "AdminPass!2026"},
        )
        r = client.get(
            "/api/v1/auditoria?action=login", headers=auth(token_admin)
        )
        assert r.status_code == 200
        assert all(item["action"] == "login" for item in r.json()["items"])

    def test_audit_filters_by_success_false(self, client, token_admin):
        client.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.com", "password": "wrong"},
        )
        r = client.get(
            "/api/v1/auditoria?success=false", headers=auth(token_admin)
        )
        assert r.status_code == 200
        assert all(item["success"] is False for item in r.json()["items"])
