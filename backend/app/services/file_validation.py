"""File upload validation. Verifies size, declared MIME against allowlist,
AND magic bytes — so a malicious caller cannot bypass the MIME check by
labeling an executable as image/png."""
from __future__ import annotations


class FileValidationError(ValueError):
    pass


_MAGIC_PREFIXES: dict[str, list[bytes]] = {
    "application/pdf": [b"%PDF-"],
    "image/jpeg": [b"\xff\xd8\xff"],
    "image/png": [b"\x89PNG\r\n\x1a\n"],
    # RIFF container — the "WEBP" inside is validated separately below.
    "image/webp": [b"RIFF"],
}


def normalize_mime(value: str | None) -> str:
    return (value or "").lower().split(";")[0].strip()


def validate_file(
    *,
    data: bytes,
    declared_mime: str | None,
    allowed_mimes: list[str],
    max_size: int,
) -> str:
    """Validates a file payload. Returns the normalized MIME on success.
    Raises FileValidationError on any rejection."""
    if not data:
        raise FileValidationError("Archivo vacío")
    if len(data) > max_size:
        raise FileValidationError(
            f"Archivo excede el tamaño máximo permitido ({max_size} bytes)"
        )

    mime = normalize_mime(declared_mime)
    if mime not in (m.lower() for m in allowed_mimes):
        raise FileValidationError(f"Tipo de archivo no permitido: {declared_mime!r}")

    prefixes = _MAGIC_PREFIXES.get(mime, [])
    if prefixes and not any(data.startswith(p) for p in prefixes):
        raise FileValidationError(
            "El contenido del archivo no coincide con el tipo declarado"
        )

    if mime == "image/webp":
        if len(data) < 12 or data[8:12] != b"WEBP":
            raise FileValidationError("Archivo WEBP inválido")

    return mime
