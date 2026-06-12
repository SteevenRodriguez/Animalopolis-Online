import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.alta import Alta
from app.models.usuario import Usuario
from app.services.upsert_service import (
    get_or_create_mascota,
    get_or_create_propietario,
)
from app.services.whatsapp_normalizer import normalize_whatsapp


def create_alta(
    db: Session,
    *,
    sede: str,
    nombre_mascota: str,
    nombre_propietario: str,
    whatsapp_raw: str,
    fecha_atencion: date,
    tipo_consulta: str,
    consentimiento: bool,
    created_by: Usuario | None,
) -> Alta:
    if not consentimiento:
        raise ValueError("El consentimiento es obligatorio")

    whatsapp = normalize_whatsapp(whatsapp_raw)
    prop = get_or_create_propietario(db, nombre_propietario, whatsapp)
    mascota = get_or_create_mascota(db, prop.id, nombre_mascota)

    alta = Alta(
        sede=sede,
        mascota_id=mascota.id,
        propietario_id=prop.id,
        fecha_atencion=fecha_atencion,
        tipo_consulta=tipo_consulta,
        consentimiento=True,
        estado_envio="pendiente",
        created_by_id=created_by.id if created_by else None,
    )
    db.add(alta)
    db.flush()
    return alta


def build_alta_query(
    *,
    sede: str | None,
    desde: date | None,
    hasta: date | None,
    estado_envio: str | None,
    restrict_to_sede: str | None,
) -> Select:
    stmt = select(Alta)
    if restrict_to_sede is not None:
        stmt = stmt.where(Alta.sede == restrict_to_sede)
    if sede is not None:
        stmt = stmt.where(Alta.sede == sede)
    if desde is not None:
        stmt = stmt.where(Alta.fecha_atencion >= desde)
    if hasta is not None:
        stmt = stmt.where(Alta.fecha_atencion <= hasta)
    if estado_envio is not None:
        stmt = stmt.where(Alta.estado_envio == estado_envio)
    return stmt.order_by(Alta.created_at.desc())


def get_alta_scoped(
    db: Session, alta_id: uuid.UUID, restrict_to_sede: str | None
) -> Alta | None:
    """Return alta only if visible to the caller's sede scope. Returns None to
    avoid disclosing record existence across sedes."""
    alta = db.get(Alta, alta_id)
    if alta is None:
        return None
    if restrict_to_sede is not None and alta.sede != restrict_to_sede:
        return None
    return alta


def mark_sent(db: Session, alta: Alta) -> Alta:
    alta.estado_envio = "enviado"
    alta.enviado_at = datetime.now(timezone.utc)
    db.flush()
    return alta


def update_alta(
    db: Session,
    alta: Alta,
    *,
    fecha_atencion: date | None = None,
    tipo_consulta: str | None = None,
) -> dict:
    """Apply allowed updates in place. Returns a diff describing what changed
    (used by the audit log). Returns {} when nothing actually changes."""
    diff: dict = {}
    if fecha_atencion is not None and fecha_atencion != alta.fecha_atencion:
        diff["fecha_atencion"] = {
            "from": alta.fecha_atencion.isoformat(),
            "to": fecha_atencion.isoformat(),
        }
        alta.fecha_atencion = fecha_atencion
    if tipo_consulta is not None and tipo_consulta != alta.tipo_consulta:
        diff["tipo_consulta"] = {"from": alta.tipo_consulta, "to": tipo_consulta}
        alta.tipo_consulta = tipo_consulta
    if diff:
        db.flush()
    return diff
