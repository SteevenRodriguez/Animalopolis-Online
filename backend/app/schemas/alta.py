import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

from app.models.enums import Sede, TipoConsulta


class AltaCreate(BaseModel):
    sede: Sede
    nombre_mascota: str = Field(min_length=1, max_length=255)
    nombre_propietario: str = Field(min_length=1, max_length=255)
    whatsapp: str = Field(min_length=4, max_length=32)
    fecha_atencion: date
    tipo_consulta: TipoConsulta
    consentimiento: bool

    @field_validator("consentimiento")
    @classmethod
    def must_consent(cls, v: bool) -> bool:
        if v is not True:
            raise ValueError("El consentimiento es obligatorio")
        return v


class AltaUpdate(BaseModel):
    """Editable fields of an alta. sede, consentimiento and mascota_id are
    intentionally immutable (sede by rule, consentimiento as legal evidence,
    mascota_id because re-linking would orphan history)."""
    fecha_atencion: date | None = None
    tipo_consulta: TipoConsulta | None = None


class AltaOut(BaseModel):
    id: uuid.UUID
    sede: str
    mascota_id: uuid.UUID
    propietario_id: uuid.UUID
    fecha_atencion: date
    tipo_consulta: str
    consentimiento: bool
    estado_envio: str
    enviado_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
