import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class PropietarioOut(BaseModel):
    id: uuid.UUID
    nombre: str
    whatsapp_e164: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PropietarioUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=255)
    whatsapp: str | None = Field(default=None, min_length=4, max_length=32)
