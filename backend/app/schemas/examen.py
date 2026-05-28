import uuid
from datetime import datetime

from pydantic import BaseModel


class ExamenOut(BaseModel):
    id: uuid.UUID
    sede: str
    mascota_id: uuid.UUID
    propietario_id: uuid.UUID
    tipo_examen: str
    archivo_nombre: str
    archivo_mime: str
    archivo_size_bytes: int
    consentimiento: bool
    estado_envio: str
    enviado_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PresignedUrlOut(BaseModel):
    url: str
    expires_at: datetime
