from abc import ABC, abstractmethod
from typing import BinaryIO


class StorageBackend(ABC):
    """
    Abstract object-storage interface. S3 and Cloudflare R2 share the same API,
    so a single S3-compatible implementation works for both — only the endpoint,
    region and credentials change. A local backend exists for dev/tests only.
    """

    @abstractmethod
    def upload(
        self, key: str, fileobj: BinaryIO, content_type: str, size: int
    ) -> None: ...

    @abstractmethod
    def presigned_url(self, key: str, expires_seconds: int) -> str: ...

    @abstractmethod
    def delete(self, key: str) -> None: ...

    @abstractmethod
    def exists(self, key: str) -> bool: ...
