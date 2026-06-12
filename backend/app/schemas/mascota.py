import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class MascotaOut(BaseModel):
    id: uuid.UUID
    nombre: str
    propietario_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MascotaUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=255)
