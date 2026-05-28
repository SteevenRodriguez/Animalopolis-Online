from io import BytesIO


class TestS3StorageBackend:
    def test_upload_and_exists(self, s3_mock):
        from app.storage.s3 import S3StorageBackend

        backend = S3StorageBackend()
        data = b"%PDF-1.4\nhello"
        backend.upload("test/file.pdf", BytesIO(data), "application/pdf", len(data))

        assert backend.exists("test/file.pdf") is True
        assert backend.exists("test/missing.pdf") is False

    def test_delete(self, s3_mock):
        from app.storage.s3 import S3StorageBackend

        backend = S3StorageBackend()
        backend.upload("delete-me.pdf", BytesIO(b"%PDF-1.4\n"), "application/pdf", 9)
        assert backend.exists("delete-me.pdf")
        backend.delete("delete-me.pdf")
        assert not backend.exists("delete-me.pdf")

    def test_presigned_url_has_expiration(self, s3_mock):
        from app.storage.s3 import S3StorageBackend

        backend = S3StorageBackend()
        backend.upload("foo.pdf", BytesIO(b"%PDF-1.4\n"), "application/pdf", 9)

        url = backend.presigned_url("foo.pdf", expires_seconds=120)
        assert "animalopolis-examenes" in url
        assert "X-Amz-Expires=120" in url or "Expires=" in url
        assert "X-Amz-Signature" in url

    def test_bucket_is_not_public(self, s3_mock):
        # moto starts buckets as private by default — confirm there's no public ACL.
        acl = s3_mock.get_bucket_acl(Bucket="animalopolis-examenes")
        grantees = [g.get("Grantee", {}) for g in acl.get("Grants", [])]
        for g in grantees:
            uri = g.get("URI", "") or ""
            assert "AllUsers" not in uri and "AuthenticatedUsers" not in uri
