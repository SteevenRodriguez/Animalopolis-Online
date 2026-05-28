from __future__ import annotations

import uuid
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.examen import Examen
from app.models.usuario import Usuario
from app.services.upsert_service import (
    get_or_create_mascota,
    get_or_create_propietario,
)
from app.services.whatsapp_normalizer import normalize_whatsapp
from app.storage.base import StorageBackend

_ALLOWED_EXTS = {".pdf", ".jpg", ".jpeg", ".png", ".webp"}


def build_storage_key(sede: str, original_filename: str) -> str:
    """examenes/{sede}/{yyyy}/{mm}/{uuid}.{ext}"""
    now = datetime.now(timezone.utc)
    ext = Path(original_filename).suffix.lower()
    if ext not in _ALLOWED_EXTS:
        ext = ".bin"
    return f"examenes/{sede}/{now.year:04d}/{now.month:02d}/{uuid.uuid4()}{ext}"


def sanitize_filename(name: str) -> str:
    # Strip any path components and clamp length.
    base = Path(name).name or "archivo"
    return base[:255]


def create_examen(
    db: Session,
    *,
    sede: str,
    nombre_mascota: str,
    nombre_propietario: str,
    whatsapp_raw: str,
    tipo_examen: str,
    file_bytes: bytes,
    file_name: str,
    file_mime: str,
    created_by: Usuario | None,
    storage: StorageBackend,
) -> Examen:
    whatsapp = normalize_whatsapp(whatsapp_raw)
    prop = get_or_create_propietario(db, nombre_propietario, whatsapp)
    mascota = get_or_create_mascota(db, prop.id, nombre_mascota)

    key = build_storage_key(sede, file_name)
    storage.upload(key, BytesIO(file_bytes), file_mime, len(file_bytes))

    examen = Examen(
        sede=sede,
        mascota_id=mascota.id,
        propietario_id=prop.id,
        tipo_examen=tipo_examen,
        storage_key=key,
        archivo_nombre=sanitize_filename(file_name),
        archivo_mime=file_mime,
        archivo_size_bytes=len(file_bytes),
        consentimiento=True,
        estado_envio="pendiente",
        created_by_id=created_by.id if created_by else None,
    )
    db.add(examen)
    db.flush()
    return examen


def build_examen_query(
    *,
    sede: str | None,
    desde: datetime | None,
    hasta: datetime | None,
    estado_envio: str | None,
    restrict_to_sede: str | None,
) -> Select:
    stmt = select(Examen)
    if restrict_to_sede is not None:
        stmt = stmt.where(Examen.sede == restrict_to_sede)
    if sede is not None:
        stmt = stmt.where(Examen.sede == sede)
    if desde is not None:
        stmt = stmt.where(Examen.created_at >= desde)
    if hasta is not None:
        stmt = stmt.where(Examen.created_at <= hasta)
    if estado_envio is not None:
        stmt = stmt.where(Examen.estado_envio == estado_envio)
    return stmt.order_by(Examen.created_at.desc())


def get_examen_scoped(
    db: Session, examen_id: uuid.UUID, restrict_to_sede: str | None
) -> Examen | None:
    examen = db.get(Examen, examen_id)
    if examen is None:
        return None
    if restrict_to_sede is not None and examen.sede != restrict_to_sede:
        return None
    return examen


def mark_sent_examen(db: Session, examen: Examen) -> Examen:
    examen.estado_envio = "enviado"
    examen.enviado_at = datetime.now(timezone.utc)
    db.flush()
    return examen
