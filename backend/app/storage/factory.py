from app.config import get_settings
from app.storage.base import StorageBackend


def get_storage() -> StorageBackend:
    """
    Returns a singleton-ish storage backend based on settings.
    Implemented in Parte 2 (S3 integration).
    """
    settings = get_settings()
    if settings.STORAGE_BACKEND == "s3":
        from app.storage.s3 import S3StorageBackend

        return S3StorageBackend()
    raise NotImplementedError(f"Storage backend {settings.STORAGE_BACKEND} no soportado todavía")
