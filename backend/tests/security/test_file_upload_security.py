"""Extra file-upload security tests: disguised types, scripts in SVG,
path traversal in filenames, and confirmation that nothing reaches S3
when validation fails."""
from io import BytesIO

from tests.conftest import auth

FORM = {
    "sede": "urdesa",
    "nombre_mascota": "Fido",
    "nombre_propietario": "Juan",
    "whatsapp": "+593991234567",
    "tipo_examen": "sangre",
    "consentimiento": "true",
}


def _upload(client, token, *, file_bytes, filename, mime, form=None):
    f = {**FORM, **(form or {})}
    files = {"file": (filename, BytesIO(file_bytes), mime)}
    return client.post("/api/v1/examenes", headers=auth(token), data=f, files=files)


class TestDisguisedTypes:
    def test_html_disguised_as_pdf(self, client, token_urdesa, s3_mock):
        r = _upload(
            client, token_urdesa,
            file_bytes=b"<html><script>alert(1)</script></html>",
            filename="x.pdf", mime="application/pdf",
        )
        assert r.status_code == 422

    def test_svg_rejected_even_with_image_mime(self, client, token_urdesa, s3_mock):
        # SVG can contain JS; we don't allow image/svg+xml.
        r = _upload(
            client, token_urdesa,
            file_bytes=b"<svg xmlns=\"http://www.w3.org/2000/svg\"><script>1</script></svg>",
            filename="x.svg", mime="image/svg+xml",
        )
        assert r.status_code == 422

    def test_zip_rejected(self, client, token_urdesa, s3_mock):
        zip_magic = b"PK\x03\x04" + b"\x00" * 30
        r = _upload(
            client, token_urdesa,
            file_bytes=zip_magic,
            filename="x.zip", mime="application/zip",
        )
        assert r.status_code == 422

    def test_pdf_with_image_extension_passes_only_if_mime_matches(
        self, client, token_urdesa, s3_mock
    ):
        # Real PDF bytes, declared mime image/png — magic mismatch → 422.
        r = _upload(
            client, token_urdesa,
            file_bytes=b"%PDF-1.4\nhello",
            filename="trick.png", mime="image/png",
        )
        assert r.status_code == 422

    def test_executable_with_pdf_mime(self, client, token_urdesa, s3_mock):
        elf = b"\x7fELF\x02\x01\x01\x00" + b"\x00" * 64
        r = _upload(
            client, token_urdesa,
            file_bytes=elf,
            filename="evil.pdf", mime="application/pdf",
        )
        assert r.status_code == 422


class TestFilenameHandling:
    def test_path_traversal_in_filename_is_sanitized(
        self, client, token_urdesa, s3_mock
    ):
        # The DB should store only "passwd.pdf" — never include the path.
        r = _upload(
            client, token_urdesa,
            file_bytes=b"%PDF-1.4\nhello",
            filename="../../etc/passwd.pdf",
            mime="application/pdf",
        )
        assert r.status_code == 201
        stored = r.json()["archivo_nombre"]
        assert "/" not in stored and "\\" not in stored
        assert ".." not in stored
        assert stored.endswith("passwd.pdf")

    def test_extremely_long_filename_truncated_or_accepted(
        self, client, token_urdesa, s3_mock
    ):
        long_name = "a" * 4096 + ".pdf"
        r = _upload(
            client, token_urdesa,
            file_bytes=b"%PDF-1.4\nhello",
            filename=long_name,
            mime="application/pdf",
        )
        if r.status_code == 201:
            assert len(r.json()["archivo_nombre"]) <= 255

    def test_storage_key_never_contains_user_input(
        self, client, token_urdesa, s3_mock
    ):
        r = _upload(
            client, token_urdesa,
            file_bytes=b"%PDF-1.4\nhello",
            filename="user-supplied-script.pdf",
            mime="application/pdf",
        )
        assert r.status_code == 201
        # Inspect the key in the bucket: must follow our scheme, not the user's name.
        objs = s3_mock.list_objects_v2(Bucket="animalopolis-examenes")
        key = objs["Contents"][0]["Key"]
        assert key.startswith("examenes/urdesa/")
        assert "user-supplied-script" not in key


class TestNothingLeaksToS3OnRejection:
    def test_rejected_upload_does_not_create_object(
        self, client, token_urdesa, s3_mock
    ):
        before = s3_mock.list_objects_v2(Bucket="animalopolis-examenes").get(
            "KeyCount", 0
        )
        r = _upload(
            client, token_urdesa,
            file_bytes=b"<html>not a pdf</html>",
            filename="evil.pdf",
            mime="application/pdf",
        )
        assert r.status_code == 422
        after = s3_mock.list_objects_v2(Bucket="animalopolis-examenes").get(
            "KeyCount", 0
        )
        assert before == after
