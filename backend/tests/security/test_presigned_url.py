"""Presigned URL properties: contains expiration, scoped to one key,
and the bucket itself remains private."""
from io import BytesIO
from urllib.parse import parse_qs, urlparse

from tests.conftest import auth


FORM = {
    "sede": "urdesa",
    "nombre_mascota": "Fido",
    "nombre_propietario": "Juan",
    "whatsapp": "+593991234567",
    "tipo_examen": "sangre",
    "consentimiento": "true",
}


def _upload(client, token):
    files = {"file": ("ok.pdf", BytesIO(b"%PDF-1.4\nhello"), "application/pdf")}
    return client.post("/api/v1/examenes", headers=auth(token), data=FORM, files=files)


class TestPresignedUrl:
    def test_url_contains_signature_and_expiry(self, client, token_urdesa, s3_mock):
        r_create = _upload(client, token_urdesa)
        examen_id = r_create.json()["id"]
        r = client.get(
            f"/api/v1/examenes/{examen_id}/file-url",
            headers=auth(token_urdesa),
        )
        assert r.status_code == 200
        url = r.json()["url"]
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        # SigV4 markers.
        assert "X-Amz-Signature" in qs
        assert "X-Amz-Expires" in qs
        # Must NOT be a publicly addressable URL — must require the signature.
        assert qs.get("X-Amz-Expires", ["0"])[0] not in ("0", "")
        # The bucket name appears in the path or host.
        assert "animalopolis-examenes" in url

    def test_url_is_scoped_to_one_object(self, client, token_admin, token_urdesa, s3_mock):
        # Upload two; verify each presigned URL points to a distinct key.
        a = _upload(client, token_urdesa).json()
        b = _upload(client, token_urdesa).json()
        url_a = client.get(
            f"/api/v1/examenes/{a['id']}/file-url", headers=auth(token_urdesa)
        ).json()["url"]
        url_b = client.get(
            f"/api/v1/examenes/{b['id']}/file-url", headers=auth(token_urdesa)
        ).json()["url"]
        assert url_a != url_b

    def test_short_expiry_is_in_seconds(self, client, token_urdesa, s3_mock):
        r_create = _upload(client, token_urdesa)
        examen_id = r_create.json()["id"]
        r = client.get(
            f"/api/v1/examenes/{examen_id}/file-url",
            headers=auth(token_urdesa),
        )
        url = r.json()["url"]
        qs = parse_qs(urlparse(url).query)
        # Default in tests/.env.example is 300s; must be a small number.
        exp = int(qs["X-Amz-Expires"][0])
        assert 1 <= exp <= 3600

    def test_bucket_has_no_public_acl(self, s3_mock):
        # Direct sanity check on the bucket itself.
        acl = s3_mock.get_bucket_acl(Bucket="animalopolis-examenes")
        for grant in acl.get("Grants", []):
            uri = grant.get("Grantee", {}).get("URI") or ""
            assert "AllUsers" not in uri
            assert "AuthenticatedUsers" not in uri

    def test_object_not_readable_without_signature(self, s3_mock):
        # An anonymous boto3 client (no creds) must NOT be able to read.
        import boto3
        from botocore import UNSIGNED
        from botocore.client import Config
        from botocore.exceptions import ClientError

        # First ensure an object exists.
        s3_mock.put_object(
            Bucket="animalopolis-examenes", Key="probe.pdf", Body=b"%PDF-1.4\n"
        )

        anon = boto3.client(
            "s3",
            region_name="us-east-1",
            config=Config(signature_version=UNSIGNED),
        )
        try:
            anon.get_object(Bucket="animalopolis-examenes", Key="probe.pdf")
            denied = False
        except ClientError as e:
            denied = e.response["Error"]["Code"] in (
                "AccessDenied",
                "403",
                "AllAccessDisabled",
            )
        assert denied, "El bucket es legible sin firma — debe ser privado"
