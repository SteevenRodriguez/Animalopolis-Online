import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class AuditAction(str, Enum):
    LOGIN = "login"
    LOGIN_FAILED = "login_failed"

    CREATE_ALTA = "create_alta"
    UPDATE_ALTA = "update_alta"
    MARK_SENT_ALTA = "mark_sent_alta"

    CREATE_EXAMEN = "create_examen"
    UPDATE_EXAMEN = "update_examen"
    DOWNLOAD_EXAMEN = "download_examen"
    MARK_SENT_EXAMEN = "mark_sent_examen"

    UPDATE_PROPIETARIO = "update_propietario"
    UPDATE_MASCOTA = "update_mascota"

    CREATE_USER = "create_user"
    UPDATE_USER = "update_user"
    DEACTIVATE_USER = "deactivate_user"


class AuditLogOut(BaseModel):
    id: uuid.UUID
    timestamp: datetime
    user_id: uuid.UUID | None
    user_email: str | None
    user_rol: str | None
    user_sede: str | None
    action: str
    resource_type: str | None
    resource_id: uuid.UUID | None
    success: bool
    ip: str | None
    user_agent: str | None
    details: dict | None

    model_config = {"from_attributes": True}
