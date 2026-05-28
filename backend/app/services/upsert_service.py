from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.mascota import Mascota
from app.models.propietario import Propietario


def get_or_create_propietario(db: Session, nombre: str, whatsapp_e164: str) -> Propietario:
    stmt = select(Propietario).where(Propietario.whatsapp_e164 == whatsapp_e164)
    prop = db.execute(stmt).scalar_one_or_none()
    if prop is None:
        prop = Propietario(nombre=nombre, whatsapp_e164=whatsapp_e164)
        db.add(prop)
        db.flush()
    elif prop.nombre != nombre:
        # Keep the most recent name supplied.
        prop.nombre = nombre
        db.flush()
    return prop


def get_or_create_mascota(db: Session, propietario_id, nombre: str) -> Mascota:
    stmt = select(Mascota).where(
        Mascota.propietario_id == propietario_id, Mascota.nombre == nombre
    )
    mascota = db.execute(stmt).scalar_one_or_none()
    if mascota is None:
        mascota = Mascota(nombre=nombre, propietario_id=propietario_id)
        db.add(mascota)
        db.flush()
    return mascota
