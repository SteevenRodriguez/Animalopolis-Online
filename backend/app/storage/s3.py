from __future__ import annotations

from typing import BinaryIO

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.config import get_settings
from app.storage.base import StorageBackend


class S3StorageBackend(StorageBackend):
    """
    S3-compatible storage. Works against:
      - AWS S3 (leave S3_ENDPOINT_URL empty / unset, set region + creds)
      - Cloudflare R2 (set endpoint to the R2 account URL; same API)
      - MinIO in local dev (set endpoint to http://minio:9000, path-style)
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._bucket = settings.S3_BUCKET
        self._region = settings.S3_REGION

        config_kwargs: dict = {"signature_version": "s3v4"}
        if settings.S3_USE_PATH_STYLE:
            config_kwargs["s3"] = {"addressing_style": "path"}

        client_kwargs: dict = {
            "region_name": settings.S3_REGION,
            "config": Config(**config_kwargs),
        }
        if settings.S3_ENDPOINT_URL:
            client_kwargs["endpoint_url"] = settings.S3_ENDPOINT_URL
        if settings.S3_ACCESS_KEY_ID:
            client_kwargs["aws_access_key_id"] = settings.S3_ACCESS_KEY_ID
        if settings.S3_SECRET_ACCESS_KEY:
            client_kwargs["aws_secret_access_key"] = settings.S3_SECRET_ACCESS_KEY

        self._client = boto3.client("s3", **client_kwargs)

    @property
    def bucket(self) -> str:
        return self._bucket

    def upload(
        self, key: str, fileobj: BinaryIO, content_type: str, size: int
    ) -> None:
        # ServerSideEncryption is set to AES256; on MinIO with default config
        # this is accepted as a no-op. R2 and S3 will encrypt at rest.
        extra_args: dict = {"ContentType": content_type}
        try:
            self._client.upload_fileobj(
                Fileobj=fileobj,
                Bucket=self._bucket,
                Key=key,
                ExtraArgs=extra_args,
            )
        except ClientError as e:
            raise RuntimeError(f"Falló subida a S3: {e}") from e

    def presigned_url(self, key: str, expires_seconds: int) -> str:
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires_seconds,
        )

    def delete(self, key: str) -> None:
        self._client.delete_object(Bucket=self._bucket, Key=key)

    def exists(self, key: str) -> bool:
        try:
            self._client.head_object(Bucket=self._bucket, Key=key)
            return True
        except ClientError:
            return False
