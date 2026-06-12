import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.propietario import Propietario
from app.services.whatsapp_normalizer import normalize_whatsapp


class WhatsAppAlreadyInUse(ValueError):
    pass


def get_propietario(db: Session, prop_id: uuid.UUID) -> Propietario | None:
    return db.get(Propietario, prop_id)


def update_propietario(
    db: Session,
    propietario: Propietario,
    *,
    nombre: str | None = None,
    whatsapp_raw: str | None = None,
) -> dict:
    diff: dict = {}
    if nombre is not None and nombre != propietario.nombre:
        diff["nombre"] = {"from": propietario.nombre, "to": nombre}
        propietario.nombre = nombre
    if whatsapp_raw is not None:
        new_e164 = normalize_whatsapp(whatsapp_raw)
        if new_e164 != propietario.whatsapp_e164:
            existing = db.execute(
                select(Propietario).where(Propietario.whatsapp_e164 == new_e164)
            ).scalar_one_or_none()
            if existing is not None and existing.id != propietario.id:
                raise WhatsAppAlreadyInUse(
                    "Ese número de WhatsApp ya está asignado a otro propietario"
                )
            diff["whatsapp_e164"] = {
                "from": propietario.whatsapp_e164,
                "to": new_e164,
            }
            propietario.whatsapp_e164 = new_e164
    if diff:
        db.flush()
    return diff
