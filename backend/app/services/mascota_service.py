import uuid

from sqlalchemy.orm import Session

from app.models.mascota import Mascota


def get_mascota(db: Session, mascota_id: uuid.UUID) -> Mascota | None:
    return db.get(Mascota, mascota_id)


def update_mascota(
    db: Session, mascota: Mascota, *, nombre: str | None = None
) -> dict:
    diff: dict = {}
    if nombre is not None and nombre != mascota.nombre:
        diff["nombre"] = {"from": mascota.nombre, "to": nombre}
        mascota.nombre = nombre
    if diff:
        db.flush()
    return diff
