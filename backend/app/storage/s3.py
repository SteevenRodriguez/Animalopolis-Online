"""Stub placeholder. Full implementation lands in Parte 2 (integración S3)."""
from typing import BinaryIO

from app.storage.base import StorageBackend


class S3StorageBackend(StorageBackend):
    def upload(self, key: str, fileobj: BinaryIO, content_type: str, size: int) -> None:
        raise NotImplementedError("S3StorageBackend.upload se implementa en Parte 2")

    def presigned_url(self, key: str, expires_seconds: int) -> str:
        raise NotImplementedError("S3StorageBackend.presigned_url se implementa en Parte 2")

    def delete(self, key: str) -> None:
        raise NotImplementedError("S3StorageBackend.delete se implementa en Parte 2")

    def exists(self, key: str) -> bool:
        raise NotImplementedError("S3StorageBackend.exists se implementa en Parte 2")
