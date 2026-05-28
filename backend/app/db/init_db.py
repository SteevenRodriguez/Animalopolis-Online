import logging

from sqlalchemy import select

from app.config import get_settings
from app.db.session import SessionLocal
from app.models.enums import Rol
from app.models.usuario import Usuario
from app.services.auth_service import create_user

logger = logging.getLogger("animalopolis")


def bootstrap_admin() -> None:
    """
    Create an initial admin user if no users exist and bootstrap env vars are set.
    Safe to run on every startup.
    """
    settings = get_settings()
    if not settings.BOOTSTRAP_ADMIN_EMAIL or not settings.BOOTSTRAP_ADMIN_PASSWORD:
        return
    db = SessionLocal()
    try:
        existing = db.execute(select(Usuario).limit(1)).scalar_one_or_none()
        if existing is not None:
            return
        create_user(
            db,
            email=settings.BOOTSTRAP_ADMIN_EMAIL,
            password=settings.BOOTSTRAP_ADMIN_PASSWORD,
            nombre=settings.BOOTSTRAP_ADMIN_NOMBRE,
            rol=Rol.admin.value,
            sede=None,
        )
        db.commit()
        logger.info("Bootstrap admin creado: %s", settings.BOOTSTRAP_ADMIN_EMAIL)
    except Exception as e:
        db.rollback()
        logger.warning("No se pudo crear bootstrap admin: %s", e)
    finally:
        db.close()
